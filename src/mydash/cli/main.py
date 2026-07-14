"""CLI entry point for mydash (Typer + Rich).

Registers top-level commands: ``brief`` (daily dashboard) and ``set``
(user preferences under ``cli.commands.set``).
"""

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.traceback import install

from mydash.cli.commands.set import set_app
from mydash.cli.renderers.brief import render_brief
from mydash.services.brief import BriefService

install(show_locals=True)

console = Console()
app = typer.Typer(help="mydash — personal daily dashboard in the terminal.")

load_dotenv()

# Preference subcommands: mydash set weather|stocks|news|geocoding|show
app.add_typer(set_app, name="set")


@app.callback()
def main() -> None:
    """mydash CLI. Use a subcommand such as ``brief`` or ``set``."""


@app.command("brief")
def brief():
    """Build and display the daily brief using saved user preferences."""
    brief_data = BriefService().build()
    render_brief(console, brief_data)


if __name__ == "__main__":
    app()
