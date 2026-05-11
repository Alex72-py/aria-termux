"""
Watch mode for ARIA — v4 patched.

How it works:
- The shell hook (installed by install.sh via PROMPT_COMMAND) writes every
  failed command to ~/.aria/last_fail.json immediately after it exits.
- WatchMode.check_and_notify() is called before each ARIA prompt (non-blocking).
  If a new failure exists, it shows a notification panel and prompts to /fix.
- The user can also just type /fix at any time — it reads the same file.

Why this design (vs blocking subprocess-wrapper watch):
- Works across two terminal sessions: user works normally, ARIA notices failures.
- No blocking. No PTY hijacking. No subprocess gymnastics.
- Works with proot-distro too.
"""

import json
import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Optional, List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .api_client import APIClient
    from .knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

_HOOK_FILE = Path.home() / ".aria" / "last_fail.json"


class WatchMode:
    """Polls ~/.aria/last_fail.json and notifies on failures."""

    def __init__(self, kb: "KnowledgeBase"):
        self.kb = kb
        self.enabled = False
        self._api_client: Optional["APIClient"] = None
        self._last_seen_cmd: str = ""  # deduplicate notifications

    # ── Toggle ────────────────────────────────────────────────────

    def enable(self, api_client=None, kb=None) -> None:
        self.enabled = True
        if api_client:
            self._api_client = api_client
        if kb:
            self.kb = kb
        logger.info("Watch mode enabled")

    def disable(self) -> None:
        self.enabled = False
        logger.info("Watch mode disabled")

    # ── Core polling ─────────────────────────────────────────────

    def check_and_notify(self, api_client=None) -> bool:
        """
        Check ~/.aria/last_fail.json for a new failure.
        Called non-blocking before each ARIA prompt.

        Returns True if a failure was found and shown.
        """
        if api_client:
            self._api_client = api_client

        if not _HOOK_FILE.exists():
            return False

        try:
            text = _HOOK_FILE.read_text().strip()
            if not text or text == "{}":
                return False
            data = json.loads(text)
        except Exception:
            return False

        cmd = data.get("cmd", "")
        if not cmd or cmd == self._last_seen_cmd:
            return False

        code = data.get("code", "?")
        cwd  = data.get("cwd", "?")

        self._last_seen_cmd = cmd
        self._show_notification(cmd, code, cwd, data.get("stderr", ""))
        return True

    def _show_notification(self, cmd: str, code, cwd: str, stderr: str = ""):
        from rich.console import Console
        from rich.panel import Panel
        con = Console()

        con.print()
        con.print(Panel(
            f"[red]✗[/red]  [bold]{cmd}[/bold]  [dim](exit {code}  ·  {cwd})[/dim]\n\n"
            "[dim]Type [bold]/fix[/bold] to diagnose  ·  or just keep going[/dim]",
            title="[bold red]⚠  Watch: Command Failed[/bold red]",
            border_style="red",
        ))

        # Instant local fix from KB
        quick = self._quick_fixes(cmd + " " + stderr)
        if quick:
            con.print(
                f"  [yellow]⚡[/yellow]  Quick fix: "
                f"[bold cyan]{quick[0]}[/bold cyan]"
            )

    def _quick_fixes(self, text: str) -> List[str]:
        """Match known error patterns for instant suggestions."""
        PATTERNS = [
            (r"No module named '([\w.]+)'",             "pip install {0} --prefer-binary"),
            (r"ModuleNotFoundError.*'([\w.]+)'",         "pip install {0} --prefer-binary"),
            (r"bash: ([\w-]+): command not found",       "pkg install {0}"),
            (r"command not found.*[:`]\s*'?([\w-]+)'?", "pkg install {0}"),
            (r"Unable to locate package ([\S]+)",        "termux-change-repo && pkg update && pkg install {0}"),
            (r"externally.managed.environment",          "pip install <pkg> --break-system-packages --prefer-binary"),
            (r"failed to build|failed to run custom",   "pip install <pkg> --prefer-binary"),
            (r"CERTIFICATE_VERIFY_FAILED",               "pip install --trusted-host pypi.org <pkg>"),
            (r"(404|E: Failed to fetch).*mirror",        "termux-change-repo && pkg update"),
            (r"Permission denied",                       "chmod +x <file>  OR  check: ls -la"),
            (r"No space left on device",                 "pkg autoclean && df -h"),
            (r"Address already in use",                  "lsof -i :PORT  then kill PID"),
        ]
        fixes = []
        for pattern, fix in PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    fixes.append(fix.format(*m.groups()))
                except Exception:
                    fixes.append(fix)
        return fixes[:3]

    # ── Legacy API (kept for compatibility) ───────────────────────

    def detect_error(self, output: str):
        patterns = [
            (r"error",              "Generic error"),
            (r"failed",             "Operation failed"),
            (r"command not found",  "Command not found"),
            (r"permission denied",  "Permission denied"),
            (r"no such file",       "File not found"),
            (r"connection refused", "Connection refused"),
            (r"segmentation fault", "Segfault"),
        ]
        for pat, desc in patterns:
            if re.search(pat, output.lower()):
                return pat, desc
        return None

    def extract_error_context(self, output: str) -> str:
        lines = output.strip().split("\n")
        return "\n".join(lines[-5:] if len(lines) > 5 else lines)

    def search_solution(self, error_pattern: str):
        results = self.kb.search(error_pattern)
        return results[0].solution if results else None

    def get_auto_fix(self, error_pattern: str):
        results = self.kb.search(error_pattern)
        for r in results:
            if r.auto_fixable and r.fix_command:
                return r.fix_command
        return None

    def execute_fix(self, command: str) -> Tuple[bool, str]:
        try:
            r = subprocess.run(
                command, shell=True,
                capture_output=True, text=True, timeout=30,
            )
            return r.returncode == 0, r.stdout or r.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def analyze_error(self, error_output: str) -> dict:
        det = self.detect_error(error_output)
        if not det:
            return {"detected": False}
        pattern, description = det
        return {
            "detected":    True,
            "pattern":     pattern,
            "description": description,
            "solution":    self.search_solution(pattern),
            "auto_fixable": self.get_auto_fix(pattern) is not None,
            "fix_command": self.get_auto_fix(pattern),
            "context":     self.extract_error_context(error_output),
        }

    def format_suggestion(self, analysis: dict) -> str:
        if not analysis.get("detected"):
            return "No error detected"
        lines = [f"🔍 {analysis['description']}"]
        if analysis.get("solution"):
            lines.append(f"\n💡 {analysis['solution']}")
        if analysis.get("auto_fixable"):
            lines.append(f"\n🔧 Auto-fix: {analysis['fix_command']}")
        return "\n".join(lines)

