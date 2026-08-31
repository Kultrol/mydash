"""``mydash brief`` — the daily dashboard, and the per-domain shortcuts.

``brief`` fetches every panel concurrently; ``weather``, ``news``, and
``stocks`` fetch exactly one and render it with the same builder, so a panel
looks identical wherever you see it.
"""

from __future__ import annotations

import asyncio

import typer

from mydash.cli import ui
from mydash.cli.context import config_service, response_cache
from mydash.cli.renderers.brief import render_brief
from mydash.cli.renderers.news import headlines_panel
from mydash.cli.renderers.stocks import stocks_panel
from mydash.cli.renderers.weather import DEFAULT_HOURS, weather_panel
from mydash.client.http_api.http_api import HttpApiClient
from mydash.services.brief import BRIEF_DOMAINS, BriefService
from mydash.services.news import NewsService
from mydash.services.stocks import StocksService
from mydash.services.user_config import (
    KNOWN_WEATHER_UNITS,
    UserConfigurationService,
    normalize_symbol,
)
from mydash.services.weather import WeatherService

REFRESH_HELP = "Ignore cached responses and fetch live data."


def brief(
    refresh: bool = typer.Option(False, "--refresh", "-r", help=REFRESH_HELP),
    only: str | None = typer.Option(
        None,
        "--only",
        help=f"Comma-separated panels to show ({', '.join(BRIEF_DOMAINS)}).",
    ),
    compact: bool = typer.Option(
        False, "--compact", "-c", help="Denser tables with fewer columns."
    ),
    as_json: bool = typer.Option(
        False, "--json", help="Print the brief as JSON instead of panels."
    ),
) -> None:
    """Build and display the daily brief using saved user preferences."""
    domains = _parse_domains(only)

    with config_service() as service:
        with ui.spinner("Gathering your brief…"):
            data = asyncio.run(
                BriefService().build(
                    config_service=service, refresh=refresh, domains=domains
                )
            )

    if as_json:
        ui.console.print_json(data.model_dump_json())
        return

    render_brief(ui.console, data, compact=compact)


def weather(
    city: str | None = typer.Option(
        None, "--city", help="Forecast a different place just for this run."
    ),
    hours: int = typer.Option(
        DEFAULT_HOURS, "--hours", min=1, max=48, help="How many hours to show."
    ),
    units: str | None = typer.Option(
        None, "--units", help=f"Override units ({', '.join(sorted(KNOWN_WEATHER_UNITS))})."
    ),
    refresh: bool = typer.Option(False, "--refresh", "-r", help=REFRESH_HELP),
    compact: bool = typer.Option(False, "--compact", "-c", help="Fewer columns."),
) -> None:
    """Show just the weather panel."""
    with config_service() as service:
        config = service.get_configuration()
        chosen_units = _resolve_units(units, config.weather_units)

        async def run():
            async with _http(service, refresh) as http:
                weather_service = WeatherService(
                    weather_provider=config.provider_weather,
                    geocoding_provider=config.provider_geocoding,
                    http_client=http,
                )
                if city:
                    place, forecast = await weather_service.fetch_for_city(
                        city, units=chosen_units
                    )
                    return place.label, forecast
                forecast = await weather_service.fetch_forecast(
                    config.coordinates, units=chosen_units
                )
                return config.city, forecast

        with ui.spinner("Checking the forecast…"):
            label, forecast = asyncio.run(run())

    ui.console.print(
        weather_panel(
            forecast,
            city=label,
            units=chosen_units,
            hours=hours,
            compact=compact,
        )
    )


def news(
    category: str | None = typer.Option(
        None, "--category", help="Read a different category just for this run."
    ),
    limit: int = typer.Option(
        8, "--limit", "-n", min=1, max=50, help="How many headlines to show."
    ),
    refresh: bool = typer.Option(False, "--refresh", "-r", help=REFRESH_HELP),
    compact: bool = typer.Option(False, "--compact", "-c", help="Fewer columns."),
) -> None:
    """Show just the headlines panel."""
    with config_service() as service:
        config = service.get_configuration()
        chosen = (category or config.news_category).strip().lower()

        async def run():
            async with _http(service, refresh) as http:
                return await NewsService(
                    news_provider=config.provider_news, http_client=http
                ).fetch_news(category=chosen, limit=limit)

        with ui.spinner("Fetching headlines…"):
            headlines = asyncio.run(run())

    ui.console.print(
        headlines_panel(headlines, category=chosen, limit=limit, compact=compact)
    )


def stocks(
    symbols: str | None = typer.Option(
        None, "--symbols", "-s", help="Comma-separated tickers, just for this run."
    ),
    refresh: bool = typer.Option(False, "--refresh", "-r", help=REFRESH_HELP),
    compact: bool = typer.Option(False, "--compact", "-c", help="Fewer columns."),
) -> None:
    """Show just the markets panel."""
    with config_service() as service:
        config = service.get_configuration()
        watch_list = _parse_symbols(symbols) or list(config.stock_symbols)

        if not watch_list:
            ui.info(
                ui.bullets(
                    [
                        "Add one with: mydash set stocks add AAPL",
                        "Or pass tickers for this run: mydash stocks -s AAPL,MSFT",
                    ]
                ),
                title="📈 No symbols yet",
            )
            raise typer.Exit(0)

        async def run():
            async with _http(service, refresh) as http:
                return await StocksService(
                    stock_ticker_symbols=watch_list,
                    stock_provider=config.provider_stocks,
                    http_client=http,
                ).fetch_stock_bars_and_quotes()

        with ui.spinner("Checking the markets…"):
            quotes, bars = asyncio.run(run())

    ui.console.print(
        stocks_panel(quotes, bars, symbols=watch_list, compact=compact)
    )


def _http(service: UserConfigurationService, refresh: bool) -> HttpApiClient:
    """Build an HTTP client sharing the config database's response cache."""
    return HttpApiClient(cache=response_cache(service), refresh=refresh)


def _parse_domains(only: str | None) -> list[str] | None:
    """Split a ``--only`` value into domain names, or ``None`` for all."""
    if not only:
        return None
    return [part.strip() for part in only.split(",") if part.strip()]


def _parse_symbols(symbols: str | None) -> list[str]:
    """Split and validate a ``--symbols`` value.

    :raises typer.BadParameter: If a ticker is not a plausible symbol.
    """
    if not symbols:
        return []
    parsed: list[str] = []
    for part in symbols.split(","):
        if not part.strip():
            continue
        try:
            normalized = normalize_symbol(part)
        except ValueError as err:
            raise typer.BadParameter(str(err), param_hint="--symbols") from err
        if normalized not in parsed:
            parsed.append(normalized)
    return parsed


def _resolve_units(units: str | None, fallback: str) -> str:
    """Validate a ``--units`` override, falling back to the saved preset.

    :raises typer.BadParameter: If *units* is not a known preset.
    """
    if units is None:
        return fallback
    normalized = units.strip().lower()
    if normalized not in KNOWN_WEATHER_UNITS:
        raise typer.BadParameter(
            f"expected one of {sorted(KNOWN_WEATHER_UNITS)}", param_hint="--units"
        )
    return normalized
