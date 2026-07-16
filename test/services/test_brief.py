"""Tests for BriefService orchestration.

Strategy: mock domain services and config so no HTTP runs. Assert the service
wires preferences into each domain and returns a DailyBrief.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from mydash.models.news import HeadLine, NewsHeadlines
from mydash.models.stocks import StockBar, StockBars, StockQuote, StockQuotes
from mydash.models.weather import DayForecast, HourForecast, MultiDayForecast
from mydash.services.brief import (
    DEFAULT_CITY,
    DEFAULT_NEWS_CATEGORY,
    DEFAULT_SYMBOLS,
    BriefService,
    DailyBrief,
)
from mydash.services.user_config import UserConfig, UserConfigurationService


def _sample_weather() -> MultiDayForecast:
    return MultiDayForecast(
        days=[
            DayForecast(
                month=7,
                day=13,
                hours=[
                    HourForecast(
                        hour=12,
                        temperature=30.0,
                        feels_like_temperature=32.0,
                        cloud_cover=20,
                        wind_speed=5.0,
                        chance_of_rain=10,
                        amount_of_rain=0.0,
                        weather_code=0,
                        uv_index=6.0,
                    )
                ],
            )
        ]
    )


def _sample_headlines() -> NewsHeadlines:
    return NewsHeadlines(
        headlines=[
            HeadLine(
                headline="Sample story",
                publication="Test Press",
                description="A test",
                source_url="https://example.com/story",
                category="politics",
                published_time=datetime(2026, 7, 13, 12, 0, tzinfo=timezone.utc),
            )
        ]
    )


def _sample_quotes() -> StockQuotes:
    return StockQuotes(
        quotes=[
            StockQuote(
                ticker_name="SPY",
                ask_price=501.0,
                bid_price=500.0,
                time=datetime(2026, 7, 13, 14, 0, tzinfo=timezone.utc),
            )
        ]
    )


def _sample_bars() -> StockBars:
    return StockBars(
        bars=[
            StockBar(
                ticker_name="SPY",
                open=499.0,
                close=500.5,
                time=datetime(2026, 7, 13, 14, 0, tzinfo=timezone.utc),
            )
        ]
    )


@pytest.fixture
def config_service(tmp_path: Path) -> UserConfigurationService:
    return UserConfigurationService(config_path=tmp_path / "config.json")


def test_build_returns_daily_brief(config_service, mocker):
    weather_svc = MagicMock()
    weather_svc.fetch_today_weather_forecast = AsyncMock(
        return_value=_sample_weather()
    )
    news_svc = MagicMock()
    news_svc.fetch_news = AsyncMock(return_value=_sample_headlines())
    stocks_svc = MagicMock()
    stocks_svc.fetch_stock_bars_and_quotes = AsyncMock(
        return_value=(_sample_quotes(), _sample_bars())
    )

    mocker.patch(
        "mydash.services.brief.WeatherService", return_value=weather_svc
    )
    mocker.patch("mydash.services.brief.NewsService", return_value=news_svc)
    mocker.patch(
        "mydash.services.brief.StocksService", return_value=stocks_svc
    )

    result = asyncio.run(BriefService().build(config_service=config_service))

    assert isinstance(result, DailyBrief)
    assert result.city == DEFAULT_CITY
    assert result.news_category == DEFAULT_NEWS_CATEGORY
    assert result.symbols == DEFAULT_SYMBOLS
    assert result.weather_units == "metric"
    assert result.weather == _sample_weather()
    assert result.headlines == _sample_headlines()
    assert result.stock_quotes == _sample_quotes()
    assert result.stock_bars == _sample_bars()


def test_build_uses_config_preferences(tmp_path: Path, mocker):
    path = tmp_path / "config.json"
    svc = UserConfigurationService(config_path=path)
    svc.set_configuration(
        UserConfig(
            city="Austin",
            news_category="politics",
            stock_symbols=["TSLA", "NVDA"],
            weather_units="imperial",
            provider_weather="open-meteo",
            provider_geocoding="open-meteo",
            provider_news="noozra",
            provider_stocks="alpaca",
        )
    )

    weather_svc = MagicMock()
    weather_svc.fetch_today_weather_forecast = AsyncMock(
        return_value=_sample_weather()
    )
    news_svc = MagicMock()
    news_svc.fetch_news = AsyncMock(return_value=_sample_headlines())
    stocks_svc = MagicMock()
    stocks_svc.fetch_stock_bars_and_quotes = AsyncMock(
        return_value=(_sample_quotes(), _sample_bars())
    )

    weather_cls = mocker.patch(
        "mydash.services.brief.WeatherService", return_value=weather_svc
    )
    news_cls = mocker.patch(
        "mydash.services.brief.NewsService", return_value=news_svc
    )
    stocks_cls = mocker.patch(
        "mydash.services.brief.StocksService", return_value=stocks_svc
    )

    result = asyncio.run(BriefService().build(config_service=svc))

    weather_cls.assert_called_once_with(
        weather_provider="open-meteo", geocoding_provider="open-meteo"
    )
    weather_svc.fetch_today_weather_forecast.assert_awaited_once_with(
        city="Austin", units="imperial"
    )
    news_cls.assert_called_once_with(news_provider="noozra")
    news_svc.fetch_news.assert_awaited_once_with(category="politics")
    stocks_cls.assert_called_once_with(
        stock_ticker_symbols=["TSLA", "NVDA"], stock_provider="alpaca"
    )
    stocks_svc.fetch_stock_bars_and_quotes.assert_awaited_once()

    assert result.city == "Austin"
    assert result.news_category == "politics"
    assert result.symbols == ["TSLA", "NVDA"]
    assert result.weather_units == "imperial"
