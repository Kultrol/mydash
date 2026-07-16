"""Rich layout for the daily brief (presentation only).

Three full-width panels, printed top to bottom: Markets, Weather, Headlines.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from mydash.core.services.brief import DailyBrief

if TYPE_CHECKING:
    from mydash.core.models.weather import HourForecast

HEADLINE_LIMIT = 8
WEATHER_HOURS = 6

STYLE_UP = "bold bright_green"
STYLE_DOWN = "bold bright_red"
STYLE_FLAT = "bold bright_white"
STYLE_MONEY = "bright_cyan"
STYLE_META = "bright_black"
STYLE_HEADLINE = "bold bright_white"
STYLE_SOURCE = "bold bright_blue"

BORDER_STOCKS = "bright_green"
BORDER_WEATHER = "bright_yellow"
BORDER_HEADLINES = "bright_blue"

# Temperature color thresholds (aligned to metric / imperial presets).
TEMP_HOT_C = 29.0
TEMP_COLD_C = 10.0
TEMP_HOT_F = 84.0
TEMP_COLD_F = 50.0
RAIN_WET = 60
RAIN_DRIZZLE = 30


def render_brief(console: Console, brief: DailyBrief) -> None:
    """Print Markets, Weather, and Headlines as stacked panels."""
    console.print(_stocks_panel(brief))
    console.print(_weather_panel(brief))
    console.print(_headlines_panel(brief))


def _stocks_panel(brief: DailyBrief) -> Panel:
    """Markets panel: dollar prices, direction markers, and quote times."""
    table = Table(
        expand=True,
        show_lines=False,
        pad_edge=False,
        header_style="bold bright_white",
        border_style="dim",
    )
    table.add_column("Ticker", style="bold bright_white", no_wrap=True)
    table.add_column("Bid", justify="right", no_wrap=True)
    table.add_column("Ask", justify="right", no_wrap=True)
    table.add_column("Close", justify="right", no_wrap=True)
    table.add_column("Change", justify="right", no_wrap=True)
    table.add_column("As of", justify="right", style=STYLE_META, no_wrap=True)

    bars_by_ticker = {bar.ticker_name: bar for bar in brief.stock_bars.bars}

    if not brief.stock_quotes.quotes:
        empty = Text("No market data right now", style="italic bright_white")
        return Panel(
            empty,
            title="📈 Markets",
            border_style=BORDER_STOCKS,
            title_align="left",
        )

    for quote in brief.stock_quotes.quotes:
        bar = bars_by_ticker.get(quote.ticker_name)
        as_of = _friendly_time(quote.time)

        if bar is not None:
            close_text, change_text = _close_and_change(bar.open, bar.close)
        else:
            close_text = Text("—", style=STYLE_META)
            change_text = Text("—", style=STYLE_META)

        table.add_row(
            quote.ticker_name,
            Text(_money(quote.bid_price), style=STYLE_MONEY),
            Text(_money(quote.ask_price), style=STYLE_MONEY),
            close_text,
            change_text,
            as_of,
        )

    symbols = ", ".join(brief.symbols)
    return Panel(
        table,
        title=f"📈 Markets · {symbols}",
        border_style=BORDER_STOCKS,
        title_align="left",
    )


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _close_and_change(open_price: float, close_price: float) -> tuple[Text, Text]:
    """Direction uses color and an arrow so meaning is not color-only."""
    delta = close_price - open_price
    if delta > 0:
        style, arrow = STYLE_UP, "↑"
    elif delta < 0:
        style, arrow = STYLE_DOWN, "↓"
    else:
        style, arrow = STYLE_FLAT, "→"

    close_text = Text(f"{arrow} {_money(close_price)}", style=style)
    change_text = Text(f"{delta:+.2f}", style=style)
    return close_text, change_text


def _friendly_time(when: datetime) -> str:
    if when.tzinfo is not None:
        when = when.astimezone()
    return when.strftime("%I:%M %p").lstrip("0")


def _weather_panel(brief: DailyBrief) -> Panel:
    """Next few hours of forecast for the brief city (unit-aware labels)."""
    hours = _next_hours(brief, n=WEATHER_HOURS)

    table = Table(
        expand=True,
        show_lines=False,
        pad_edge=False,
        header_style="bold bright_white",
    )
    table.add_column("When", style="bold", no_wrap=True)
    table.add_column("", width=2, justify="center")
    table.add_column("Temp", justify="right")
    table.add_column("Feels", justify="right")
    table.add_column("Rain", justify="right")

    units = brief.weather_units

    if not hours:
        body: Table | Text = Text(
            "No forecast data right now", style="italic bright_white"
        )
    else:
        for month, day, hour in hours:
            table.add_row(
                f"{month:02d}/{day:02d} {hour.hour:02d}:00",
                _weather_emoji(hour.weather_code),
                _temp_text(hour.temperature, units=units),
                _temp_text(hour.feels_like_temperature, units=units),
                _rain_text(hour.chance_of_rain),
            )
        body = table

    unit_label = "°F" if units == "imperial" else "°C"
    return Panel(
        body,
        title=f"🌤️  Weather · {brief.city} · {unit_label}",
        border_style=BORDER_WEATHER,
        title_align="left",
    )


def _next_hours(
    brief: DailyBrief, n: int
) -> list[tuple[int, int, HourForecast]]:
    """Return the next *n* hourly slots from now, or the first *n* as fallback."""
    flat: list[tuple[int, int, HourForecast]] = []
    for day in brief.weather.days:
        for hour in day.hours:
            flat.append((day.month, day.day, hour))

    if not flat:
        return []

    now = datetime.now()
    upcoming = [
        (m, d, h)
        for m, d, h in flat
        if (m, d, h.hour) >= (now.month, now.day, now.hour)
    ]
    return upcoming[:n] if upcoming else flat[:n]


def _temp_text(temp: float, units: str = "metric") -> Text:
    """Format temperature with °C/°F and hot/cold styling for *units*."""
    if units == "imperial":
        hot, cold, suffix = TEMP_HOT_F, TEMP_COLD_F, "°F"
    else:
        hot, cold, suffix = TEMP_HOT_C, TEMP_COLD_C, "°C"

    if temp >= hot:
        style = "bold bright_yellow"
    elif temp <= cold:
        style = "bold bright_cyan"
    else:
        style = "bright_white"
    return Text(f"{temp:.1f}{suffix}", style=style)


def _rain_text(chance: int) -> Text:
    if chance >= RAIN_WET:
        style = "bold bright_magenta"
    elif chance >= RAIN_DRIZZLE:
        style = "bold bright_yellow"
    else:
        style = "bright_green"
    return Text(f"{chance}%", style=style)


def _weather_emoji(weather_code: int) -> str:
    """Map WMO weather codes (Open-Meteo) to a short emoji cue."""
    if weather_code == 0:
        return "☀️"
    if weather_code in (1, 2):
        return "🌤️"
    if weather_code == 3:
        return "☁️"
    if weather_code in (45, 48):
        return "🌫️"
    if weather_code in (51, 53, 55, 56, 57):
        return "🌦️"
    if weather_code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "🌧️"
    if weather_code in (71, 73, 75, 77, 85, 86):
        return "❄️"
    if weather_code in (95, 96, 99):
        return "⛈️"
    return "🌡️"


def _headlines_panel(brief: DailyBrief) -> Panel:
    """Headlines panel; source labels link to the article URL when possible."""
    table = Table(
        expand=True,
        show_lines=False,
        pad_edge=False,
        header_style="bold bright_white",
        collapse_padding=True,
    )
    table.add_column("#", style=STYLE_META, width=3, justify="right")
    table.add_column("Headline", style=STYLE_HEADLINE, overflow="ellipsis", ratio=3)
    table.add_column("Source", overflow="ellipsis", ratio=1)
    table.add_column("Published", style=STYLE_META, no_wrap=True)

    items = brief.headlines.headlines[:HEADLINE_LIMIT]

    if not items:
        body: Table | Text = Text(
            "No headlines right now", style="italic bright_white"
        )
    else:
        for index, item in enumerate(items, start=1):
            table.add_row(
                str(index),
                item.headline,
                _source_link(item.publication, item.source_url),
                _friendly_published(item.published_time),
            )
        body = table

    return Panel(
        body,
        title=f"📰 Headlines · {brief.news_category}",
        border_style=BORDER_HEADLINES,
        title_align="left",
    )


def _source_link(publication: str, url: str | None) -> Text:
    """Underline the publication name and attach a terminal hyperlink."""
    label = publication or "Source"
    if url:
        style = Style(color="bright_blue", bold=True, underline=True, link=url)
        return Text(label, style=style)
    return Text(label, style=STYLE_SOURCE)


def _friendly_published(when: datetime) -> str:
    if when.tzinfo is not None:
        when = when.astimezone()
    return when.strftime("%b %d · %H:%M")
