"""Tests for BriefService orchestration.

Strategy: mock domain services and use a tmp_path config database so no HTTP
runs. Assert the service wires preferences into each domain, returns a
DailyBrief, and survives one domain failing.
"""

import asyncio
from datetime import UTC, date, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from mydash.models.news import HeadLine, NewsHeadlines
from mydash.models.stocks import StockBar, StockBars, StockQuote, StockQuotes
from mydash.models.weather import DayForecast, HourForecast, MultiDayForecast
from mydash.services.brief import BRIEF_DOMAINS, BriefService, DailyBrief
from mydash.services.user_config import (
    DEFAULT_CITY,
    DEFAULT_NEWS_CATEGORY,
    DEFAULT_SYMBOLS,
    UserConfig,
    UserConfigurationService,
)


def _sample_weather() -> MultiDayForecast:
    return MultiDayForecast(
        days=[
            DayForecast(
                date=date(2026, 7, 13),
                hours=[
                    HourForecast(
                        time=datetime(2026, 7, 13, 12),
                        temperature=25.0,
                        feels_like_temperature=26.0,
                        cloud_cover=10,
                        wind_speed=2.0,
                        chance_of_rain=0,
                        amount_of_rain=0.0,
                        weather_code=0,
                        uv_index=5.0,
                    )
                ],
            )
        ],
        timezone="America/New_York",
    )


def _sample_headlines() -> NewsHeadlines:
    return NewsHeadlines(
        headlines=[
            HeadLine(
                headline="Service headline",
                publication="Test",
                description=None,
                source_url="https://example.com",
                category="tech",
                published_time=datetime(2026, 7, 13, 12, 0, tzinfo=UTC),
            )
        ]
    )


def _sample_quotes() -> StockQuotes:
    return StockQuotes(
        quotes=[
            StockQuote(
                ticker_name="SPY",
                ask_price=1.0,
                bid_price=1.0,
                time=datetime(2026, 7, 13, 14, 0, tzinfo=UTC),
            )
        ]
    )


def _sample_bars() -> StockBars:
    return StockBars(
        bars=[
            StockBar(
                ticker_name="SPY",
                open=1.0,
                close=1.0,
                time=datetime(2026, 7, 13, 14, 0, tzinfo=UTC),
            )
        ]
    )


@pytest.fixture
def config_service(tmp_path: Path):
    svc = UserConfigurationService(db_path=tmp_path / "mydash.db")
    yield svc
    svc.close()


@pytest.fixture
def domains(mocker):
    """Patch all three domain services and hand back the mocks."""
    weather_svc = MagicMock()
    weather_svc.fetch_forecast = AsyncMock(return_value=_sample_weather())
    news_svc = MagicMock()
    news_svc.fetch_news = AsyncMock(return_value=_sample_headlines())
    stocks_svc = MagicMock()
    stocks_svc.fetch_stock_bars_and_quotes = AsyncMock(
        return_value=(_sample_quotes(), _sample_bars())
    )

    return {
        "weather": weather_svc,
        "news": news_svc,
        "stocks": stocks_svc,
        "weather_cls": mocker.patch(
            "mydash.services.brief.WeatherService", return_value=weather_svc
        ),
        "news_cls": mocker.patch(
            "mydash.services.brief.NewsService", return_value=news_svc
        ),
        "stocks_cls": mocker.patch(
            "mydash.services.brief.StocksService", return_value=stocks_svc
        ),
    }


def _build(config_service, **kwargs) -> DailyBrief:
    return asyncio.run(BriefService().build(config_service=config_service, **kwargs))


# --- happy path -----------------------------------------------------------


def test_build_returns_daily_brief(config_service, domains):
    result = _build(config_service)

    assert isinstance(result, DailyBrief)
    assert result.city == DEFAULT_CITY
    assert result.news_category == DEFAULT_NEWS_CATEGORY
    assert result.symbols == DEFAULT_SYMBOLS
    assert result.weather_units == "metric"
    assert result.weather == _sample_weather()
    assert result.headlines == _sample_headlines()
    assert result.stock_quotes == _sample_quotes()
    assert result.stock_bars == _sample_bars()
    assert result.errors == {}
    assert result.is_complete
    assert result.domains == list(BRIEF_DOMAINS)


