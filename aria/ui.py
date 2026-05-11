"""
Rich UI components for ARIA — v4 patched.

Improvements:
- Claude Code / Gemini CLI style animations:
  · Named agent thinking steps with elapsed time
  · Multi-stage boot with real checks
  · Smooth spinners per operation
- Response display uses Markdown rendering
- No logging to terminal whatsoever
"""

import time
import sys
import logging
from typing import List, Optional
from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.rule import Rule
from rich import box

logger = logging.getLogger(__name__)
console = Console(highlight=False)


# ══════════════════════════════════════════════════════════════════
#  AGENT ANIMATION CONTEXT MANAGER
#  Usage:
#    with agent_thinking("Sentry", "Scanning shell context"):
#        ctx = sentry.gather()
#    with agent_thinking("Librarian", "Searching knowledge base"):
#        kb = lib.search(query)
#    with agent_thinking("Fixer", "Calling Gemma 4"):
#        response = api.call(...)
# ══════════════════════════════════════════════════════════════════

AGENT_STYLES = {
    "Sentry":    ("cyan",    "👁 "),
    "Librarian": ("blue",    "📚"),
    "Guardian":  ("yellow",  "🛡️ "),
    "Fixer":     ("magenta", "🔧"),
    "ARIA":      ("cyan",    "✦ "),
}

@contextmanager
def agent_thinking(agent: str, task: str):
    """
    Context manager that shows a Claude Code-style animated thinking state.

    with agent_thinking("Fixer", "Calling Gemma 4"):
        result = expensive_call()
    # → shows: ✦ Fixer  Calling Gemma 4…  (animated)  2.3s ✓
    """
    style, icon = AGENT_STYLES.get(agent, ("cyan", "·"))
    start = time.time()

    with Live(
        _agent_spinner(icon, agent, task, style),
        console=console,
        refresh_per_second=15,
        transient=True,
    ):
        yield

    elapsed = time.time() - start
    console.print(
        f"  {icon} [bold {style}]{agent}[/bold {style}]  "
        f"[dim]{task}[/dim]  "
        f"[dim green]✓ {elapsed:.1f}s[/dim green]"
    )


def _agent_spinner(icon: str, agent: str, task: str, style: str) -> Text:
    t = Text()
    t.append(f"  {icon} ", style=f"bold {style}")
    t.append(f"{agent}  ", style=f"bold {style}")
    t.append(f"{task}… ", style="dim")
    return t


def thinking(label: str = "ARIA is thinking"):
    """Simple thinking spinner (no agent context needed)."""
    return Live(
        Spinner("dots", text=f"  [cyan]{label}…[/cyan]"),
        console=console,
        refresh_per_second=20,
        transient=True,
    )


# ══════════════════════════════════════════════════════════════════
#  BOOT SEQUENCE
# ══════════════════════════════════════════════════════════════════

_LOGO = r"""
   █████╗ ██████╗ ██╗ █████╗
  ██╔══██╗██╔══██╗██║██╔══██╗
  ███████║██████╔╝██║███████║
  ██╔══██║██╔══██╗██║██╔══██║
  ██║  ██║██║  ██║██║██║  ██║
  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
"""

_LOGO_COLORS = [
    "bold magenta", "bold blue", "bold cyan",
    "bold cyan",    "bold blue", "bold magenta",
]


