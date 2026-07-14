"""Brief orchestration: compose weather, news, and stocks into one DTO."""

from typing import Literal

from pydantic import BaseModel

from mydash.models.news import NewsHeadlines
from mydash.models.stocks import StockBars, StockQuotes
from mydash.models.weather import MultiDayForecast
from mydash.services.news import NewsService
from mydash.services.stocks import StocksService
from mydash.services.user_config import (
    DEFAULT_CITY,
    DEFAULT_NEWS_CATEGORY,
    DEFAULT_SYMBOLS,
    DEFAULT_WEATHER_UNITS,
    UserConfigurationService,
)
from mydash.services.weather import WeatherService

WeatherUnits = Literal["metric", "imperial"]

# Re-export defaults for callers/tests that previously imported from brief.
__all__ = [
    "DEFAULT_CITY",
    "DEFAULT_NEWS_CATEGORY",
    "DEFAULT_SYMBOLS",
    "DEFAULT_WEATHER_UNITS",
    "BriefService",
    "DailyBrief",
]


class DailyBrief(BaseModel):
    """Aggregated snapshot for the daily brief command."""

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

    def build(
        self, config_service: UserConfigurationService | None = None
    ) -> DailyBrief:
        """Fetch weather, news, and stocks; return one composed brief."""
        cfg_svc = config_service or UserConfigurationService()
        cfg = cfg_svc.get_configuration()

        weather = WeatherService(
            weather_provider=cfg.provider_weather,
            geocoding_provider=cfg.provider_geocoding,
        ).fetch_today_weather_forecast(city=cfg.city, units=cfg.weather_units)
        headlines = NewsService(news_provider=cfg.provider_news).fetch_news(
            category=cfg.news_category
        )
        stock_quotes, stock_bars = StocksService(
            stock_ticker_symbols=list(cfg.stock_symbols),
            stock_provider=cfg.provider_stocks,
        ).fetch_stock_bars_and_quotes()

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
