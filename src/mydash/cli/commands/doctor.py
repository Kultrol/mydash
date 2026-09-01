"""``mydash doctor`` — check storage, credentials, and provider reachability.

Answers the question you actually have when a panel is empty: is it my
config, my keys, or the provider?
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import typer
from rich.text import Text

from mydash.cli import ui
from mydash.cli.context import config_service, response_cache
from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.news.factory import get_news_client
from mydash.client.stocks.providers.alpaca.alpaca import AlpacaClient
from mydash.client.stocks.providers.alpaca.errors import MissingCredentialsError
from mydash.client.weather.factory import get_weather_client
from mydash.env import load_environment, user_env_path
from mydash.services.user_config import UserConfig, UserConfigurationService

OK = "✅"
FAILED = "❌"
# No trailing space: the status column is sized in cells, and a variation
# selector plus padding pushed this past the width and rendered as an ellipsis.
SKIPPED = "⚠️"


@dataclass
class Check:
    """One diagnostic result."""

    name: str
    status: str
    detail: str

    @property
    def failed(self) -> bool:
        return self.status == FAILED


def doctor(
    offline: bool = typer.Option(
        False, "--offline", help="Skip the provider reachability checks."
    ),
) -> None:
    """Check that mydash can reach its storage, credentials, and providers."""
    with config_service() as service:
        config = service.get_configuration()
        checks = _local_checks(service, config)

        if not offline:
            with ui.spinner("Contacting providers…"):
                checks += asyncio.run(_provider_checks(service, config))

    _render(checks, offline=offline)
    if any(check.failed for check in checks):
        raise typer.Exit(1)


def _local_checks(
    service: UserConfigurationService, config: UserConfig
) -> list[Check]:
    """Checks that need no network."""
    stats = response_cache(service).stats()
    credentials_status, credentials_detail = _credentials()

    return [
        Check("Database", OK, str(service.database_path)),
        Check("Credentials file", *_env_file()),
        Check(
            "Preferences",
            OK,
            f"{config.city} · {config.weather_units} · {config.news_category}",
        ),
        Check(
            "Watch list",
            OK if config.stock_symbols else SKIPPED,
            ", ".join(config.stock_symbols) or "empty — add one with 'set stocks add'",
        ),
        Check("Alpaca credentials", credentials_status, credentials_detail),
        Check(
            "Response cache",
            OK,
            f"{stats.fresh} fresh, {stats.expired} expired",
        ),
    ]


def _env_file() -> tuple[str, str]:
    """Report which env file supplied credentials, if any."""
    loaded = load_environment()
    if loaded:
        return OK, ", ".join(str(path) for path in loaded)
    return (
        SKIPPED,
        f"none found — 'mydash config env --create' writes one at {user_env_path()}",
    )


def _credentials() -> tuple[str, str]:
    """Report whether Alpaca credentials are present."""
    try:
        AlpacaClient.credentials()
    except MissingCredentialsError as err:
        return SKIPPED, f"not set ({', '.join(err.missing)}) — markets panel is off"
    return OK, "found in the environment"


async def _provider_checks(
    service: UserConfigurationService, config: UserConfig
) -> list[Check]:
    """Ping every configured provider once, concurrently."""
    async with HttpApiClient(
        cache=response_cache(service), refresh=True, retries=0
    ) as http:
        probes: list[tuple[str, Callable[[], Awaitable[str]]]] = [
            (
                "Geocoding provider",
                lambda: _describe_geocoding(config, http),
            ),
            (
                "Weather provider",
                lambda: _describe_weather(config, http),
            ),
            (
                "News provider",
                lambda: _describe_news(config, http),
            ),
        ]
        if config.stock_symbols:
            probes.append(("Stocks provider", lambda: _describe_stocks(config, http)))

        results = await asyncio.gather(
            *(probe() for _, probe in probes), return_exceptions=True
        )

    checks: list[Check] = []
    for (name, _), result in zip(probes, results, strict=True):
        if isinstance(result, BaseException):
            checks.append(Check(name, FAILED, str(result) or type(result).__name__))
        else:
            checks.append(Check(name, OK, result))
    return checks


async def _describe_geocoding(config: UserConfig, http: HttpApiClient) -> str:
    client = get_geocoding_client(config.provider_geocoding, http_client=http)
    places = await client.search(config.city, limit=1)
    return f"{config.provider_geocoding} → {places[0].label}"


async def _describe_weather(config: UserConfig, http: HttpApiClient) -> str:
    client = get_weather_client(config.provider_weather, http_client=http)
    forecast = await client.fetch_forecast(
        config.coordinates, units=config.weather_units
    )
    hours = sum(len(day.hours) for day in forecast.days)
    return f"{config.provider_weather} → {hours} hours, {forecast.timezone or 'no zone'}"


async def _describe_news(config: UserConfig, http: HttpApiClient) -> str:
    client = get_news_client(config.provider_news, http_client=http)
    headlines = await client.fetch_headlines(config.news_category, limit=5)
    return f"{config.provider_news} → {len(headlines.headlines)} headlines"


async def _describe_stocks(config: UserConfig, http: HttpApiClient) -> str:
    client = AlpacaClient(http_client=http)
    quotes = await client.fetch_quotes(list(config.stock_symbols))
    detail = f"{config.provider_stocks} → {len(quotes.quotes)} quotes"
    if quotes.missing:
        detail += f" (no data for {', '.join(quotes.missing)})"
    return detail


def _render(checks: list[Check], *, offline: bool) -> None:
    """Print the checks as a status table with a verdict underneath."""
    table = ui.detail_table()
    table.add_column("", width=3, no_wrap=True)
    table.add_column("Check", style="heading", no_wrap=True)
    table.add_column("Detail", style="value", overflow="fold")
    for check in checks:
        table.add_row(check.status, check.name, check.detail)

    failures = [check for check in checks if check.failed]
    border = "border.error" if failures else "border.success"
    ui.console.print(ui.panel(table, title="🩺 Doctor", border=border))

    if failures:
        ui.console.print(
            Text(
                f"{len(failures)} check(s) failed — the panels above name what "
                "could not be reached.",
                style="warn",
            )
        )
    elif offline:
        ui.console.print(
            Text("Local checks passed. Drop --offline to test providers.", style="muted")
        )
    else:
        ui.console.print(Text("Everything checks out.", style="success"))