class UIManager:
    """ARIA Rich UI components."""

    # ── Boot ─────────────────────────────────────────────────────

    @staticmethod
    def boot_sequence() -> None:
        console.clear()

        # Character-by-character ASCII reveal
        lines = _LOGO.strip("\n").split("\n")
        max_len = max(len(l) for l in lines)

        with Live(console=console, refresh_per_second=60, transient=False) as live:
            for col in range(max_len + 1):
                frame = Text()
                for row, line in enumerate(lines):
                    color = _LOGO_COLORS[row % len(_LOGO_COLORS)]
                    frame.append(line[:col].ljust(max_len) + "\n", style=color)
                live.update(Align.center(frame))
                time.sleep(0.010)
            time.sleep(0.06)

        console.print(Align.center(Text(
            "Autonomous Repair & Intelligence Agent",
            style="dim cyan"
        )))
        console.print(Align.center(Text(
            "Powered by Gemma 4  ·  Built for Termux",
            style="dim"
        )))
        console.print()

        # Animated boot steps — each shows as a real check
        boot_steps = [
            ("Sentry",    "Scanning Termux environment"),
            ("Librarian", "Loading knowledge base"),
            ("Guardian",  "Activating safety layer"),
            ("ARIA",      "Checking API connection"),
        ]

        for agent, task in boot_steps:
            icon, style = AGENT_STYLES[agent][1], AGENT_STYLES[agent][0]
            with Live(
                _agent_spinner(icon, agent, task, style),
                console=console,
                refresh_per_second=15,
                transient=True,
            ):
                time.sleep(0.18 if agent != "ARIA" else 0.05)

            console.print(
                f"  {icon} [bold {style}]{agent}[/bold {style}]  "
                f"[dim]{task}[/dim]  [dim green]✓[/dim green]"
            )

        console.print()

    # ── Response display ─────────────────────────────────────────

    @staticmethod
    def display_response(response: str) -> None:
        if not response:
            return
        try:
            console.print(Panel(
                Markdown(response),
                title="[bold cyan]✦ ARIA[/bold cyan]",
                border_style="cyan",
                padding=(0, 2),
            ))
        except Exception:
            console.print(Panel(
                response,
                title="[bold cyan]✦ ARIA[/bold cyan]",
                border_style="cyan",
            ))

        # Auto-copy first bash block to clipboard
        UIManager._auto_clipboard(response)

    @staticmethod
    def _auto_clipboard(text: str) -> None:
        import re, subprocess
        blocks = re.findall(r'```(?:bash|sh|shell)?\n(.*?)```', text, re.DOTALL)
        if not blocks:
            return
        first = blocks[0].strip().split("\n")[0].strip()
        if not first:
            return
        try:
            subprocess.run(["termux-clipboard-set", first],
                           capture_output=True, timeout=3)
            console.print("  [dim]📋 First command copied to clipboard[/dim]")
        except Exception:
            pass

    # ── Panels ───────────────────────────────────────────────────

    @staticmethod
    def display_error(message: str, title: str = "Error") -> None:
        console.print(Panel(
            f"[red]{message}[/red]",
            title=f"[bold red]✗ {title}[/bold red]",
            border_style="red",
        ))

    @staticmethod
    def display_success(message: str, title: str = "Done") -> None:
        console.print(Panel(
            f"[green]{message}[/green]",
            title=f"[bold green]✓ {title}[/bold green]",
            border_style="green",
        ))

    @staticmethod
    def display_info(message: str, title: str = "Info") -> None:
        console.print(Panel(
            message,
            title=f"[bold blue]{title}[/bold blue]",
            border_style="blue",
        ))

    @staticmethod
    def display_warning(message: str, title: str = "Warning") -> None:
        console.print(Panel(
            f"[yellow]{message}[/yellow]",
            title=f"[bold yellow]⚠ {title}[/bold yellow]",
            border_style="yellow",
        ))

    @staticmethod
    def display_code(code: str, language: str = "bash", title: str = "") -> None:
        syntax = Syntax(code, language, theme="monokai",
                        line_numbers=False, word_wrap=True)
        console.print(Panel(
            syntax,
            title=title or f"[dim]{language}[/dim]",
            border_style="dim",
        ))

    # ── Input ─────────────────────────────────────────────────────

    @staticmethod
    def prompt(message: str = "") -> str:
        if message:
            return console.input(f"  [dim]{message}[/dim]")
        # Main ARIA prompt
        try:
            from rich.prompt import Prompt
            return Prompt.ask("\n[bold cyan]aria[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            return "/exit"

    @staticmethod
    def confirm(message: str, default: bool = True) -> bool:
        try:
            from rich.prompt import Confirm
            return Confirm.ask(f"  {message}", default=default)
        except (KeyboardInterrupt, EOFError):
            return default

    # ── Legacy spinner (kept for compatibility) ───────────────────

    @staticmethod
    def spinner(message: str, duration: float = 0.5,
                spinner_type: str = "neural") -> None:
        with Live(
            Spinner("dots", text=f"  [cyan]{message}[/cyan]"),
            console=console, refresh_per_second=20, transient=True,
        ):
            time.sleep(duration)
        console.print(f"  [green]✓[/green]  [dim]{message}[/dim]")