def test_build_uses_config_preferences(tmp_path: Path, domains):
    with UserConfigurationService(db_path=tmp_path / "mydash.db") as svc:
        svc.set_configuration(
            UserConfig(
                city="Austin",
                news_category="politics",
                stock_symbols=["TSLA", "NVDA"],
                weather_units="imperial",
            )
        )

        result = _build(svc)

        weather_kwargs = domains["weather_cls"].call_args.kwargs
        assert weather_kwargs["weather_provider"] == "open-meteo"
        assert weather_kwargs["geocoding_provider"] == "open-meteo"
        domains["weather"].fetch_forecast.assert_awaited_once_with(
            svc.get_coordinates(), units="imperial"
        )

        assert domains["news_cls"].call_args.kwargs["news_provider"] == "noozra"
        assert domains["news"].fetch_news.await_args.kwargs["category"] == "politics"

        stocks_kwargs = domains["stocks_cls"].call_args.kwargs
        assert stocks_kwargs["stock_ticker_symbols"] == ["TSLA", "NVDA"]
        assert stocks_kwargs["stock_provider"] == "alpaca"
        domains["stocks"].fetch_stock_bars_and_quotes.assert_awaited_once()

    assert result.city == "Austin"
    assert result.news_category == "politics"
    assert result.symbols == ["TSLA", "NVDA"]
    assert result.weather_units == "imperial"


def test_every_domain_shares_one_http_client(config_service, domains):
    _build(config_service)

    clients = {
        id(domains[f"{name}_cls"].call_args.kwargs["http_client"])
        for name in ("weather", "news", "stocks")
    }
    assert len(clients) == 1


# --- partial failure ------------------------------------------------------


def test_one_failing_domain_does_not_sink_the_brief(config_service, domains):
    domains["stocks"].fetch_stock_bars_and_quotes.side_effect = RuntimeError(
        "Alpaca credentials are missing"
    )

    result = _build(config_service)

    assert result.failed("stocks") == "Alpaca credentials are missing"
    assert result.stock_quotes.quotes == []
    assert not result.is_complete
    # The other panels still have their data.
    assert result.weather == _sample_weather()
    assert result.headlines == _sample_headlines()
    assert result.failed("weather") is None


def test_every_domain_failing_still_returns_a_brief(config_service, domains):
    domains["weather"].fetch_forecast.side_effect = RuntimeError("no weather")
    domains["news"].fetch_news.side_effect = RuntimeError("no news")
    domains["stocks"].fetch_stock_bars_and_quotes.side_effect = RuntimeError(
        "no stocks"
    )

    result = _build(config_service)

    assert set(result.errors) == set(BRIEF_DOMAINS)
    assert result.weather.days == []
    assert result.headlines.headlines == []
    assert result.city == DEFAULT_CITY


def test_error_without_a_message_still_names_the_failure(config_service, domains):
    domains["news"].fetch_news.side_effect = TimeoutError()

    assert _build(config_service).failed("news") == "TimeoutError"


# --- domain selection -----------------------------------------------------


def test_only_requested_domains_are_fetched(config_service, domains):
    result = _build(config_service, domains=["weather"])

    assert result.domains == ["weather"]
    domains["weather"].fetch_forecast.assert_awaited_once()
    domains["news"].fetch_news.assert_not_awaited()
    domains["stocks"].fetch_stock_bars_and_quotes.assert_not_awaited()


def test_requested_domains_keep_display_order(config_service, domains):
    result = _build(config_service, domains=["news", "stocks"])

    assert result.domains == ["stocks", "news"]


def test_domain_names_are_normalized(config_service, domains):
    assert _build(config_service, domains=[" Weather "]).domains == ["weather"]


def test_unknown_domain_is_rejected(config_service, domains):
    with pytest.raises(ValueError, match="unknown brief domain"):
        _build(config_service, domains=["horoscope"])


def test_empty_domain_selection_falls_back_to_everything(config_service, domains):
    assert _build(config_service, domains=[]).domains == list(BRIEF_DOMAINS)
