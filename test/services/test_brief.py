"""Tests for BriefService orchestration.

Strategy: mock client factories so no HTTP runs. Assert the service wires each
domain pipeline and returns a DailyBrief with the expected pieces.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from mydash.models.geocoding import Coordinates
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
def mock_clients(mocker):
    """Patch all four factories used by BriefService."""
    coords = Coordinates(latitude=25.76, longitude=-80.19)

    geo = MagicMock()
    geo.get_coordinates.return_value = coords

    weather = MagicMock()
    weather.get_weather_forecast.return_value = _sample_weather()

    news = MagicMock()
    news.get_news_headlines.return_value = _sample_headlines()

    stocks = MagicMock()
    stocks.get_current_stock_quotes.return_value = _sample_quotes()
    stocks.get_current_stock_bars.return_value = _sample_bars()

    mocker.patch(
        "mydash.services.brief.get_geocoding_client", return_value=geo
    )
    mocker.patch(
        "mydash.services.brief.get_weather_client", return_value=weather
    )
    mocker.patch("mydash.services.brief.get_news_client", return_value=news)
    mocker.patch(
        "mydash.services.brief.get_stock_client", return_value=stocks
    )

    return {
        "geo": geo,
        "weather": weather,
        "news": news,
        "stocks": stocks,
        "coords": coords,
    }


def test_build_returns_daily_brief(mock_clients):
    result = BriefService().build()

    assert isinstance(result, DailyBrief)
    assert result.city == DEFAULT_CITY
    assert result.news_category == DEFAULT_NEWS_CATEGORY
    assert result.symbols == DEFAULT_SYMBOLS
    assert result.weather == _sample_weather()
    assert result.headlines == _sample_headlines()
    assert result.stock_quotes == _sample_quotes()
    assert result.stock_bars == _sample_bars()


def test_build_runs_each_domain_pipeline(mock_clients):
    BriefService().build()

    geo = mock_clients["geo"]
    weather = mock_clients["weather"]
    news = mock_clients["news"]
    stocks = mock_clients["stocks"]
    coords = mock_clients["coords"]

    geo.set_coordinates.assert_called_once_with(DEFAULT_CITY)
    geo.get_coordinates.assert_called_once()

    weather.set_coordinates.assert_called_once_with(coords)
    weather.set_weather_forecast.assert_called_once_with(
        forecast_length=1, backwardcast_length=1
    )
    weather.get_weather_forecast.assert_called_once()

    news.set_news_headlines.assert_called_once_with(
        category=DEFAULT_NEWS_CATEGORY
    )
    news.get_news_headlines.assert_called_once()

    stocks.set_current_stock_quotes.assert_called_once_with(
        symbols=DEFAULT_SYMBOLS
    )
    stocks.get_current_stock_quotes.assert_called_once()
    stocks.set_current_stock_bars.assert_called_once_with(
        symbols=DEFAULT_SYMBOLS
    )
    stocks.get_current_stock_bars.assert_called_once()
