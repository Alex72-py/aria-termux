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
import time
from typing import Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

from .api_client import APIClient, APIConfig
from .config import ConfigManager
from .command_system import CommandSystem
from .knowledge_base import KnowledgeBase
from .guardian import Guardian
from .watch_mode import WatchMode
from .ui import UIManager
from .repair_agent import RepairAgent

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
        self.repair_agent = RepairAgent(self.guardian, self.knowledge_base)
        self.api_client: Optional[APIClient] = None
        self.running = False
        logger.info("ARIA initialized")

    # ── Setup ─────────────────────────────────────────────────────

    def setup(self) -> bool:
        config = self.config_manager.load()

        provider = (config.get("provider") or "").strip().lower()
        api_keys = config.get("api_keys", {})
        selected_key = api_keys.get(provider) or config.get("api_key", "")
        if selected_key:
            self.config_manager.set("api_key", selected_key)
            config["api_key"] = selected_key

        if not provider or not config.get("model") or not config.get("api_key"):
            logger.warning("Incomplete configuration; launching wizard")
            self.run_config_wizard()
            config = self.config_manager.load()
            provider = (config.get("provider") or "").strip().lower()

        if not provider or not config.get("model") or not config.get("api_key"):
            UIManager.display_error("Setup is incomplete. Run /config and finish all required fields.")
            return False

        try:
            api_config = APIConfig(
                api_key=config.get("api_key", ""),
                model=config.get("model", ""),
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 8192),
                provider=provider,
                stream=config.get("stream", False),
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
        if config.get("watch_mode", False):
            self.watch_mode.enable(self.api_client, self.knowledge_base)

        logger.info("Setup complete")
        return True

    def _register_commands(self):
        reg = self.command_system.register
        reg("ask",     self.cmd_ask,     "Ask the AI a question",                 requires_args=True)
        reg("fix",     self.cmd_fix,     "Diagnose the latest failure and auto-repair safe Termux issues")
        reg("install", self.cmd_install, "Install complex Termux packages (rust, torch, etc.)", requires_args=True)
        reg("watch",   self.cmd_watch,   "Toggle watch mode")
        reg("provider", self.cmd_provider, "Manage model provider (list/set/status/cycle)")
        reg("model",   self.cmd_model,   "Manage model (list/set/status)")
        reg("models",  self.cmd_models,  "List available models")
        reg("config",  self.cmd_config,  "Run configuration wizard")
        reg("kb",      self.cmd_kb,      "Search knowledge base",                 requires_args=True)
        reg("history", self.cmd_history, "Show command history")
        reg("status",  self.cmd_status,  "Show ARIA system status")
        reg("help",    self.cmd_help,    "Show help menu")
        logger.info("Commands registered")

    def _startup_commands(self):
        return [
            {"command": "/ask <question>", "description": "chat with the active model"},
            {"command": "/fix", "description": "diagnose the latest shell or log failure"},
            {"command": "/install <pkg>", "description": "install complex Termux dependencies"},
            {"command": "/provider list", "description": "view providers and key availability"},
            {"command": "/provider openrouter", "description": "switch providers directly"},
            {"command": "/provider cycle", "description": "rotate to the next saved provider"},
            {"command": "/model list", "description": "browse models for the current provider"},
            {"command": "/watch", "description": "toggle background failure monitoring"},
            {"command": "/status", "description": "show active provider, model, and safety state"},
        ]

    # ── Commands ──────────────────────────────────────────────────

    def cmd_ask(self, query: str, status_handler=None) -> str:
        if not self.api_client:
            return "Error: No API client. Run /config."

        response = self.api_client.generate_content(
            prompt=query,
            system_instruction=(
                "You are ARIA, a terminal AI for Termux on Android. "
                "Provide concise, practical answers. "
                "Put ALL commands in ```bash code blocks. "
                "Lead with the command, then a 1-line explanation. "
                "If you need to think through a complex problem, wrap your internal steps in <thought>...</thought> tags. "
                "NEVER repeat the user's question or state what the user is asking. "
                "NEVER apologize. ONLY show the final result and essential commands."
            ),
        )
        clean_response = self._process_ai_response(response, status_handler)
        
        # Check for executable plan
        plan = self.repair_agent.plan_from_ai_text(clean_response)
        if plan.steps:
            UIManager.display_response(clean_response, is_markdown=True)
            auto_apply = self.config_manager.get("auto_apply", False)
            if auto_apply:
                UIManager.display_info("Auto-applying suggested plan...")
                outcome = self.repair_agent.execute_plan(plan)
                return outcome.render()
            
            if UIManager.confirm("Would you like to execute this suggested plan?"):
                with UIManager.status("Executing plan..."):
                    outcome = self.repair_agent.execute_plan(plan)
                return outcome.render()
            return "Plan displayed but not executed."

        return clean_response

    def cmd_fix(self, error: str = "", status_handler=None) -> str:
        """
        Diagnose the most recent shell failure or log error.
        """
        if not self.api_client:
            return "Error: No API client. Run /config."

        hook: dict = {}
        # 1. Try shell hook first
        if _HOOK_FILE.exists():
            try:
                hook = json.loads(_HOOK_FILE.read_text())
                if hook:
                    _HOOK_FILE.write_text("{}")   # clear after reading
            except Exception:
                hook = {}

        # 2. Try watch log if hook is empty
        log_error = ""
        watch_log = Path.home() / ".aria" / "watch.log"
        if not hook.get("cmd") and watch_log.exists():
            try:
                # Read last 20 lines of watch.log
                with open(watch_log, "r") as f:
                    lines = f.readlines()
                    if lines:
                        log_error = "".join(lines[-20:])
            except Exception:
                pass

        parts = []
        if hook.get("cmd"):
            parts.append(f"Failed command: $ {hook['cmd']}")
            parts.append(f"Exit code: {hook.get('code', '?')}")
            parts.append(f"CWD: {hook.get('cwd', '?')}")
            if hook.get("stderr"):
                parts.append(f"stderr:\n{hook['stderr'][:800]}")
        elif log_error:
            parts.append(f"Detected log error/output:\n{log_error[:1000]}")

        if error:
            parts.append(f"User note: {error}")

        hist = ""
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

        # ── Step 1: Attempt local auto-repair ─────────────────────
        auto_apply = self.config_manager.get("auto_apply", False)
        outcome = self.repair_agent.attempt_auto_repair(
            hook=hook,
            log_error=log_error or hist,
            user_note=error,
            auto_apply=auto_apply
        )

        if outcome.matched:
            if outcome.applied:
                return outcome.render()
            
            # Not applied yet (either auto_apply=False or blocked by safety)
            UIManager.display_info(outcome.render(), title="Proposed Local Repair")
            if UIManager.confirm("Apply this repair plan?"):
                with UIManager.status("Applying repairs..."):
                    outcome = self.repair_agent.execute_plan(outcome)
                return outcome.render()
            else:
                return "Local repair cancelled by user."

        # ── Step 2: Fallback to AI model for complex failures ─────
        if not parts:
            return (
                "Info: No failure context found.\n\n"
                "The shell hook captures failures automatically.\n"
                "You can also pipe output to ~/.aria/watch.log to have ARIA watch it:\n"
                "```bash\n"
                "some_command 2>&1 | tee -a ~/.aria/watch.log\n"
                "```"
            )

        context = "\n".join(parts)
        prompt = (
            f"Termux failure detected. Context:\n\n{context}\n\n"
            "Provide:\n"
            "1. Wrap your diagnosis steps in <thought>...</thought>.\n"
            "2. What failed and why (1-2 lines)\n"
            "3. Exact fix in ```bash blocks\n"
            "4. How to prevent recurrence (1 line)\n\n"
            "NEVER repeat the input or start with 'The user is asking...'."
        )

        raw_response = self.api_client.generate_content(
            prompt=prompt,
            system_instruction=(
                "You are ARIA, a Termux repair agent on Android. "
                "Diagnose the failure concisely. Put ALL fix commands in ```bash blocks. "
                "NEVER repeat the user's question. NEVER apologize."
            ),
        )
        response = self._process_ai_response(raw_response, status_handler)
        
        # ── Step 3: Offer to execute AI-suggested fix ─────────────
        plan = self.repair_agent.plan_from_ai_text(response)
        if plan.steps:
            UIManager.display_response(response, is_markdown=True)
            auto_apply = self.config_manager.get("auto_apply", False)
            if auto_apply:
                UIManager.display_info("Auto-applying AI-suggested fix...")
                outcome = self.repair_agent.execute_plan(plan)
                return outcome.render()
            
            if UIManager.confirm("Would you like to execute the AI-suggested plan?"):
                with UIManager.status("Executing AI plan..."):
                    outcome = self.repair_agent.execute_plan(plan)
                return outcome.render()
            return "AI fix displayed but not executed."

        return response

    def _process_ai_response(self, response: str, status_handler=None) -> str:
        """Extract and animate <thought> steps, then return cleaned response."""
        import re
        thoughts = re.findall(r"<thought>(.*?)</thought>", response, re.DOTALL)
        
        if thoughts and status_handler:
            for thought in thoughts:
                # Split thought into lines/steps and animate them
                steps = [s.strip() for s in thought.split("\n") if s.strip()]
                for step in steps:
                    # Clean the step text (e.g., remove leading dashes)
                    clean_step = re.sub(r"^[-\d.]+\s*", "", step)
                    status_handler.update(f"Analyzing: {clean_step}")
                    time.sleep(0.4)
        
        # Remove all <thought> blocks from the final response
        clean_response = re.sub(r"<thought>.*?</thought>", "", response, flags=re.DOTALL).strip()
        return clean_response

    def cmd_install(self, package: str) -> str:
        """Install complex Termux packages with automatic dependency handling."""
        if not package:
            return "Usage: /install <package_name>"

        with UIManager.status(f"Planning installation for {package}..."):
            outcome = self.repair_agent.plan_install(package)

        if not outcome.matched or not outcome.steps:
            return f"Error: Could not plan installation for `{package}`."

        auto_apply = self.config_manager.get("auto_apply", False)
        if auto_apply:
            with UIManager.status(f"Installing {package}..."):
                outcome = self.repair_agent.execute_plan(outcome)
            return outcome.render()

        UIManager.display_info(outcome.render(), title=f"Install Plan: {package}")
        if UIManager.confirm(f"Proceed with installing `{package}` and its dependencies?"):
            with UIManager.status(f"Installing {package}..."):
                outcome = self.repair_agent.execute_plan(outcome)
            return outcome.render()
        
        return f"Installation of `{package}` cancelled by user."

    def cmd_watch(self, args: str = "") -> str:
        args = (args or "").strip()
        if args.startswith("add "):
            return self._watch_add_target(args[4:].strip())
        if args == "status":
            return self._watch_status()
        if args.startswith("remove "):
            return self._watch_remove_target(args[7:].strip())

        if self.watch_mode.enabled:
            self.watch_mode.disable()
            self._set_watch_mode_pref(False)
            return "Watch mode disabled."

        self.watch_mode.enable(self.api_client, self.knowledge_base)
        self._set_watch_mode_pref(True)
        return (
            "Watch mode active (Background Monitoring).\n\n"
            "ARIA is now monitoring:\n"
            "1. [bold]Shell failures[/bold] (via hook)\n"
            "2. [bold]~/.aria/watch.log[/bold] (for exceptions/errors)\n\n"
            "You can work in another terminal. If a command fails or an error\n"
            "appears in the log, ARIA will notify you here immediately.\n\n"
            "Tip: To watch a specific command's output, use:\n"
            "```bash\n"
            "./script.py 2>&1 | tee -a ~/.aria/watch.log\n"
            "```"
        )

    def _watch_targets_file(self) -> Path:
        p = Path.home() / ".aria" / "watch_targets.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text('{"targets":[]}', encoding="utf-8")
        return p

    def _load_watch_targets(self) -> list:
        p = self._watch_targets_file()
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data.get("targets", [])
        except Exception:
            return []

    def _save_watch_targets(self, targets: list) -> None:
        p = self._watch_targets_file()
        p.write_text(json.dumps({"targets": targets}, indent=2), encoding="utf-8")

    def _watch_add_target(self, spec: str) -> str:
        if not spec:
            return "Usage: /watch add pid=<pid> log=<path> name=<name>"
        target = {"id": f"t-{int(time.time())}"}
        for part in spec.split():
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            k = k.strip().lower()
            if k == "pid":
                try:
                    target["pid"] = int(v)
                except ValueError:
                    return "Error: Invalid pid value."
            elif k == "log":
                target["log"] = str(Path(v).expanduser())
            elif k == "name":
                target["name"] = v
            elif k == "oneshot":
                target["oneshot"] = v.lower() in ("1", "true", "yes", "on")
        if not target.get("pid") and not target.get("log"):
            return "Error: Add at least one of pid=<pid> or log=<path>."
        targets = self._load_watch_targets()
        targets.append(target)
        self._save_watch_targets(targets)
        return f"Watch target added: {target}"

    def _watch_remove_target(self, target_id: str) -> str:
        if not target_id:
            return "Usage: /watch remove <id>"
        targets = self._load_watch_targets()
        new_targets = [t for t in targets if str(t.get("id")) != target_id]
        if len(new_targets) == len(targets):
            return f"Error: No watch target found with id={target_id}"
        self._save_watch_targets(new_targets)
        return f"Removed watch target id={target_id}"

    def _watch_status(self) -> str:
        targets = self._load_watch_targets()
        lines = [f"Watch mode: {'enabled' if self.watch_mode.enabled else 'disabled'}"]
        lines.append(f"Tracked targets: {len(targets)}")
        for t in targets[:10]:
            lines.append(
                f"- {t.get('id')} name={t.get('name','-')} pid={t.get('pid','-')} log={t.get('log','-')}"
            )
        if not targets:
            lines.append("Tip: /watch add pid=<pid> log=<path> name=<name>")
        return "\n".join(lines)

    def cmd_models(self, args: str = "") -> str:
        if not self.api_client:
            return "Error: No API client."

        models = self.api_client.fetch_available_models()
        current = self.config_manager.get("model", "unknown")
        provider = self.config_manager.get("provider", "google")
        lines = [f"## Models | {UIManager.provider_label(provider)}", ""]
        if not models:
            lines.append("- No models returned. Check `/provider status` or your API key.")
            return "\n".join(lines)
        for m in models:
            tick = "X" if m == current else " "
            lines.append(f"- [{'x' if tick == 'X' else ' '}] `{m}`")
        lines.extend([
            "",
            f"Active: `{current}`",
            "Switch with `/model set <name>`",
        ])
        return "\n".join(lines)

    def cmd_provider(self, args: str = "") -> str:
        args = (args or "").strip()
        if not self.api_client:
            return "Error: No API client. Run /config."
        providers = self.api_client.get_supported_providers()
        current = self.config_manager.get("provider", "google")

        if not args or args == "list":
            lines = ["## Providers", ""]
            for key, label in providers.items():
                marker = "X" if key == current else " "
                has_key = bool(self.config_manager.get("api_keys", {}).get(key))
                shortcut = f"/provider {key}"
                lines.append(
                    f"- [{'x' if marker == 'X' else ' '}] `{key}`  {label}  "
                    f"key={'set' if has_key else 'missing'}  |  switch: `{shortcut}`"
                )
            lines.extend([
                "",
                "Shortcuts:",
                "- `/provider google`",
                "- `/provider openrouter`",
                "- `/provider nvidia_nim`",
                "- `/provider cycle`",
                "- `/provider key <name>` to update a saved key",
            ])
            return "\n".join(lines)

        if args == "status":
            return (
                f"Provider: {UIManager.provider_label(current)}\n"
                f"Model: {self.config_manager.get('model', 'unknown')}\n"
                f"API key: {'set' if self.config_manager.get('api_key') else 'missing'}"
            )

        if args == "cycle":
            return self._cycle_provider(providers, current)

        if args.startswith("key "):
            target = args[4:].strip().lower()
            if target not in providers:
                return f"Error: Unsupported provider: {target}"
            return self._set_provider_key(target)

        if args.startswith("set "):
            target = args[4:].strip().lower()
            return self._switch_provider(target, providers)

        if args in providers:
            return self._switch_provider(args, providers)

        return (
            "Usage: /provider list | /provider status | /provider cycle | "
            "/provider key <name> | /provider <name> | /provider set <name>"
        )

    def cmd_model(self, args: str = "") -> str:
        args = (args or "").strip()
        if not self.api_client:
            return "Error: No API client. Run /config."
        if not args or args == "list":
            return self.cmd_models("")
        if args == "status":
            return (
                f"Provider: {UIManager.provider_label(self.config_manager.get('provider', 'google'))}\n"
                f"Model: {self.config_manager.get('model', 'unknown')}"
            )
        if args.startswith("set "):
            model = args[4:].strip()
            if not model:
                return "Error: Missing model name."
            self.config_manager.set("model", model)
            self.config_manager.save()
            return self._reload_api_client_and_report()
        return "Usage: /model list | /model status | /model set <name>"

    def cmd_config(self, args: str = "") -> str:
        self.run_config_wizard()
        return "Configuration updated."

    def cmd_kb(self, query: str) -> str:
        results = self.knowledge_base.search(query)
        if not results:
            return f"Error: No KB results for: {query}"
        lines = [f"Knowledge Base ({len(results)} found):\n"]
        for i, r in enumerate(results[:5], 1):
            lines.append(f"{i}. {r.pattern.upper()}")
            lines.append(f"   {r.solution}")
            if r.auto_fixable:
                lines.append(f"   Fix: {r.fix_command}")
            lines.append("")
        return "\n".join(lines)

    def cmd_history(self, args: str = "") -> str:
        history = self.command_system.get_history(limit=10)
        if not history:
            return "No history."
        lines = ["Recent Commands:\n"]
        for i, cmd in enumerate(history, 1):
            lines.append(f"  {i}. {cmd}")
        return "\n".join(lines)

    def cmd_status(self, args: str = "") -> str:
        cfg = self.config_manager.config
        lines = ["ARIA Status\n"]
        lines.append(f"  Provider:   {cfg.get('provider') or '(not set)'}")
        lines.append(f"  Model:      {cfg.get('model') or '(not set)'}")
        lines.append(f"  API key:    {'set' if cfg.get('api_key') else 'NOT SET'}")
        lines.append(f"  Max tokens: {cfg.get('max_tokens', 8192)}")
        lines.append(f"  Guardian:   {'enabled' if self.guardian.enabled else 'disabled'}")
        lines.append(f"  Watch:      {'active' if self.watch_mode.enabled else 'off'}")

        if _HOOK_FILE.exists():
            try:
                data = json.loads(_HOOK_FILE.read_text())
                if data.get("cmd"):
                    lines.append(f"\n  Pending failure: $ {data['cmd']} (exit {data.get('code','?')})")
                    lines.append("  Run /fix to diagnose")
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

        cur_provider = self.config_manager.get("provider", "google")
        cur_keys = self.config_manager.get("api_keys", {})
        cur_key = cur_keys.get(cur_provider) or self.config_manager.get("api_key", "")
        cur_model = self.config_manager.get("model", "gemma-4-26b-a4b-it")

        provider = UIManager.prompt(
            f"Provider [{cur_provider}] (google/openrouter/nvidia_nim): "
        ).strip().lower() or cur_provider
        api_key = UIManager.prompt(
            f"API key for {provider} (Enter to keep current): "
        ).strip() or cur_key
        model   = UIManager.prompt(f"Model [{cur_model}]: ").strip() or cur_model
        guardian = UIManager.confirm("Enable Guardian safety mode?")
        auto_apply = UIManager.confirm("Enable auto-apply for fixes?", default=False)

        keys = self.config_manager.get("api_keys", {})
        keys[provider] = api_key
        self.config_manager.set("api_keys", keys)
        self.config_manager.set("provider", provider)
        self.config_manager.set("api_key", api_key)
        self.config_manager.set("model", model)
        self.config_manager.set("guardian_mode", guardian)
        self.config_manager.set("auto_apply", auto_apply)
        self.config_manager.set("max_tokens", 8192)
        self.config_manager.save()
        UIManager.display_success("Configuration saved!")

    def _set_provider_key(self, provider: str) -> str:
        api_keys = self.config_manager.get("api_keys", {})
        current_key = api_keys.get(provider, "")
        prompt = f"API key for {provider} (Enter to keep current): "
        key = UIManager.prompt(prompt).strip() or current_key
        if not key:
            return f"Error: No API key configured for {provider}."
        api_keys[provider] = key
        self.config_manager.set("api_keys", api_keys)
        if self.config_manager.get("provider") == provider:
            self.config_manager.set("api_key", key)
        self.config_manager.save()
        return f"Saved API key for {UIManager.provider_label(provider)}"

    def _switch_provider(self, target: str, providers: dict) -> str:
        if target not in providers:
            return f"Error: Unsupported provider: {target}"
        api_keys = self.config_manager.get("api_keys", {})
        key = api_keys.get(target, "")
        if not key:
            key = UIManager.prompt(f"API key for {target}: ").strip()
            if not key:
                return "Error: Provider switch cancelled (no API key)."
            api_keys[target] = key
            self.config_manager.set("api_keys", api_keys)
        self.config_manager.set("provider", target)
        self.config_manager.set("api_key", key)
        self.config_manager.save()
        return self._reload_api_client_and_report()

    def _cycle_provider(self, providers: dict, current: str) -> str:
        keys = list(providers.keys())
        if not keys:
            return "Error: No providers available."
        if current not in keys:
            return self._switch_provider(keys[0], providers)
        next_index = (keys.index(current) + 1) % len(keys)
        return self._switch_provider(keys[next_index], providers)

    def _set_watch_mode_pref(self, enabled: bool) -> None:
        self.config_manager.set("watch_mode", enabled)
        self.config_manager.save()

    def _reload_api_client_and_report(self) -> str:
        config = self.config_manager.load()
        try:
            self.api_client = APIClient(
                APIConfig(
                    api_key=config.get("api_key", ""),
                    model=config.get("model", ""),
                    temperature=config.get("temperature", 0.7),
                    max_tokens=config.get("max_tokens", 8192),
                    provider=config.get("provider", ""),
                    stream=config.get("stream", False),
                )
            )
            models = self.api_client.fetch_available_models()
            provider = config.get("provider", "google")
            active = config.get("model", "")
            if models and active not in models:
                self.config_manager.set("model", models[0])
                self.config_manager.save()
                active = models[0]
            return (
                f"Active provider: {provider}\n"
                f"Active model: {active}\n"
                f"Available models: {len(models)}"
            )
        except Exception as e:
            logger.error(f"Provider reload failed: {e}")
            return f"Error: Failed to switch provider/model: {e}"

    # ── Main loop ─────────────────────────────────────────────────

    def run(self):
        self.running = True
        UIManager.boot_sequence()

        if not self.setup():
            UIManager.display_error("Setup failed. See ~/.aria/aria.log")
            return

        UIManager.display_startup_hub(
            provider=self.config_manager.get("provider", "") or "(not set)",
            model=self.config_manager.get("model", "") or "(not set)",
            guardian_enabled=self.guardian.enabled,
            watch_enabled=self.watch_mode.enabled,
            commands=self._startup_commands(),
        )

        # ── Startup failure check (Cross-session) ─────────────────
        self._check_startup_failures()

        try:
            while self.running:
                # Non-blocking watch check before each prompt
                if self.watch_mode.enabled:
                    self.watch_mode.check_and_notify()

                user_input = UIManager.prompt()

                if not user_input.strip():
                    continue

                if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
                    UIManager.display_success("Goodbye.")
                    self.running = False
                    break

                parsed = self.command_system.parse_command(user_input)

                if parsed:
                    label = self._status_label_for_command(parsed["command"])
                    with UIManager.status(label) as st:
                        result = self._execute_with_timeout(
                            lambda: self.command_system.execute(parsed, status_handler=st),
                            timeout_s=120,
                            timeout_message="Command timed out after 120s.",
                        )
                    if result:
                        UIManager.display_response(result, is_markdown=False)
                else:
                    # Bare text → treat as /ask
                    with UIManager.status("Thinking... Querying model...") as st:
                        result = self._execute_with_timeout(
                            lambda: self.cmd_ask(user_input, status_handler=st),
                            timeout_s=120,
                            timeout_message="Model request timed out after 120s.",
                        )
                    if result:
                        UIManager.display_response(result, is_markdown=True)

        except KeyboardInterrupt:
            UIManager.display_info("\nGoodbye.")
            self.running = False
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            UIManager.display_error(f"Error: {e}\nSee ~/.aria/aria.log")
        finally:
            self.watch_mode.disable()

    def _check_startup_failures(self) -> None:
        """Check for pending failures from previous sessions."""
        if _HOOK_FILE.exists():
            try:
                data = json.loads(_HOOK_FILE.read_text())
                if data.get("cmd"):
                    UIManager.display_warning(
                        f"A pending failure was detected from a previous session:\n"
                        f"$ [bold]{data['cmd']}[/bold] (exit {data.get('code','?')})\n\n"
                        "Run [bold]/fix[/bold] to diagnose and repair.",
                        title="Cross-Session Failure Detected"
                    )
            except Exception:
                pass

    def _execute_with_timeout(self, fn, timeout_s: int, timeout_message: str) -> str:
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(fn)
                return future.result(timeout=timeout_s)
        except FutureTimeoutError:
            logger.error(timeout_message)
            return f"Error: {timeout_message}\nTry /models or /config, then retry."
        except Exception as e:
            logger.error(f"Execution failure: {e}")
            return f"Error: Execution failed: {e}"

    def _status_label_for_command(self, command_name: str) -> str:
        labels = {
            "ask": "Thinking... Querying model...",
            "fix": "Executing... Analyzing error context...",
            "install": "Executing... Planning installation...",
            "kb": "Executing... Searching knowledge base...",
            "models": "Connecting... Querying model registry...",
            "provider": "Connecting... Switching provider...",
            "model": "Connecting... Loading model metadata...",
            "watch": "Watching logs...",
            "status": "Executing...",
            "history": "Executing...",
            "help": "Executing...",
            "config": "Executing...",
        }
        return labels.get(command_name, "Executing...")


def main():
    try:
        aria = ARIA()
        aria.run()
    except Exception as e:
        logger.error(f"Fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
