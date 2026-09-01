"""Formatting shared by the brief and the single-domain panels.

Everything here turns a domain value into styled :class:`~rich.text.Text`.
Direction and severity are always carried by a glyph as well as a colour, so
the panels stay readable without colour.
"""

from __future__ import annotations

from datetime import datetime

from rich.style import Style
from rich.text import Text

from mydash.cli import ui

# Temperature thresholds, aligned to the metric / imperial presets.
TEMP_HOT_C = 29.0
TEMP_COLD_C = 10.0
TEMP_HOT_F = 84.0
TEMP_COLD_F = 50.0

# Rain probability bands.
RAIN_WET = 60
RAIN_DRIZZLE = 30

# WMO weather codes (Open-Meteo) grouped by the cue we show for them.
_WEATHER_EMOJI: dict[int, str] = {
    0: "☀️",
    1: "🌤️",
    2: "🌤️",
    3: "☁️",
    45: "🌫️",
    48: "🌫️",
    51: "🌦️",
    53: "🌦️",
    55: "🌦️",
    56: "🌦️",
    57: "🌦️",
    61: "🌧️",
    63: "🌧️",
    65: "🌧️",
    66: "🌧️",
    67: "🌧️",
    80: "🌧️",
    81: "🌧️",
    82: "🌧️",
    71: "❄️",
    73: "❄️",
    75: "❄️",
    77: "❄️",
    85: "❄️",
    86: "❄️",
    95: "⛈️",
    96: "⛈️",
    99: "⛈️",
}


def unit_label(units: str) -> str:
    """Return the degree suffix for a unit preset."""
    return "°F" if units == "imperial" else "°C"


def speed_label(units: str) -> str:
    """Return the wind-speed suffix for a unit preset."""
    return "mph" if units == "imperial" else "km/h"


def temperature(temp: float, *, units: str = "metric") -> Text:
    """Format a temperature, styled hot / mild / cold for *units*."""
    if units == "imperial":
        hot, cold = TEMP_HOT_F, TEMP_COLD_F
    else:
        hot, cold = TEMP_HOT_C, TEMP_COLD_C

    if temp >= hot:
        style = "temp.hot"
    elif temp <= cold:
        style = "temp.cold"
    else:
        style = "temp.mild"
    return Text(f"{temp:.0f}{unit_label(units)}", style=style)


def rain_chance(chance: int) -> Text:
    """Format a rain probability, styled by how likely it is."""
    if chance >= RAIN_WET:
        style = "rain.wet"
    elif chance >= RAIN_DRIZZLE:
        style = "rain.damp"
    else:
        style = "rain.dry"
    return Text(f"{chance}%", style=style)


def weather_emoji(weather_code: int) -> str:
    """Map a WMO weather code to a short emoji cue."""
    return _WEATHER_EMOJI.get(weather_code, "🌡️")


def price_change(open_price: float, close_price: float) -> tuple[Text, Text]:
    """Return the absolute and percentage change, arrow-marked and styled."""
    delta = close_price - open_price
    if delta > 0:
        style, arrow = "money.up", "▲"
    elif delta < 0:
        style, arrow = "money.down", "▼"
    else:
        style, arrow = "money.flat", "▬"

    absolute = Text(f"{arrow} {delta:+,.2f}", style=style)
    if open_price:
        percent = Text(f"{delta / open_price * 100:+.2f}%", style=style)
    else:
        percent = Text("—", style="muted")
    return absolute, percent


def optional_money(value: float | None) -> Text:
    """Format a price, showing a dash when there is no live quote.

    Alpaca reports a bid or ask of 0 outside market hours, when nobody is
    offering. Printing "$0.00" would read as a real price.
    """
    if not value:
        return Text("—", style="muted")
    return Text(ui.money(value), style="money")


def source_link(publication: str, url: str | None) -> Text:
    """Underline a publication name and attach a terminal hyperlink."""
    label = publication or "Source"
    if url:
        return Text(label, style=Style(bold=True, underline=True, link=url))
    return Text(label, style="link")


def published(when: datetime) -> Text:
    """Format a publication time as a short relative age."""
    return Text(ui.relative_time(when), style="muted")


def missing_note(missing: list[str]) -> Text | None:
    """Return a footnote naming symbols the provider had no data for."""
    if not missing:
        return None
    note = Text()
    note.append("No data for ", style="warn")
    note.append(", ".join(missing), style="value")
    return note
