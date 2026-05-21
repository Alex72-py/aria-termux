"""
Watch mode for ARIA — v4.1 Enhanced.

How it works:
- The shell hook (installed by install.sh) writes failed commands to ~/.aria/last_fail.json.
- WatchMode runs a background thread that polls this file and ~/.aria/watch.log.
- When a failure or error pattern is detected, it flags it for the main loop or
  shows a notification if it's safe to do so.
"""

import json
import logging
import re
import subprocess
import time
import threading
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .api_client import APIClient
    from .knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)

_ARIA_DIR = Path.home() / ".aria"
_HOOK_FILE = _ARIA_DIR / "last_fail.json"
_WATCH_LOG = _ARIA_DIR / "watch.log"
_RUNTIME_LOG = _ARIA_DIR / "runtime_errors.log"
_WATCH_TARGETS = _ARIA_DIR / "watch_targets.json"


class WatchMode:
    """Continuous background monitor for shell failures and log errors."""

    def __init__(self, kb: "KnowledgeBase"):
        self.kb = kb
        self.enabled = False
        self._api_client: Optional["APIClient"] = None
        
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        self._last_hook_ts: str = ""
        self._log_offsets: Dict[str, int] = {}
        self._tracked_targets: Dict[str, Dict[str, Any]] = {}
        self._pending_failures: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    @property
    def _pending_failure(self) -> Optional[Dict[str, Any]]:
        """Compatibility accessor for callers that expect a single pending event."""
        return self._pending_failures[0] if self._pending_failures else None

    @_pending_failure.setter
    def _pending_failure(self, value: Optional[Dict[str, Any]]) -> None:
        if value is None:
            self._pending_failures.clear()
            return
        self._pending_failures = [value]

    # ── Lifecycle ────────────────────────────────────────────────

    def enable(self, api_client=None, kb=None) -> None:
        """Start the background monitoring thread."""
        with self._lock:
            if self.enabled:
                return
            
            self.enabled = True
            self._pending_failures.clear()
            self._tracked_targets = {}
            self._log_offsets = {}
            if api_client:
                self._api_client = api_client
            if kb:
                self.kb = kb

            self._stop_event.clear()
            _ARIA_DIR.mkdir(parents=True, exist_ok=True)
            if not _WATCH_TARGETS.exists():
                _WATCH_TARGETS.write_text("{\"targets\": []}", encoding="utf-8")
            # Reset states to avoid old notifications
            if _HOOK_FILE.exists():
                try:
                    data = json.loads(_HOOK_FILE.read_text())
                    self._last_hook_ts = data.get("ts", "")
                except Exception:
                    self._last_hook_ts = ""
            else:
                self._last_hook_ts = ""
            
            if _WATCH_LOG.exists():
                self._log_offsets[str(_WATCH_LOG)] = _WATCH_LOG.stat().st_size
            else:
                _WATCH_LOG.touch()
                self._log_offsets[str(_WATCH_LOG)] = 0
            if _RUNTIME_LOG.exists():
                self._log_offsets[str(_RUNTIME_LOG)] = _RUNTIME_LOG.stat().st_size
            else:
                _RUNTIME_LOG.touch()
                self._log_offsets[str(_RUNTIME_LOG)] = 0

        self._sync_targets_file()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Watch mode background thread started")

    def disable(self) -> None:
        """Stop the background monitoring thread."""
        with self._lock:
            if not self.enabled:
                return
            
            self.enabled = False
            self._stop_event.set()
            
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        logger.info("Watch mode background thread stopped")

    # ── Background Loop ──────────────────────────────────────────

    def _monitor_loop(self):
        """Main loop for the background thread."""
        while not self._stop_event.is_set():
            try:
                self._check_hook_file()
                self._sync_targets_file()
                self._check_log_file(_WATCH_LOG, "watch.log")
                self._check_log_file(_RUNTIME_LOG, "runtime_errors.log")
                self._check_tracked_targets()
            except Exception as e:
                logger.error(f"Watch loop error: {e}")
            
            # Sleep to keep CPU usage low
            time.sleep(1.0)

    def _check_hook_file(self):
        """Check for new failures from the shell hook."""
        if not _HOOK_FILE.exists():
            return

        try:
            text = _HOOK_FILE.read_text().strip()
            if not text or text == "{}":
                return
            data = json.loads(text)
        except:
            return

        ts = data.get("ts", "")
        if ts and ts != self._last_hook_ts:
            with self._lock:
                self._last_hook_ts = ts
                self._pending_failures.append({
                    "type": "shell_hook",
                    "severity": "error",
                    "source": "shell-hook",
                    "timestamp": ts or "unknown",
                    "cmd": data.get("cmd", "unknown"),
                    "code": data.get("code", "?"),
                    "cwd": data.get("cwd", "?"),
                    "stderr": data.get("stderr", "")
                })
            logger.info(f"Detected new shell failure: {data.get('cmd')}")

    def _check_log_file(self, path: Path, source_name: str):
        """Check a log file for new error patterns."""
        if not path.exists():
            return

        try:
            key = str(path)
            current_size = path.stat().st_size
            previous_size = self._log_offsets.get(key, 0)

            if current_size < previous_size:
                # Log truncated or rotated
                self._log_offsets[key] = current_size
                return

            if current_size == previous_size:
                return

            with open(path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(previous_size)
                new_lines = f.readlines()

            self._log_offsets[key] = current_size

            if not new_lines:
                return

            content = "".join(new_lines)
            detected = self.detect_error(content)
            if detected:
                with self._lock:
                    self._pending_failures.append({
                        "type": "log_watch",
                        "severity": "error",
                        "source": source_name,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "pattern": detected[0],
                        "description": detected[1],
                        "context": self.extract_error_context(content)
                    })
                logger.info(f"Detected error in {source_name}: {detected[1]}")

        except Exception as e:
            logger.error(f"Error checking {source_name}: {e}")

    def _sync_targets_file(self):
        """Load externally registered targets from ~/.aria/watch_targets.json."""
        if not _WATCH_TARGETS.exists():
            return
        try:
            payload = json.loads(_WATCH_TARGETS.read_text(encoding="utf-8"))
            targets = payload.get("targets", [])
            incoming = {}
            for target in targets:
                key = str(target.get("id") or target.get("pid") or target.get("log"))
                if not key:
                    continue
                existing = self._tracked_targets.get(key, {})
                merged = dict(target)
                if "_running" in existing:
                    merged["_running"] = existing["_running"]
                incoming[key] = merged
                log_path = merged.get("log")
                if log_path:
                    p = Path(log_path).expanduser()
                    if p.exists():
                        self._log_offsets.setdefault(str(p), p.stat().st_size)
            with self._lock:
                self._tracked_targets = incoming
        except Exception as e:
            logger.error(f"Failed reading watch targets: {e}")

    def _check_tracked_targets(self):
        """Monitor tracked PIDs/logs across sessions."""
        import os

        for key, target in list(self._tracked_targets.items()):
            pid = target.get("pid")
            log_path = target.get("log")
            name = target.get("name") or f"target:{key}"

            if pid:
                running = self._pid_alive(int(pid))
                prev_running = target.get("_running", True)
                target["_running"] = running
                if prev_running and not running:
                    self._queue_event({
                        "type": "process_exit",
                        "severity": "error",
                        "source": name,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "description": "Tracked subprocess terminated",
                        "context": f"PID {pid} is no longer running",
                    })

            if log_path:
                p = Path(log_path).expanduser()
                if p.exists():
                    self._check_log_file(p, name)

            if target.get("oneshot") and not target.get("_running", True):
                del self._tracked_targets[key]

    def _pid_alive(self, pid: int) -> bool:
        """Termux-safe PID liveness check."""
        try:
            if pid <= 0:
                return False
            import os
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Can't signal it but likely exists in another context.
            return True
        except Exception:
            return False

    def _queue_event(self, event: Dict[str, Any]):
        with self._lock:
            self._pending_failures.append(event)

    # ── UI Integration ───────────────────────────────────────────

    def check_and_notify(self) -> bool:
        """
        Check if any new failure was detected by the background thread.
        Called by the main loop.
        """
        failures: List[Dict[str, Any]] = []
        with self._lock:
            if self._pending_failures:
                failures = self._pending_failures[:]
                self._pending_failures.clear()

        if not failures:
            return False

        for failure in failures:
            if failure["type"] == "shell_hook":
                self._show_shell_notification(
                    failure["cmd"], failure["code"], failure["cwd"], failure["stderr"]
                )
            else:
                self._show_structured_notification(failure)
        return True

    def _show_shell_notification(self, cmd: str, code, cwd: str, stderr: str):
        from rich.console import Console
        from rich.panel import Panel
        con = Console()

        con.print()
        con.print(Panel(
            f"[red]ERROR[/red]  [bold]{cmd}[/bold]  [dim](exit {code} | {cwd})[/dim]\n\n"
            "[dim]Type [bold]/fix[/bold] to diagnose | or just keep going[/dim]",
            title="[bold red]Watch: Command Failed[/bold red]",
            border_style="red",
        ))

        quick = self._quick_fixes(cmd + " " + stderr)
        if quick:
            con.print(f"  [yellow]TIP[/yellow]  Quick fix: [bold cyan]{quick[0]}[/bold cyan]")

    def _show_structured_notification(self, failure: Dict[str, Any]):
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        con = Console()

        table = Table(show_header=False, box=None, pad_edge=False)
        table.add_row("Type", failure.get("type", "unknown"))
        table.add_row("Source", failure.get("source", "unknown"))
        table.add_row("Severity", failure.get("severity", "error"))
        table.add_row("Time", failure.get("timestamp", "unknown"))
        table.add_row("Summary", failure.get("description", "Runtime error detected"))

        context = failure.get("context", "")
        con.print()
        con.print(Panel(
            f"{table}\n\n[dim]{context}[/dim]\n\n"
            "[dim]Type [bold]/fix[/bold] to analyze this log error[/dim]",
            title="[bold red]Watch: Runtime Error[/bold red]",
            border_style="red",
        ))

    # ── Analysis Logic ───────────────────────────────────────────

    def detect_error(self, output: str) -> Optional[Tuple[str, str]]:
        patterns = [
            (r"Traceback \(most recent call last\):", "Python Exception"),
            (r"ModuleNotFoundError: No module named '([\w.]+)'", "Missing Python Module"),
            (r"ImportError: (.*)", "Python Import Error"),
            (r"SyntaxError: (.*)", "Python Syntax Error"),
            (r"Segmentation fault", "Process Segfaulted"),
            (r"Permission denied", "Permission Denied"),
            (r"Connection refused", "Network Connection Refused"),
            (r"ReadTimeout|TimeoutError|timed out", "Timeout"),
            (r"429|rate limit|quota", "Model/API Rate Limit"),
            (r"401|403|invalid api key|permission denied", "Model/API Auth Failure"),
            (r"5\d\d|service unavailable|internal server error", "Model/API Server Error"),
            (r"Address already in use", "Port Conflict"),
            (r"No space left on device", "Disk Full"),
            (r"FATAL ERROR: (.*)", "Fatal System Error"),
            (r"ld: error: (.*)", "Linker Error"),
            (r"clang: error: (.*)", "Compiler Error"),
            (r"make: \*\*\* \[(.*)\] Error (\d+)", "Make Build Failure"),
            (r"ninja: build stopped: (.*)", "Ninja Build Failure"),
            (r"npm ERR! (.*)", "NPM Error"),
            (r"error: failed to push some refs to", "Git Push Failed"),
        ]
        for pat, desc in patterns:
            if re.search(pat, output, re.IGNORECASE):
                return pat, desc
        return None

    def extract_error_context(self, output: str) -> str:
        lines = output.strip().split("\n")
        # Get last 5 lines for context
        return "\n".join(lines[-5:])

    def _quick_fixes(self, text: str) -> List[str]:
        """Match known error patterns for instant suggestions."""
        PATTERNS = [
            (r"No module named '([\w.]+)'",             "pip install {0} --break-system-packages --prefer-binary"),
            (r"ModuleNotFoundError.*'([\w.]+)'",         "pip install {0} --break-system-packages --prefer-binary"),
            (r"bash: ([\w-]+): command not found",       "pkg install {0}"),
            (r"command not found.*[:`]\s*'?([\w-]+)'?", "pkg install {0}"),
            (r"Unable to locate package ([\S]+)",        "termux-change-repo && pkg update && pkg install {0}"),
            (r"externally.managed.environment",          "pip install <pkg> --break-system-packages --prefer-binary"),
            (r"failed to build|failed to run custom",   "pip install <pkg> --break-system-packages --prefer-binary"),
            (r"CERTIFICATE_VERIFY_FAILED",               "pip install --break-system-packages --trusted-host pypi.org <pkg>"),
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
                except:
                    fixes.append(fix)
        return fixes[:3]

    # ── Legacy Compatibility ─────────────────────────────────────

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
