"""``mydash init`` — first-run setup for city, units, category, and tickers.

Interactive by default. Pass any option and that answer is taken as given, so
the same command works in a dotfiles script.
"""

from __future__ import annotations

import asyncio

import typer
from rich.text import Text

from mydash.cli import ui
from mydash.cli.commands.config import config_table
from mydash.cli.context import config_service
from mydash.models.geocoding import Place
from mydash.services.user_config import (
    KNOWN_WEATHER_UNITS,
    UserConfigurationService,
    normalize_symbol,
)

CITY_MATCH_LIMIT = 5


def init(
    city: str | None = typer.Option(None, "--city", help="Place to forecast."),
    units: str | None = typer.Option(
        None,
        "--units",
        help=f"Weather units ({', '.join(sorted(KNOWN_WEATHER_UNITS))}).",
    ),
    category: str | None = typer.Option(
        None, "--category", help="News category, e.g. tech."
    ),
    symbols: str | None = typer.Option(
        None, "--symbols", "-s", help="Comma-separated tickers for the watch list."
    ),
) -> None:
    """Set up mydash: pick a city, units, a news category, and some tickers."""
    non_interactive = any(
        value is not None for value in (city, units, category, symbols)
    )

    with config_service() as service:
        current = service.get_configuration()

        if not non_interactive:
            ui.console.print(_welcome())

        _apply_city(service, city, current.city, interactive=not non_interactive)
        _apply_units(service, units, current.weather_units, not non_interactive)
        _apply_category(
            service, category, current.news_category, not non_interactive
        )
        _apply_symbols(
            service, symbols, current.stock_symbols, not non_interactive
        )

        final = service.get_configuration()

    ui.console.print(
        ui.panel(config_table(final), title="✅ You're set up", border="border.success")
    )
    hint = Text()
    hint.append("Run ", style="muted")
    hint.append("mydash brief", style="accent")
    hint.append(" for your dashboard, or ", style="muted")
    hint.append("mydash doctor", style="accent")
    hint.append(" if something looks off.", style="muted")
    ui.console.print(hint)


def _welcome() -> object:
    """Intro panel explaining what the wizard will ask."""
    body = Text()
    body.append("Four quick questions.", style="value")
    body.append(" Press Enter to keep what is already there.\n\n", style="muted")
    body.append_text(
        ui.bullets(
            [
                "City — used for the weather panel",
                "Units — metric or imperial",
                "News category — e.g. tech, politics",
                "Tickers — your markets watch list",
            ]
        )
    )
    return ui.panel(body, title="👋 Welcome to mydash", border="border.info")


def _apply_city(
    service: UserConfigurationService,
    city: str | None,
    current: str,
    interactive: bool,
) -> None:
    """Resolve and store the city, offering a choice between matches."""
    if city is None:
        if not interactive:
            return
        city = typer.prompt("City", default=current)
    if not city.strip() or city.strip() == current:
        return

    with ui.spinner(f"Looking up {city.strip()}…"):
        matches = asyncio.run(service.search_cities(city, limit=CITY_MATCH_LIMIT))

    place = _choose_place(matches, interactive=interactive)
    service.set_city_place(place)
    ui.console.print(Text(f"  → {place.label}", style="muted"))


def _choose_place(matches: list[Place], *, interactive: bool) -> Place:
    """Return the match to use, asking when several are plausible."""
    if len(matches) == 1 or not interactive:
        return matches[0]

    table = ui.detail_table()
    table.add_column("", style="accent", width=3, justify="right")
    table.add_column("Place", style="value")
    for index, place in enumerate(matches, start=1):
        table.add_row(str(index), place.label)
    ui.console.print(ui.panel(table, title="📍 Which one?", border="border.info"))

    while True:
        choice = typer.prompt("Pick a number", default=1, type=int)
        if 1 <= choice <= len(matches):
            return matches[choice - 1]
        ui.console.print(
            Text(f"Pick a number between 1 and {len(matches)}.", style="warn")
        )


def _apply_units(
    service: UserConfigurationService,
    units: str | None,
    current: str,
    interactive: bool,
) -> None:
    """Store the weather unit preset."""
    if units is None:
        if not interactive:
            return
        units = typer.prompt(
            f"Units ({', '.join(sorted(KNOWN_WEATHER_UNITS))})", default=current
        )
    service.set_weather_forecast_units(units)


def _apply_category(
    service: UserConfigurationService,
    category: str | None,
    current: str,
    interactive: bool,
) -> None:
    """Store the news category."""
    if category is None:
        if not interactive:
            return
        category = typer.prompt("News category", default=current)
    service.set_news_category(category)


def _apply_symbols(
    service: UserConfigurationService,
    symbols: str | None,
    current: list[str],
    interactive: bool,
) -> None:
    """Store the watch list, or leave it alone when the answer is blank."""
    if symbols is None:
        if not interactive:
            return
        symbols = typer.prompt("Tickers (comma-separated)", default=",".join(current))

    parsed = [part for part in symbols.split(",") if part.strip()]
    if not parsed:
        service.set_stock_symbols([])
        return

    try:
        service.set_stock_symbols([normalize_symbol(part) for part in parsed])
    except ValueError as err:
        raise typer.BadParameter(str(err), param_hint="--symbols") from err
