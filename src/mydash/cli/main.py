"""CLI entry point for mydash (Typer + Rich).

Assembles the command tree and decides how failures are shown. Ordinary
mistakes — a city that does not exist, a provider that is down — get a short
panel; ``--debug`` puts the full traceback back.
"""

from __future__ import annotations

import sys
from types import TracebackType

import typer
from dotenv import load_dotenv
from rich.text import Text

from mydash import __version__
from mydash.cli import ui
from mydash.cli.commands import brief as brief_commands
from mydash.cli.commands import cache as cache_commands
from mydash.cli.commands import config as config_commands
from mydash.cli.commands import doctor as doctor_command
from mydash.cli.commands import init as init_command
from mydash.cli.commands.set import set_app
from mydash.cli.context import config_service, flags

app = typer.Typer(
    help="mydash — your personal daily dashboard in the terminal.",
    no_args_is_help=False,
    add_completion=True,
)

load_dotenv()

# Daily dashboard and its single-panel shortcuts.
app.command("brief")(brief_commands.brief)
app.command("weather")(brief_commands.weather)
app.command("news")(brief_commands.news)
app.command("stocks")(brief_commands.stocks)

# Setup and maintenance.
app.command("init")(init_command.init)
app.command("doctor")(doctor_command.doctor)
app.add_typer(set_app, name="set")
app.add_typer(config_commands.app, name="config")
app.add_typer(cache_commands.app, name="cache")


#: Shown by the welcome panel, in the order a new user needs them.
COMMAND_SUMMARY: tuple[tuple[str, str], ...] = (
    ("brief", "Markets, weather, and headlines in one view"),
    ("weather", "Just the forecast"),
    ("news", "Just the headlines"),
    ("stocks", "Just your watch list"),
    ("set", "Change a preference"),
    ("config", "Show, locate, or reset preferences"),
    ("cache", "Inspect or clear cached responses"),
    ("doctor", "Check storage, credentials, and providers"),
    ("init", "Run the setup wizard"),
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-V", help="Show the mydash version and exit."
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Show full tracebacks instead of error panels."
    ),
    no_color: bool = typer.Option(
        False, "--no-color", help="Disable colour and styling."
    ),
) -> None:
    """mydash CLI. Run a subcommand such as ``brief`` or ``set``."""
    flags.debug = debug
    ui.set_color(not no_color)
    _install_error_handler(debug)

    if version:
        ui.console.print(f"mydash {__version__}")
        raise typer.Exit(0)

    if ctx.invoked_subcommand is None:
        _welcome()
        raise typer.Exit(0)


def _welcome() -> None:
    """Landing panel: what is configured, and what you can run. No network."""
    ui.console.print(_summary_panel())
    ui.console.print(_commands_panel())

    hint = Text()
    hint.append("New here? Run ", style="muted")
    hint.append("mydash init", style="accent")
    hint.append(" to set things up, then ", style="muted")
    hint.append("mydash brief", style="accent")
    hint.append(".", style="muted")
    ui.console.print(hint)


def _summary_panel():
    """Panel showing the current preferences, or a nudge to run init."""
    body = Text()
    try:
        with config_service() as service:
            config = service.get_configuration()
    except Exception as err:  # storage problems must not break the landing page
        body.append("Could not read your preferences.\n", style="warn")
        body.append(str(err), style="muted")
        return ui.panel(body, title="🌟 mydash", border="warn")

    body.append("City      ", style="muted")
    body.append(f"{config.city}\n", style="value")
    body.append("Units     ", style="muted")
    body.append(f"{config.weather_units}\n", style="value")
    body.append("News      ", style="muted")
    body.append(f"{config.news_category}\n", style="value")
    body.append("Watching  ", style="muted")
    body.append(", ".join(config.stock_symbols) or "(nothing yet)", style="value")
    return ui.panel(
        body, title="🌟 mydash", border="border.info", subtitle=f"v{__version__}"
    )


def _commands_panel():
    """Panel listing every command with a one-line description."""
    table = ui.detail_table()
    table.add_column("Command", style="accent", no_wrap=True)
    table.add_column("Does", style="value")
    for name, description in COMMAND_SUMMARY:
        table.add_row(f"mydash {name}", description)
    return ui.panel(table, title="📋 Commands", border="border.info")


def _install_error_handler(debug: bool) -> None:
    """Route uncaught failures to a panel, or to a traceback under --debug."""
    if debug:
        from rich.traceback import install

        install(show_locals=True)
        return

    sys.excepthook = _excepthook


def _excepthook(
    exc_type: type[BaseException],
    exc: BaseException,
    traceback: TracebackType | None,
) -> None:
    """Print a short panel for an uncaught failure."""
    if issubclass(exc_type, KeyboardInterrupt):
        ui.console.print(Text("Cancelled.", style="muted"))
        return
    ui.render_exception(exc, hint=_hint_for(exc))


def _hint_for(exc: BaseException) -> str | None:
    """Suggest a next step based on what kind of failure this is."""
    from mydash.client.geocoding.base_errors import CityNotFoundError
    from mydash.client.http_api.errors import HttpApiError
    from mydash.client.stocks.providers.alpaca.errors import MissingCredentialsError

    if isinstance(exc, MissingCredentialsError):
        return "Copy .env.example to .env and fill in your Alpaca keys."
    if isinstance(exc, CityNotFoundError):
        return "Try a larger nearby city, or add the country: 'Paris, France'."
    if isinstance(exc, HttpApiError):
        return "Check your connection, then run: mydash doctor"
    if isinstance(exc, ValueError):
        return "Run 'mydash config show' to see what is currently stored."
    return "Run 'mydash doctor' to check storage, credentials, and providers."


if __name__ == "__main__":
    app()
