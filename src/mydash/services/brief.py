"""Brief orchestration: compose weather, news, and stocks into one DTO.

Preferences (city, symbols, category, units, providers) come from
:class:`~mydash.services.user_config.UserConfigurationService` so the CLI
``set`` command and the brief stay in sync.
"""

import asyncio
from typing import Literal

from pydantic import BaseModel

from mydash.models.news import NewsHeadlines
from mydash.models.stocks import StockBars, StockQuotes
from mydash.models.weather import MultiDayForecast
from mydash.services.news import NewsService
from mydash.services.stocks import StocksService
from mydash.services.user_config import (
    DEFAULT_WEATHER_UNITS,
    UserConfigurationService,
)
from mydash.services.weather import WeatherService

WeatherUnits = Literal["metric", "imperial"]

__all__ = ["BriefService", "DailyBrief"]


class DailyBrief(BaseModel):
    """Aggregated snapshot for the daily brief command and Rich renderer.

    ``weather_units`` records the preset used when fetching weather so the
    renderer can show °C/°F and matching temperature thresholds.
    """

    headlines: NewsHeadlines
    stock_quotes: StockQuotes
    stock_bars: StockBars
    weather: MultiDayForecast
    city: str
    news_category: str
    symbols: list[str]
    weather_units: WeatherUnits = DEFAULT_WEATHER_UNITS


class BriefService:
    """Fetch all brief domains and return a :class:`DailyBrief` (fail-fast)."""

    async def build(
        self, config_service: UserConfigurationService | None = None
    ) -> DailyBrief:
        """Fetch weather, news, and stocks using saved user preferences.

        Domain fetches run concurrently via :func:`asyncio.gather`.

        :param config_service: Optional config instance (tests inject a temp
            path). When omitted, loads the platform user config file.
        :returns: Composed brief DTO for the renderer.
        """
        cfg_svc = config_service or UserConfigurationService()
        cfg = cfg_svc.get_configuration()

        weather, headlines, stock_pair = await asyncio.gather(
            WeatherService(
                weather_provider=cfg.provider_weather,
                geocoding_provider=cfg.provider_geocoding,
            ).fetch_forecast(cfg.coordinates, units=cfg.weather_units),
            NewsService(news_provider=cfg.provider_news).fetch_news(
                category=cfg.news_category
            ),
            StocksService(
                stock_ticker_symbols=list(cfg.stock_symbols),
                stock_provider=cfg.provider_stocks,
            ).fetch_stock_bars_and_quotes(),
        )
        stock_quotes, stock_bars = stock_pair

        return DailyBrief(
            headlines=headlines,
            stock_quotes=stock_quotes,
            stock_bars=stock_bars,
            weather=weather,
            city=cfg.city,
            news_category=cfg.news_category,
            symbols=list(cfg.stock_symbols),
            weather_units=cfg.weather_units,
        )
