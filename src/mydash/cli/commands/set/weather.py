"""``mydash set weather`` — city, forecast units, and weather provider.

Incomplete ``mydash set weather`` shows next-step hints; leaf commands
update :class:`~mydash.services.user_config.UserConfigurationService`.
"""

from __future__ import annotations

import typer

from mydash.cli.commands.set._helpers import (
    config_service,
    fmt_choices,
    hint_panel,
    require_arg,
    run,
)
from mydash.services.user_config import KNOWN_WEATHER_PROVIDERS, KNOWN_WEATHER_UNITS

app = typer.Typer(
    help="🌤️  Weather-related preferences (city, units, provider).",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def weather_root(ctx: typer.Context) -> None:
    """If no leaf subcommand was given, print weather next-step hints and exit."""
    if ctx.invoked_subcommand is not None:
        return
    hint_panel(
        title="🌤️  set weather",
        intro="Choose a weather setting to update.",
        next_steps=[
            "city <city> — set location (geocodes and stores coordinates)",
            f"units <preset> — forecast units ({fmt_choices(KNOWN_WEATHER_UNITS)})",
            f"provider <name> — weather API ({fmt_choices(KNOWN_WEATHER_PROVIDERS)})",
        ],
        examples=[
            'mydash set weather city "New York"',
            "mydash set weather units imperial",
            "mydash set weather provider open-meteo",
        ],
        tip="mydash set weather --help  ·  mydash set -lo",
    )
    raise typer.Exit(0)


@app.command("city")
def city(
    city: str | None = typer.Argument(
        None,
        help="City name to geocode and store (updates city + coordinates).",
    ),
) -> None:
    """Geocode and store the brief weather location."""
    city = require_arg(
        city,
        title="🌤️  set weather city",
        intro="A city name is required.",
        next_steps=[
            'Provide a city: mydash set weather city "<city>"',
            "This geocodes the city and stores coordinates in your config.",
        ],
        examples=[
            'mydash set weather city "New York"',
            "mydash set weather city Miami",
        ],
        tip="mydash set weather city --help",
    )
    svc = config_service()

    def action() -> None:
        svc.set_city(city)

    def message() -> str:
        coords = svc.get_coordinates()
        return (
            f"City set to [bold bright_white]{svc.get_city()}[/bold bright_white]\n"
            f"Coordinates: [bright_cyan]{coords.latitude}[/bright_cyan], "
            f"[bright_cyan]{coords.longitude}[/bright_cyan]"
        )

    run(action, success_message=message, success_title="🌤️  Weather · city")


@app.command("units")
def units(
    units: str | None = typer.Argument(
        None,
        help=(
            "Forecast unit preset. "
            f"Available: {fmt_choices(KNOWN_WEATHER_UNITS)}"
        ),
    ),
) -> None:
    """Set metric or imperial forecast units for the brief."""
    units = require_arg(
        units,
        title="🌤️  set weather units",
        intro="A unit preset is required.",
        next_steps=[
            "Provide a preset: mydash set weather units <metric|imperial>",
        ],
        available=fmt_choices(KNOWN_WEATHER_UNITS),
        examples=[
            "mydash set weather units metric",
            "mydash set weather units imperial",
        ],
        tip="mydash set weather units --help",
    )
    svc = config_service()

    def action() -> None:
        svc.set_weather_forecast_units(units)

    def message() -> str:
        return (
            f"Weather units set to "
            f"[bold bright_white]{svc.get_weather_forecast_units()}[/bold bright_white]\n"
            f"Available: [bright_cyan]{fmt_choices(KNOWN_WEATHER_UNITS)}[/bright_cyan]"
        )

    run(action, success_message=message, success_title="🌤️  Weather · units")


@app.command("provider")
def provider(
    provider: str | None = typer.Argument(
        None,
        help=(
            "Weather data provider. "
            f"Available: {fmt_choices(KNOWN_WEATHER_PROVIDERS)}"
        ),
    ),
) -> None:
    """Set the weather API provider used by the brief."""
    provider = require_arg(
        provider,
        title="🌤️  set weather provider",
        intro="A weather provider name is required.",
        next_steps=[
            "Provide a provider: mydash set weather provider <name>",
        ],
        available=fmt_choices(KNOWN_WEATHER_PROVIDERS),
        examples=[
            "mydash set weather provider open-meteo",
        ],
        tip="mydash set weather provider --help",
    )
    svc = config_service()

    def action() -> None:
        svc.set_weather_provider(provider)

    def message() -> str:
        return (
            f"Weather provider set to "
            f"[bold bright_white]{svc.get_weather_provider()}[/bold bright_white]\n"
            f"Available: [bright_cyan]{fmt_choices(KNOWN_WEATHER_PROVIDERS)}[/bright_cyan]"
        )

    run(action, success_message=message, success_title="🌤️  Weather · provider")
