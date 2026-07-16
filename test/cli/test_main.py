"""Tests for mydash.cli.main.

Strategy: CliRunner for command smoke; mock services (not HTTP) for brief.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from typer.testing import CliRunner

from mydash.cli.main import app
from mydash.models.news import HeadLine, NewsHeadlines
from mydash.models.stocks import StockBar, StockBars, StockQuote, StockQuotes
from mydash.models.weather import DayForecast, HourForecast, MultiDayForecast
from mydash.services.brief import DailyBrief

runner = CliRunner()


def _sample_brief() -> DailyBrief:
    return DailyBrief(
        headlines=NewsHeadlines(
            headlines=[
                HeadLine(
                    headline="CLI smoke headline",
                    publication="Test",
                    description=None,
                    source_url="https://example.com",
                    category="politics",
                    published_time=datetime(
                        2026, 7, 13, 12, 0, tzinfo=timezone.utc
                    ),
                )
            ]
        ),
        stock_quotes=StockQuotes(
            quotes=[
                StockQuote(
                    ticker_name="SPY",
                    ask_price=1.0,
                    bid_price=1.0,
                    time=datetime(2026, 7, 13, 14, 0, tzinfo=timezone.utc),
                )
            ]
        ),
        stock_bars=StockBars(
            bars=[
                StockBar(
                    ticker_name="SPY",
                    open=1.0,
                    close=1.0,
                    time=datetime(2026, 7, 13, 14, 0, tzinfo=timezone.utc),
                )
            ]
        ),
        weather=MultiDayForecast(
            days=[
                DayForecast(
                    month=7,
                    day=13,
                    hours=[
                        HourForecast(
                            hour=12,
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
            ]
        ),
        city="Miami",
        news_category="politics",
        symbols=["SPY", "AAPL", "MSFT"],
        weather_units="metric",
    )


def test_brief_command_uses_service_and_renderer(mocker):
    """brief should call BriefService.build and render_brief; no live HTTP."""
    sample = _sample_brief()
    mock_service = MagicMock()
    mock_service.build = AsyncMock(return_value=sample)

    mocker.patch("mydash.cli.main.BriefService", return_value=mock_service)
    mock_render = mocker.patch("mydash.cli.main.render_brief")

    result = runner.invoke(app, ["brief"])

    assert result.exit_code == 0, result.output
    mock_service.build.assert_awaited_once_with()
    mock_render.assert_called_once()
    args, _kwargs = mock_render.call_args
    assert args[1] is sample
