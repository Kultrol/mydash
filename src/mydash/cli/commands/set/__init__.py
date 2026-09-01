"""``mydash set`` command tree — Typer one-file-per-command layout.

Domain modules each expose a :class:`typer.Typer` ``app`` that is registered
here with :meth:`add_typer`. Leaf ``show`` is registered as a command on this
root app. Incomplete paths (bare ``set`` / missing args) print Rich hint panels
instead of raw Click errors.
"""

from __future__ import annotations

import typer
from rich.text import Text

from mydash.cli.commands.set import geocoding, news, stocks, weather
from mydash.cli.commands.set._helpers import info, print_set_options
from mydash.cli.commands.set.show import show as show_command

set_app = typer.Typer(
    help="⚙️  Update mydash user preferences.",
    no_args_is_help=False,
)

set_app.add_typer(weather.app, name="weather")
set_app.add_typer(stocks.app, name="stocks")
set_app.add_typer(news.app, name="news")
set_app.add_typer(geocoding.app, name="geocoding")
set_app.command("show")(show_command)


@set_app.callback(invoke_without_command=True)
def set_root(
    ctx: typer.Context,
    list_options: bool = typer.Option(
        False,
        "--list-options",
        "-lo",
        help="List all set subcommands with domain grouping.",
    ),
) -> None:
    """Root of ``mydash set``: list options, or guide when no subcommand given.

    :param list_options: When true, print the full subcommand catalog and exit.
    """
    if list_options:
        print_set_options()
        raise typer.Exit(0)
    if ctx.invoked_subcommand is None:
        body = Text()
        body.append("No configuration change specified.\n\n", style="value")
        body.append("  • Run ", style="value")
        body.append("mydash set --help", style="accent")
        body.append(" for command help\n", style="value")
        body.append("  • Run ", style="value")
        body.append("mydash set -lo", style="accent")
        body.append(" to list all subcommands", style="value")
        info(body, title="ℹ️  mydash set")
        raise typer.Exit(0)


__all__ = ["set_app"]
