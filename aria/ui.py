"""Rich UI components for ARIA with the source project's visual design."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
import time
from contextlib import contextmanager
from typing import Dict, List

from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

C_PURPLE = "#7B2FF7"
C_CYAN = "#00D4AA"
C_GREEN = "#00C853"
C_AMBER = "#FFB300"
C_RED = "#FF1744"
C_BLUE = "#2979FF"
C_DIM = "#757575"

ARIA_THEME = Theme(
    {
        "brand": f"bold {C_PURPLE}",
        "brand_cyan": f"bold {C_CYAN}",
        "success": f"bold {C_GREEN}",
        "warning": f"bold {C_AMBER}",
        "error": f"bold {C_RED}",
        "info": f"bold {C_BLUE}",
        "dim": C_DIM,
        "title": f"bold {C_PURPLE}",
    }
)

SPINNERS = {
    "neural": ["o", "O", "0", "O"],
    "scan": ["[    ]", "[=   ]", "[==  ]", "[=== ]", "[====]"],
    "pulse": [".", "..", "...", "....", "...", ".."],
}

ASCII_ART = """
  █████╗ ██████╗ ██╗ █████╗
 ██╔══██╗██╔══██╗██║██╔══██╗
 ███████║██████╔╝██║███████║
 ██╔══██║██╔══██╗██║██╔══██║
 ██║  ██║██║  ██║██║██║  ██║
 ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
