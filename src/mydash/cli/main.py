"""CLI entry point for mydash (Typer + Rich)."""

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.traceback import install

from mydash.cli.renderers.brief import render_brief
from mydash.services.brief import BriefService

install(show_locals=True)

console = Console()
app = typer.Typer(help="mydash — personal daily dashboard in the terminal.")

load_dotenv()


@app.callback()
def main() -> None:
    """mydash CLI. Use a subcommand such as ``brief``."""


@app.command("brief")
def brief():
    """Build and display the daily brief."""
    brief_data = BriefService().build()
    render_brief(console, brief_data)


if __name__ == "__main__":
    app()
