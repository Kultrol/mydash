"""Brief orchestration: compose weather, news, and stocks into one DTO.

Preferences (city, coordinates, symbols, category, units, providers) come from
:class:`~mydash.services.user_config.UserConfigurationService` so the CLI
``set`` command and the brief stay in sync.

Domains are fetched concurrently and independently: a provider that is down,
rate-limited, or missing credentials costs you *its* panel and nothing else.
The failure travels back in :attr:`DailyBrief.errors` so the renderer can say
what went wrong where the data would have been.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from mydash.client.http_api.http_api import HttpApiClient
from mydash.models.news import NewsHeadlines
from mydash.models.stocks import StockBars, StockQuotes
from mydash.models.weather import MultiDayForecast
from mydash.services.news import NewsService
from mydash.services.stocks import StocksService
from mydash.services.user_config import (
    DEFAULT_WEATHER_UNITS,
    UserConfig,
    UserConfigurationService,
)
from mydash.services.weather import WeatherService
from mydash.storage.cache import ResponseCache

WeatherUnits = Literal["metric", "imperial"]

#: Panels a brief can contain, in display order.
BRIEF_DOMAINS: tuple[str, ...] = ("stocks", "weather", "news")

#: Headlines fetched for a brief; the renderer shows a subset of these.
BRIEF_HEADLINE_LIMIT = 12

__all__ = ["BRIEF_DOMAINS", "BriefService", "DailyBrief"]


class DailyBrief(BaseModel):
    """Aggregated snapshot for the daily brief command and Rich renderer.

    ``weather_units`` records the preset used when fetching weather so the
    renderer can show °C/°F and matching temperature thresholds. ``domains``
    lists the panels that were asked for; ``errors`` maps a domain to why it
    has no data.
    """

    headlines: NewsHeadlines
    stock_quotes: StockQuotes
    stock_bars: StockBars
    weather: MultiDayForecast
    city: str
    news_category: str
    symbols: list[str]
    weather_units: WeatherUnits = DEFAULT_WEATHER_UNITS
    domains: list[str] = Field(default_factory=lambda: list(BRIEF_DOMAINS))
    errors: dict[str, str] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)

    def failed(self, domain: str) -> str | None:
        """Return why *domain* has no data, or ``None`` if it is fine."""
        return self.errors.get(domain)

    @property
    def is_complete(self) -> bool:
        """True when every requested domain returned data."""
        return not self.errors


class BriefService:
    """Fetch every brief domain concurrently and tolerate partial failure."""

    async def build(
        self,
        config_service: UserConfigurationService | None = None,
        *,
        refresh: bool = False,
        domains: Iterable[str] | None = None,
    ) -> DailyBrief:
        """Fetch weather, news, and stocks using saved user preferences.

        :param config_service: Optional config instance (tests inject a temp
            database). When omitted, opens the platform user database.
        :param refresh: Bypass cached responses and fetch live data.
        :param domains: Subset of :data:`BRIEF_DOMAINS` to fetch; defaults to
            all of them.
        :returns: Composed brief DTO for the renderer, including any per-domain
            failures.
        """
        cfg_svc = config_service or UserConfigurationService()
        cfg = cfg_svc.get_configuration()
        wanted = _requested_domains(domains)

        cache = ResponseCache(cfg_svc.database)
        # One client for the whole brief: the Alpaca quote and bar calls share
        # a connection, and every provider shares the cache.
        async with HttpApiClient(cache=cache, refresh=refresh) as http:
            results = await asyncio.gather(
                self._weather(cfg, http) if "weather" in wanted else _none(),
                self._news(cfg, http) if "news" in wanted else _none(),
                self._stocks(cfg, http) if "stocks" in wanted else _none(),
                return_exceptions=True,
            )

        weather_result, news_result, stocks_result = results
        errors: dict[str, str] = {}

        weather = _unwrap(weather_result, "weather", errors) or MultiDayForecast(days=[])
        headlines = _unwrap(news_result, "news", errors) or NewsHeadlines(headlines=[])
        stock_pair = _unwrap(stocks_result, "stocks", errors)
        stock_quotes, stock_bars = stock_pair or (
            StockQuotes(quotes=[]),
            StockBars(bars=[]),
        )

        return DailyBrief(
            headlines=headlines,
            stock_quotes=stock_quotes,
            stock_bars=stock_bars,
            weather=weather,
            city=cfg.city,
            news_category=cfg.news_category,
            symbols=list(cfg.stock_symbols),
            weather_units=cfg.weather_units,
            domains=[domain for domain in BRIEF_DOMAINS if domain in wanted],
            errors=errors,
        )

    @staticmethod
    async def _weather(cfg: UserConfig, http: HttpApiClient) -> MultiDayForecast:
        """Forecast for the coordinates already stored with the city."""
        return await WeatherService(
            weather_provider=cfg.provider_weather,
            geocoding_provider=cfg.provider_geocoding,
            http_client=http,
        ).fetch_forecast(cfg.coordinates, units=cfg.weather_units)

    @staticmethod
    async def _news(cfg: UserConfig, http: HttpApiClient) -> NewsHeadlines:
        return await NewsService(
            news_provider=cfg.provider_news, http_client=http
        ).fetch_news(category=cfg.news_category, limit=BRIEF_HEADLINE_LIMIT)

    @staticmethod
    async def _stocks(
        cfg: UserConfig, http: HttpApiClient
    ) -> tuple[StockQuotes, StockBars]:
        return await StocksService(
            stock_ticker_symbols=list(cfg.stock_symbols),
            stock_provider=cfg.provider_stocks,
            http_client=http,
        ).fetch_stock_bars_and_quotes()


def _requested_domains(domains: Iterable[str] | None) -> set[str]:
    """Normalize a domain selection, defaulting to everything.

    :raises ValueError: If a name is not a known brief domain.
    """
    if domains is None:
        return set(BRIEF_DOMAINS)
    wanted = {str(domain).strip().lower() for domain in domains if str(domain).strip()}
    unknown = wanted - set(BRIEF_DOMAINS)
    if unknown:
        raise ValueError(
            f"unknown brief domain(s) {sorted(unknown)}; expected any of "
            f"{list(BRIEF_DOMAINS)}"
        )
    return wanted or set(BRIEF_DOMAINS)


async def _none() -> None:
    """Placeholder coroutine for a domain that was not requested."""
    return None


def _unwrap(result: object, domain: str, errors: dict[str, str]):
    """Return a gathered result, recording an exception under *domain*."""
    if isinstance(result, BaseException):
        errors[domain] = str(result) or result.__class__.__name__
        return None
    return result
