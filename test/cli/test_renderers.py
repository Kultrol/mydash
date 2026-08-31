"""Tests for the panel builders.

Strategy: render each panel to a wide, colourless console and assert on the
text a reader would see. Covers the states that are easy to get wrong — a
failed domain, an empty result, partial data, and compact mode.
"""

from datetime import UTC, date, datetime, timedelta

import pytest
from rich.console import Console

from mydash.cli import ui
from mydash.cli.renderers import _common
from mydash.cli.renderers.news import headlines_panel
from mydash.cli.renderers.stocks import stocks_panel
from mydash.cli.renderers.weather import weather_panel
from mydash.models.news import HeadLine, NewsHeadlines
from mydash.models.stocks import StockBar, StockBars, StockQuote, StockQuotes
from mydash.models.weather import (
    DailySummary,
    DayForecast,
    HourForecast,
    MultiDayForecast,
)

NOW = datetime(2026, 7, 13, 14, 0, tzinfo=UTC)


@pytest.fixture
def render():
    """Render a panel to plain text, wide enough to avoid truncation."""
    console = Console(width=200, no_color=True, force_terminal=False, theme=ui.THEME)

    def _render(panel) -> str:
        with console.capture() as capture:
            console.print(panel)
        return capture.get()

    return _render


# --- markets --------------------------------------------------------------


def _quotes(*tickers, missing=None, bid=10.0, ask=10.5) -> StockQuotes:
    return StockQuotes(
        quotes=[
            StockQuote(ticker_name=t, ask_price=ask, bid_price=bid, time=NOW)
            for t in tickers
        ],
        missing=list(missing or []),
    )


def _bars(*tickers, missing=None, open_price=100.0, close=101.0) -> StockBars:
    return StockBars(
        bars=[
            StockBar(ticker_name=t, open=open_price, close=close, time=NOW)
            for t in tickers
        ],
        missing=list(missing or []),
    )


def test_markets_panel_shows_price_and_movement(render):
    output = render(stocks_panel(_quotes("SPY"), _bars("SPY"), symbols=["SPY"]))

    assert "SPY" in output
    assert "$101.00" in output
    assert "+1.00" in output
    assert "+1.00%" in output


def test_markets_panel_marks_a_fall(render):
    output = render(
        stocks_panel(
            _quotes("SPY"), _bars("SPY", open_price=100.0, close=95.0), symbols=["SPY"]
        )
    )

    assert "-5.00" in output
    assert "-5.00%" in output


def test_markets_panel_reports_missing_symbols(render):
    output = render(
        stocks_panel(
            _quotes("SPY", missing=["ZZZZ"]),
            _bars("SPY", missing=["ZZZZ"]),
            symbols=["SPY", "ZZZZ"],
        )
    )

    assert "No data for" in output
    assert "ZZZZ" in output


def test_markets_panel_hides_zero_quotes(render):
    output = render(
        stocks_panel(_quotes("SPY", bid=0.0, ask=0.0), _bars("SPY"), symbols=["SPY"])
    )

    assert "$0.00" not in output


def test_markets_panel_follows_watch_list_order(render):
    output = render(
        stocks_panel(
            _quotes("AAPL", "SPY"), _bars("AAPL", "SPY"), symbols=["SPY", "AAPL"]
        )
    )

    assert output.index("SPY") < output.index("AAPL")


def test_markets_panel_explains_a_failure(render):
    output = render(
        stocks_panel(_quotes(), _bars(), failure="Alpaca credentials are missing")
    )

    assert "Unavailable" in output
    assert "Alpaca credentials are missing" in output


def test_markets_panel_handles_no_data(render):
    output = render(stocks_panel(_quotes(), _bars(), symbols=["SPY"]))

    assert "No market data" in output


def test_markets_panel_survives_a_quote_without_a_bar(render):
    output = render(stocks_panel(_quotes("SPY"), _bars(), symbols=["SPY"]))

    assert "SPY" in output
    assert "—" in output


def test_markets_compact_drops_the_spread(render):
    full = render(stocks_panel(_quotes("SPY"), _bars("SPY"), symbols=["SPY"]))
    compact = render(
        stocks_panel(_quotes("SPY"), _bars("SPY"), symbols=["SPY"], compact=True)
    )

    assert "Bid" in full
    assert "Bid" not in compact


# --- weather --------------------------------------------------------------


def _forecast(*, summary: DailySummary | None = None) -> MultiDayForecast:
    hours = [
        HourForecast(
            time=datetime(2026, 7, 13, hour),
            temperature=25.0,
            feels_like_temperature=26.0,
            cloud_cover=10,
            wind_speed=12.0,
            chance_of_rain=70,
            amount_of_rain=0.4,
            weather_code=61,
            uv_index=5.0,
        )
        for hour in range(24)
    ]
    return MultiDayForecast(
        days=[DayForecast(date=date(2026, 7, 13), hours=hours, summary=summary)]
    )