""".strip("\n")

console = Console(theme=ARIA_THEME, highlight=False)


def thinking(label: str = "ARIA is thinking"):
    return Live(
        Spinner("dots", text=f"  [brand_cyan]{label}...[/brand_cyan]"),
        console=console,
        refresh_per_second=20,
        transient=True,
    )


class LiveStatus:
    """Handle dynamic status updates during a long-running AI operation."""
    def __init__(self, spinner: Spinner, live: Live):
        self.spinner = spinner
        self.live = live

    def update(self, label: str):
        """Update the status label dynamically."""
        self.spinner.text = f"  [brand_cyan]{label}...[/brand_cyan]"
        self.live.refresh()

@contextmanager
def status(label: str):
    spinner = Spinner("dots", text=f"  [brand_cyan]{label}[/brand_cyan]")
    with Live(
        spinner,
        console=console,
        refresh_per_second=18,
        transient=True,
    ) as live:
        yield LiveStatus(spinner, live)


class UIManager:
    """ARIA Rich UI components."""

    @staticmethod
    def boot_sequence() -> None:
        console.clear()
        UIManager._animated_logo_reveal()
        console.print()
        UIManager._scan_step("Initializing neural link...", "neural", 0.35)
        UIManager._scan_step("Scanning Termux environment...", "scan", 0.30)
        UIManager._scan_step("Loading knowledge base...", "pulse", 0.30)
        UIManager._scan_step("Preparing command system...", "scan", 0.25)
        console.print()

    @staticmethod
    def _animated_logo_reveal() -> None:
        """Fast character-by-character ARIA logo reveal animation."""
        lines = ASCII_ART.splitlines()
        colors = [
            f"bold {C_PURPLE}",
            f"bold {C_BLUE}",
            f"bold {C_CYAN}",
            f"bold {C_CYAN}",
            f"bold {C_BLUE}",
            f"bold {C_PURPLE}",
        ]
        max_len = max(len(l) for l in lines)

        # Character-by-character reveal (fast, lightweight)
        with Live(console=console, refresh_per_second=60, transient=False) as live:
            for col in range(0, max_len + 1, 2):  # step by 2 for speed
                frame = Text()
                for idx, line in enumerate(lines):
                    color = colors[idx % len(colors)]
                    frame.append(line[:col].ljust(max_len) + "\n", style=color)
                live.update(Align.center(frame))
                time.sleep(0.008)

        console.print(Align.center(Text("Autonomous Repair and Intelligence Agent", style=f"dim {C_CYAN}")))
        console.print(Align.center(Text("Terminal-Native Repair and Automation for Termux", style=f"dim {C_DIM}")))

    @staticmethod
    def _print_ascii() -> None:
        """Static fallback for non-animated contexts."""
        lines = ASCII_ART.splitlines()
        colors = [
            f"bold {C_PURPLE}",
            f"bold {C_BLUE}",
            f"bold {C_CYAN}",
            f"bold {C_CYAN}",
            f"bold {C_BLUE}",
            f"bold {C_PURPLE}",
        ]
        for idx, line in enumerate(lines):
            console.print(Text(line, style=colors[idx % len(colors)]), justify="center")
        console.print(Align.center(Text("Autonomous Repair and Intelligence Agent", style=f"dim {C_CYAN}")))
        console.print(Align.center(Text("Terminal-Native Repair and Automation for Termux", style=f"dim {C_DIM}")))

    @staticmethod
    def _scan_step(label: str, spinner_name: str = "neural", delay: float = 0.4) -> bool:
        frames = SPINNERS.get(spinner_name, SPINNERS["neural"])
        start = time.time()
        idx = 0
        while time.time() - start < delay:
            frame = frames[idx % len(frames)]
            console.print(f"  {frame} {label}", end="\r", style=C_PURPLE)
            idx += 1
            time.sleep(0.08)
        console.print(" " * 80, end="\r")
        console.print(f"  [success][ok][/success] {label}")
        return True

    @staticmethod
    def display_startup_hub(
        *,
        provider: str,
        model: str,
        guardian_enabled: bool,
        watch_enabled: bool,
        commands: List[Dict[str, str]],
    ) -> None:
        status_table = Table(show_header=False, box=None, pad_edge=False)
        status_table.add_row("Provider", f"[brand_cyan]{UIManager.provider_label(provider)}[/brand_cyan]")
        status_table.add_row("Model", f"[bold]{model}[/bold]")
        status_table.add_row("Guardian", "[success]online[/success]" if guardian_enabled else "[dim]offline[/dim]")
        status_table.add_row("Watch", "[success]online[/success]" if watch_enabled else "[dim]offline[/dim]")

        device_name, android = UIManager._device_info()
        battery = UIManager._battery_info()
        ram = UIManager._memory_info()
        session_id = hashlib.md5(f"{time.time()}-{provider}-{model}".encode()).hexdigest()[:8]

        system_table = Table(show_header=False, box=None, pad_edge=False)
        system_table.add_row("Device", f"[bold]{device_name}[/bold]")
        system_table.add_row("Android", android)
        system_table.add_row("Battery", battery)
        system_table.add_row("RAM", ram)
        system_table.add_row("Session", session_id)

        command_table = Table(show_header=False, box=None, pad_edge=False)
        command_table.add_column(no_wrap=True)
        command_table.add_column()
        for item in commands:
            command_table.add_row(
                f"[brand_cyan]{item['command']}[/brand_cyan]",
                f"[dim]{item['description']}[/dim]",
            )

        left = Panel(
            status_table,
            title="[title]Session[/title]",
            border_style=C_PURPLE,
            padding=(0, 1),
        )
        middle = Panel(
            system_table,
            title="[title]System[/title]",
            border_style=C_PURPLE,
            padding=(0, 1),
        )
        right = Panel(
            command_table,
            title="[brand_cyan]Commands[/brand_cyan]",
            subtitle="[dim]Bare text uses /ask[/dim]",
            border_style=C_CYAN,
            padding=(0, 1),
        )

        console.print(Columns([left, middle, right], equal=True, expand=True))

        console.print(
            Panel(
                "[bold]Quick Control[/bold]\n"
                "[brand_cyan]/provider google[/brand_cyan]  [dim]switch immediately[/dim]\n"
                "[brand_cyan]/provider openrouter[/brand_cyan]  [dim]use saved key or prompt once[/dim]\n"
                "[brand_cyan]/provider nvidia_nim[/brand_cyan]  [dim]same flow[/dim]\n"
                "[brand_cyan]/provider cycle[/brand_cyan]  [dim]jump to the next configured provider[/dim]\n"
                "[brand_cyan]/model list[/brand_cyan]  [dim]browse models for the active provider[/dim]",
                title="[warning]Control Surface[/warning]",
                border_style=C_AMBER,
                padding=(0, 1),
            )
        )
        console.print()

    @staticmethod
    def _device_info() -> tuple[str, str]:
        model = UIManager._run_command(["getprop", "ro.product.model"]) or "Unknown Device"
        android = UIManager._run_command(["getprop", "ro.build.version.release"]) or "?"
        return model, android

    @staticmethod
    def _battery_info() -> str:
        # 1. Try Termux API (most reliable if installed)
        try:
            raw = UIManager._run_command(["termux-battery-status"], timeout=5)
            if raw:
                payload = json.loads(raw)
                percentage = payload.get("percentage")
                if percentage is not None:
                    return f"{percentage}%"
        except Exception:
            pass

        # 2. Try sysfs (common on Android/Linux)
        for candidate in (
            Path("/sys/class/power_supply/battery/capacity"),
            Path("/sys/class/power_supply/BAT0/capacity"),
            Path("/sys/class/power_supply/ac/capacity"),
        ):
            try:
                if candidate.exists():
                    value = candidate.read_text(encoding="utf-8", errors="replace").strip()
                    if value and value.isdigit():
                        return f"{value}%"
            except Exception:
                pass

        # 3. Try dumpsys as last resort
        raw = UIManager._run_command(["dumpsys", "battery"], timeout=3)
        if raw:
            for line in raw.splitlines():
                stripped = line.strip()
                if stripped.lower().startswith("level:"):
                    level = stripped.split(":", 1)[1].strip()
                    if level and level.isdigit():
                        return f"{level}%"

        return "Unavailable"

    @staticmethod
    def _memory_info() -> str:
        raw = UIManager._run_command(["free", "-m"])
        if not raw:
            return "?MB"
        lines = raw.strip().splitlines()
        if len(lines) < 2:
            return "?MB"
        
        # Parse the 'Mem:' line
        parts = lines[1].split()
        if len(parts) >= 7:
            # available is usually at index 6
            return f"{parts[6]}MB avail"
        elif len(parts) >= 4:
            # fallback to free at index 3
            return f"{parts[3]}MB free"
        
        return "?MB"

    @staticmethod
    def _run_command(cmd: list[str], timeout: int = 2) -> str:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""

    @staticmethod
    def display_response(response: str, is_markdown: bool = True) -> None:
        if not response:
            return
        
        if is_markdown:
            try:
                body = Markdown(response)
            except Exception:
                body = response
        else:
            body = response

        console.print(
            Panel(
                body,
                title="[brand_cyan]ARIA[/brand_cyan]",
                border_style=C_CYAN,
                padding=(0, 2),
            )
        )
        UIManager._auto_clipboard(response)

    @staticmethod
    def _auto_clipboard(text: str) -> None:
        import re

        blocks = re.findall(r"```(?:bash|sh|shell)?\n(.*?)```", text, re.DOTALL)
        if not blocks:
            return
        first = blocks[0].strip().split("\n")[0].strip()
        if not first:
            return
        try:
            subprocess.run(["termux-clipboard-set", first], capture_output=True, timeout=3)
            console.print("  [dim]First command copied to clipboard[/dim]")
        except Exception:
            pass

    @staticmethod
    def display_error(message: str, title: str = "Error") -> None:
        console.print(Panel(f"[error]{message}[/error]", title=f"[error]{title}[/error]", border_style=C_RED))

    @staticmethod
    def display_success(message: str, title: str = "Done") -> None:
        console.print(Panel(f"[success]{message}[/success]", title=f"[success]{title}[/success]", border_style=C_GREEN))

    @staticmethod
    def display_info(message: str, title: str = "Info") -> None:
        console.print(Panel(message, title=f"[info]{title}[/info]", border_style=C_BLUE))

    @staticmethod
    def display_warning(message: str, title: str = "Warning") -> None:
        console.print(Panel(f"[warning]{message}[/warning]", title=f"[warning]{title}[/warning]", border_style=C_AMBER))

    @staticmethod
    def display_code(code: str, language: str = "bash", title: str = "") -> None:
        syntax = Syntax(code, language, theme="monokai", line_numbers=False, word_wrap=True)
        console.print(Panel(syntax, title=title or f"[dim]{language}[/dim]", border_style=C_DIM))

    @staticmethod
    def prompt(message: str = "") -> str:
        if message:
            return console.input(f"  [dim]{message}[/dim]")
        try:
            return Prompt.ask("\n[brand_cyan]aria[/brand_cyan]")
        except (KeyboardInterrupt, EOFError):
            return "/exit"

    @staticmethod
    def confirm(message: str, default: bool = True) -> bool:
        try:
            return Confirm.ask(f"  {message}", default=default)
        except (KeyboardInterrupt, EOFError):
            return default

    @staticmethod
    @contextmanager
    def status(label: str):
        with status(label):
            yield

    @staticmethod
    def spinner(message: str, duration: float = 0.5, spinner_type: str = "neural") -> None:
        with Live(
            Spinner("dots", text=f"  [brand_cyan]{message}[/brand_cyan]"),
            console=console,
            refresh_per_second=20,
            transient=True,
        ):
            time.sleep(duration)
        console.print(f"  [success][ok][/success] [dim]{message}[/dim]")

    @staticmethod
    def provider_label(provider: str) -> str:
        labels = {
            "google": "Google AI Studio",
            "openrouter": "OpenRouter",
            "nvidia_nim": "NVIDIA NIM",
        }
        return labels.get(provider, provider)
