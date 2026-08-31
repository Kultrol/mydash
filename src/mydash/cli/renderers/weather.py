"""Weather panel: the next few hours, with today's range in the subtitle."""

from __future__ import annotations

from rich.panel import Panel

from mydash.cli import ui
from mydash.cli.renderers import _common
from mydash.models.weather import DailySummary, MultiDayForecast

DEFAULT_HOURS = 6


def weather_panel(
    forecast: MultiDayForecast,
    *,
    city: str,
    units: str = "metric",
    hours: int = DEFAULT_HOURS,
    failure: str | None = None,
    compact: bool = False,
) -> Panel:
    """Build the weather panel.

    :param forecast: Hourly forecast, already in the location's timezone.
    :param city: Place name for the panel title.
    :param units: ``metric`` or ``imperial``, for labels and thresholds.
    :param hours: How many upcoming hours to show.
    :param failure: Why the forecast is missing, if it is.
    :param compact: Drop the "feels like" and wind columns.
    """
    title = f"🌤️  Weather · {city}"

    if failure is not None:
        return ui.panel(
            ui.unavailable(failure), title=title, border="border.weather"
        )

    upcoming = forecast.upcoming_hours(hours)
    if not upcoming:
        return ui.panel(
            ui.empty("No forecast data right now"),
            title=title,
            border="border.weather",
        )

    table = ui.data_table()
    table.add_column("When", style="heading", no_wrap=True)
    table.add_column("", width=2, justify="center")
    table.add_column("Temp", justify="right", no_wrap=True)
    if not compact:
        table.add_column("Feels", justify="right", no_wrap=True)
    table.add_column("Rain", justify="right", no_wrap=True)
    if not compact:
        table.add_column("Wind", justify="right", style="muted", no_wrap=True)

    for hour in upcoming:
        row = [
            hour.time.strftime("%H:00"),
            _common.weather_emoji(hour.weather_code),
            _common.temperature(hour.temperature, units=units),
        ]
        if not compact:
            row.append(_common.temperature(hour.feels_like_temperature, units=units))
        row.append(_common.rain_chance(hour.chance_of_rain))
        if not compact:
            row.append(f"{hour.wind_speed:.0f} {_common.speed_label(units)}")
        table.add_row(*row)

    return ui.panel(
        table,
        title=title,
        border="border.weather",
        subtitle=_subtitle(forecast, units),
    )


def _subtitle(forecast: MultiDayForecast, units: str) -> str:
    """Today's high/low and daylight, when the provider gave us a summary."""
    today = forecast.today
    summary: DailySummary | None = today.summary if today else None
    if summary is None:
        return _common.unit_label(units)

    parts: list[str] = []
    if summary.high is not None and summary.low is not None:
        suffix = _common.unit_label(units)
        parts.append(f"↑{summary.high:.0f}{suffix} ↓{summary.low:.0f}{suffix}")
    if summary.sunrise and summary.sunset:
        parts.append(
            f"☀ {summary.sunrise.strftime('%H:%M')} – {summary.sunset.strftime('%H:%M')}"
        )
    return "  ·  ".join(parts) if parts else _common.unit_label(units)