def test_weather_panel_shows_hours_and_city(render):
    output = render(
        weather_panel(_forecast(), city="Miami", hours=3, units="metric")
    )

    assert "Miami" in output
    assert "25°C" in output
    assert "70%" in output
    assert "km/h" in output


def test_weather_panel_uses_imperial_labels(render):
    output = render(weather_panel(_forecast(), city="Miami", units="imperial"))

    assert "°F" in output
    assert "mph" in output


def test_weather_panel_subtitle_carries_the_daily_summary(render):
    summary = DailySummary(
        high=31.0,
        low=22.0,
        sunrise=datetime(2026, 7, 13, 6, 45),
        sunset=datetime(2026, 7, 13, 20, 15),
    )
    output = render(weather_panel(_forecast(summary=summary), city="Miami"))

    assert "31" in output and "22" in output
    assert "06:45" in output and "20:15" in output


def test_weather_panel_without_a_summary_shows_the_unit(render):
    output = render(weather_panel(_forecast(), city="Miami"))

    assert "°C" in output


def test_weather_panel_explains_a_failure(render):
    output = render(
        weather_panel(MultiDayForecast(days=[]), city="Miami", failure="timed out")
    )

    assert "Unavailable" in output
    assert "timed out" in output


def test_weather_panel_handles_no_hours(render):
    output = render(weather_panel(MultiDayForecast(days=[]), city="Miami"))

    assert "No forecast data" in output


def test_weather_compact_drops_feels_and_wind(render):
    compact = render(weather_panel(_forecast(), city="Miami", compact=True))

    assert "Feels" not in compact
    assert "Wind" not in compact


# --- headlines ------------------------------------------------------------


def _headlines(count: int = 3) -> NewsHeadlines:
    return NewsHeadlines(
        headlines=[
            HeadLine(
                headline=f"Headline number {index}",
                publication="Example Times",
                description=None,
                source_url=f"https://example.com/{index}",
                category="tech",
                published_time=datetime.now(UTC) - timedelta(hours=index),
            )
            for index in range(1, count + 1)
        ]
    )


def test_headlines_panel_numbers_and_lists(render):
    output = render(headlines_panel(_headlines(), category="tech"))

    assert "Headline number 1" in output
    assert "Example Times" in output
    assert "tech" in output


def test_headlines_panel_shows_relative_ages(render):
    output = render(headlines_panel(_headlines(), category="tech"))

    assert "h ago" in output


def test_headlines_panel_respects_the_limit(render):
    output = render(headlines_panel(_headlines(10), category="tech", limit=2))

    assert "Headline number 2" in output
    assert "Headline number 3" not in output
    assert "2 of 10" in output


def test_headlines_panel_explains_a_failure(render):
    output = render(
        headlines_panel(
            NewsHeadlines(headlines=[]), category="tech", failure="provider down"
        )
    )

    assert "Unavailable" in output
    assert "provider down" in output


def test_headlines_panel_handles_no_items(render):
    output = render(headlines_panel(NewsHeadlines(headlines=[]), category="tech"))

    assert "No headlines" in output


def test_headlines_compact_drops_the_source(render):
    compact = render(headlines_panel(_headlines(), category="tech", compact=True))

    assert "Example Times" not in compact


# --- formatting helpers ---------------------------------------------------


@pytest.mark.parametrize(
    "temp, units, expected",
    [(30.0, "metric", "30°C"), (5.0, "metric", "5°C"), (90.0, "imperial", "90°F")],
)
def test_temperature_formatting(temp, units, expected):
    assert _common.temperature(temp, units=units).plain == expected


@pytest.mark.parametrize("chance", [0, 30, 60, 100])
def test_rain_chance_always_reads_as_a_percentage(chance):
    assert _common.rain_chance(chance).plain == f"{chance}%"


def test_price_change_marks_direction_without_relying_on_colour():
    up, _ = _common.price_change(100.0, 110.0)
    down, _ = _common.price_change(100.0, 90.0)
    flat, _ = _common.price_change(100.0, 100.0)

    assert up.plain.startswith("▲")
    assert down.plain.startswith("▼")
    assert flat.plain.startswith("▬")


def test_price_change_without_an_open_has_no_percentage():
    _, percent = _common.price_change(0.0, 10.0)

    assert percent.plain == "—"


@pytest.mark.parametrize(
    "code, expected", [(0, "☀️"), (3, "☁️"), (95, "⛈️"), (12345, "🌡️")]
)
def test_weather_emoji_falls_back_for_unknown_codes(code, expected):
    assert _common.weather_emoji(code) == expected


def test_source_link_falls_back_without_a_url():
    assert _common.source_link("", None).plain == "Source"
