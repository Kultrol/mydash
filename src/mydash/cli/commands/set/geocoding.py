"""``mydash set geocoding`` — geocoding provider for city resolution."""

from __future__ import annotations

import typer

from mydash.cli.commands.set._helpers import (
    config_service,
    fmt_choices,
    hint_panel,
    require_arg,
    run,
)
from mydash.services.user_config import KNOWN_GEOCODING_PROVIDERS

app = typer.Typer(
    help="📍  Geocoding-related preferences (provider).",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def geocoding_root(ctx: typer.Context) -> None:
    """If no leaf subcommand was given, print geocoding next-step hints and exit."""
    if ctx.invoked_subcommand is not None:
        return
    hint_panel(
        title="📍  set geocoding",
        intro="Choose a geocoding setting to update.",
        next_steps=[
            f"provider <name> — geocoding API ({fmt_choices(KNOWN_GEOCODING_PROVIDERS)})",
        ],
        examples=[
            "mydash set geocoding provider open-meteo",
        ],
        tip="mydash set geocoding --help  ·  mydash set -lo",
    )
    raise typer.Exit(0)


@app.command("provider")
def provider(
    provider: str | None = typer.Argument(
        None,
        help=(
            "Geocoding provider. "
            f"Available: {fmt_choices(KNOWN_GEOCODING_PROVIDERS)}"
        ),
    ),
) -> None:
    """Set the geocoding API provider used when resolving cities."""
    provider = require_arg(
        provider,
        title="📍  set geocoding provider",
        intro="A geocoding provider name is required.",
        next_steps=[
            "Provide a provider: mydash set geocoding provider <name>",
        ],
        available=fmt_choices(KNOWN_GEOCODING_PROVIDERS),
        examples=[
            "mydash set geocoding provider open-meteo",
        ],
        tip="mydash set geocoding provider --help",
    )
    svc = config_service()

    def action() -> None:
        svc.set_geocoding_provider(provider)

    def message() -> str:
        return (
            f"Geocoding provider set to "
            f"[bold bright_white]{svc.get_geocoding_provider()}[/bold bright_white]\n"
            f"Available: [bright_cyan]{fmt_choices(KNOWN_GEOCODING_PROVIDERS)}[/bright_cyan]"
        )

    run(action, success_message=message, success_title="📍  Geocoding · provider")
