"""
CLI entry point for ARIA.

Provides command-line interface for running ARIA.
"""

import sys
import click
from .main import ARIA


@click.group()
def cli():
    """ARIA — Autonomous Repair and Intelligence Agent for Termux development."""
    pass


@cli.command()
def start():
    """Start ARIA interactive session."""
    aria = ARIA()
    aria.run()


@cli.command()
def config():
    """Run configuration wizard."""
    aria = ARIA()
    aria.run_config_wizard()
    click.echo("✅ Configuration updated")


@cli.command()
@click.argument("query")
def ask(query):
    """Ask the AI a question."""
    aria = ARIA()
    if not aria.setup():
        click.echo("❌ Failed to setup ARIA")
        sys.exit(1)
    
    result = aria.cmd_ask(query)
    click.echo(result)


@cli.command()
@click.argument("error")
def fix(error):
    """Analyze and fix an error."""
    aria = ARIA()
    if not aria.setup():
        click.echo("❌ Failed to setup ARIA")
        sys.exit(1)
    
    result = aria.cmd_fix(error)
    click.echo(result)


@cli.command()
@click.argument("query")
def kb(query):
    """Search knowledge base."""
    aria = ARIA()
    if not aria.setup():
        click.echo("❌ Failed to setup ARIA")
        sys.exit(1)
    
    result = aria.cmd_kb(query)
    click.echo(result)


@cli.command()
def models():
    """List available models."""
    aria = ARIA()
    if not aria.setup():
        click.echo("❌ Failed to setup ARIA")
        sys.exit(1)
    
    result = aria.cmd_models("")
    click.echo(result)


@cli.command()
def version():
    """Show ARIA version."""
    click.echo("ARIA version 1.0.0")
    click.echo("Autonomous Repair and Intelligence Agent for Termux")


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
