"""
Main ARIA application — v4 patched.

Key fixes vs original:
- Logging goes to ~/.aria/aria.log only (no terminal pollution)
- /fix reads ~/.aria/last_fail.json from shell hook automatically
- max_tokens raised to 8192 (was 2048 → caused truncation)
- /watch properly polls hook file
- Bare input treated as /ask
"""

import logging
import sys
import json
from typing import Optional
from pathlib import Path

from .api_client import APIClient, APIConfig
from .config import ConfigManager
from .command_system import CommandSystem
from .knowledge_base import KnowledgeBase
from .guardian import Guardian
from .watch_mode import WatchMode
from .ui import UIManager

# ── FILE-ONLY logging — zero terminal pollution ───────────────────
_log_dir = Path.home() / ".aria"
_log_dir.mkdir(parents=True, exist_ok=True)

_file_handler = logging.FileHandler(_log_dir / "aria.log")
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s: %(message)s"
))
logging.root.handlers = []          # clear any handlers set elsewhere
logging.root.addHandler(_file_handler)
logging.root.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

_HOOK_FILE = Path.home() / ".aria" / "last_fail.json"


class ARIA:
    """Main ARIA application class."""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.command_system = CommandSystem()
        self.knowledge_base = KnowledgeBase()
        self.guardian = Guardian()
        self.watch_mode = WatchMode(self.knowledge_base)
        self.api_client: Optional[APIClient] = None
        self.running = False
        logger.info("ARIA initialized")

    # ── Setup ─────────────────────────────────────────────────────

    def setup(self) -> bool:
        config = self.config_manager.load()

        if not config.get("api_key"):
            logger.warning("No API key — launching wizard")
            self.run_config_wizard()
            config = self.config_manager.load()

        try:
            api_config = APIConfig(
                api_key=config.get("api_key", ""),
                model=config.get("model", "gemma-4-26b-a4b-it"),
                temperature=config.get("temperature", 0.7),
                # Raised from 2048 → prevents mid-sentence truncation
                max_tokens=config.get("max_tokens", 8192),
            )
            self.api_client = APIClient(api_config)
            logger.info("API client ready")
        except Exception as e:
            logger.error(f"API init failed: {e}")
            UIManager.display_error(f"API init failed: {e}")
            return False

        self._register_commands()

        if config.get("guardian_mode", True):
            self.guardian.enable()

        logger.info("Setup complete")
        return True

    def _register_commands(self):
        reg = self.command_system.register
        reg("ask",     self.cmd_ask,     "Ask the AI a question",                 requires_args=True)
        reg("fix",     self.cmd_fix,     "Diagnose last failure (or describe one)")
        reg("watch",   self.cmd_watch,   "Toggle watch mode")
        reg("models",  self.cmd_models,  "List available models")
        reg("config",  self.cmd_config,  "Run configuration wizard")
        reg("kb",      self.cmd_kb,      "Search knowledge base",                 requires_args=True)
        reg("history", self.cmd_history, "Show command history")
        reg("status",  self.cmd_status,  "Show ARIA system status")
        reg("help",    self.cmd_help,    "Show help menu")
        logger.info("Commands registered")

    # ── Commands ──────────────────────────────────────────────────

    def cmd_ask(self, query: str) -> str:
        if not self.api_client:
            return "❌ No API client. Run /config."

        response = self.api_client.generate_content(
            prompt=query,
            system_instruction=(
                "You are ARIA, a terminal AI for Termux on Android. "
                "Give concise, practical answers. "
                "Put ALL commands in ```bash code blocks. "
                "Lead with the command, then a 1-line explanation. "
                "Never apologize. Never show reasoning steps."
            ),
        )
        return response

    def cmd_fix(self, error: str = "") -> str:
        """
        Diagnose the most recent shell failure.

        Reads ~/.aria/last_fail.json written by the PROMPT_COMMAND hook.
        If no hook data exists, uses the optional `error` argument.
        """
        if not self.api_client:
            return "❌ No API client. Run /config."

        hook: dict = {}
        if _HOOK_FILE.exists():
            try:
                hook = json.loads(_HOOK_FILE.read_text())
                _HOOK_FILE.write_text("{}")   # clear after reading
            except Exception:
                hook = {}

        parts = []
        if hook.get("cmd"):
            parts.append(f"Failed command: $ {hook['cmd']}")
            parts.append(f"Exit code: {hook.get('code', '?')}")
            parts.append(f"CWD: {hook.get('cwd', '?')}")
            if hook.get("stderr"):
                parts.append(f"stderr:\n{hook['stderr'][:800]}")

        if error:
            parts.append(f"User note: {error}")

        if not parts:
            # Try bash history as last resort
            import subprocess
            try:
                hist = subprocess.check_output(
                    ["bash", "-c", "tail -8 ~/.bash_history"],
                    text=True, stderr=subprocess.DEVNULL, timeout=3
                ).strip()
                parts.append(f"Recent history (no hook data):\n{hist}")
            except Exception:
                pass

        if not parts:
            return (
                "ℹ️  No failure context found.\n\n"
                "The shell hook captures failures automatically.\n"
                "Run `bash install.sh` to install it, then retry any failing command,\n"
                "then come back and type /fix."
            )

        context = "\n".join(parts)
        prompt = (
            f"Termux command failed. Full context:\n\n{context}\n\n"
            "Provide:\n"
            "1. What failed and why (1–2 lines)\n"
            "2. Exact fix in ```bash blocks\n"
            "3. How to prevent recurrence (1 line)"
        )

        return self.api_client.generate_content(
            prompt=prompt,
            system_instruction=(
                "You are ARIA, a Termux repair specialist. "
                "Commands first in ```bash blocks. "
                "Be concise. Never apologize. Never show reasoning."
            ),
        )

    def cmd_watch(self, args: str = "") -> str:
        if self.watch_mode.enabled:
            self.watch_mode.disable()
            return "👁  Watch mode disabled."

        self.watch_mode.enable(self.api_client, self.knowledge_base)
        return (
            "👁  Watch mode active.\n\n"
            "Every time a command fails in your shell, the hook writes the details to\n"
            "~/.aria/last_fail.json.\n\n"
            "Come back to ARIA and type  /fix  — no arguments needed.\n"
            "ARIA will pick up the exact command, exit code, and error automatically.\n\n"
            "Tip: You can also describe the error: /fix 'pip install failing with Rust error'"
        )

    def cmd_models(self, args: str = "") -> str:
        if not self.api_client:
            return "❌ No API client."

        models = self.api_client.fetch_available_models()
        current = self.config_manager.get("model", "unknown")
        lines = ["📊 Available Gemma Models:\n"]
        for m in models:
            tick = "✓" if m == current else " "
            lines.append(f"  [{tick}] {m}")
        lines.append(f"\nActive: {current}")
        lines.append("Switch: /config → enter model name")
        return "\n".join(lines)

    def cmd_config(self, args: str = "") -> str:
        self.run_config_wizard()
        return "✅ Configuration updated."

    def cmd_kb(self, query: str) -> str:
        results = self.knowledge_base.search(query)
        if not results:
            return f"❌ No KB results for: {query}"
        lines = [f"📚 Knowledge Base ({len(results)} found):\n"]
        for i, r in enumerate(results[:5], 1):
            lines.append(f"{i}. {r.pattern.upper()}")
            lines.append(f"   {r.solution}")
            if r.auto_fixable:
                lines.append(f"   🔧 {r.fix_command}")
            lines.append("")
        return "\n".join(lines)

    def cmd_history(self, args: str = "") -> str:
        history = self.command_system.get_history(limit=10)
        if not history:
            return "No history."
        lines = ["📜 Recent Commands:\n"]
        for i, cmd in enumerate(history, 1):
            lines.append(f"  {i}. {cmd}")
        return "\n".join(lines)

    def cmd_status(self, args: str = "") -> str:
        cfg = self.config_manager.config
        lines = ["⚙️  ARIA Status\n"]
        lines.append(f"  Model:      {cfg.get('model', '?')}")
        lines.append(f"  API key:    {'set ✓' if cfg.get('api_key') else 'NOT SET ✗'}")
        lines.append(f"  Max tokens: {cfg.get('max_tokens', 8192)}")
        lines.append(f"  Guardian:   {'enabled' if self.guardian.enabled else 'disabled'}")
        lines.append(f"  Watch:      {'active ✓' if self.watch_mode.enabled else 'off'}")

        if _HOOK_FILE.exists():
            try:
                data = json.loads(_HOOK_FILE.read_text())
                if data.get("cmd"):
                    lines.append(f"\n  Pending failure: $ {data['cmd']} (exit {data.get('code','?')})")
                    lines.append("  → Run /fix to diagnose")
            except Exception:
                pass

        return "\n".join(lines)

    def cmd_help(self, args: str = "") -> str:
        return self.command_system.get_help()

    def run_config_wizard(self):
        from rich.console import Console
        from rich.panel import Panel
        Console().print(Panel(
            "[bold]ARIA Configuration Wizard[/bold]\n\n"
            "Free key (no card): [cyan]https://aistudio.google.com/app/apikey[/cyan]",
            border_style="cyan"
        ))

        cur_key   = self.config_manager.get("api_key", "")
        cur_model = self.config_manager.get("model", "gemma-4-26b-a4b-it")

        api_key = UIManager.prompt("API key (Enter to keep current): ").strip() or cur_key
        model   = UIManager.prompt(f"Model [{cur_model}]: ").strip() or cur_model
        guardian = UIManager.confirm("Enable Guardian safety mode?")

        self.config_manager.set("api_key", api_key)
        self.config_manager.set("model", model)
        self.config_manager.set("guardian_mode", guardian)
        self.config_manager.set("max_tokens", 8192)
        self.config_manager.save()
        UIManager.display_success("Configuration saved!")

    # ── Main loop ─────────────────────────────────────────────────

    def run(self):
        self.running = True
        UIManager.boot_sequence()

        if not self.setup():
            UIManager.display_error("Setup failed. See ~/.aria/aria.log")
            return

        try:
            while self.running:
                # Non-blocking watch check before each prompt
                if self.watch_mode.enabled:
                    self.watch_mode.check_and_notify()

                user_input = UIManager.prompt()

                if not user_input.strip():
                    continue

                if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
                    UIManager.display_success("Goodbye! 👋")
                    self.running = False
                    break

                parsed = self.command_system.parse_command(user_input)

                if parsed:
                    result = self.command_system.execute(parsed)
                    UIManager.display_response(result)
                else:
                    # Bare text → treat as /ask
                    result = self.cmd_ask(user_input)
                    UIManager.display_response(result)

        except KeyboardInterrupt:
            UIManager.display_info("\nGoodbye! 👋")
            self.running = False
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            UIManager.display_error(f"Error: {e}\nSee ~/.aria/aria.log")


def main():
    try:
        aria = ARIA()
        aria.run()
    except Exception as e:
        logger.error(f"Fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

