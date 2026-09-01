"""Pydantic models for weather forecast data.

Times are local to the *forecast location*, not to the machine running mydash —
providers are asked for the location's own timezone, so "the next six hours"
means the next six hours there.

Field names map to Open-Meteo hourly parameters requested in ``OpenMeteoClient``:
    temperature_2m, apparent_temperature, precipitation_probability,
    precipitation, weather_code, cloud_cover, wind_speed_10m, uv_index
"""

from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel


class HourForecast(BaseModel):
    """Single-hour weather snapshot within a day."""

    time: datetime.datetime
    temperature: float
    feels_like_temperature: float
    cloud_cover: int
    wind_speed: float
    chance_of_rain: int
    amount_of_rain: float
    weather_code: int
    uv_index: float

    @property
    def hour(self) -> int:
        """Hour of the day, local to the forecast location."""
        return self.time.hour


class DailySummary(BaseModel):
    """Whole-day figures that no single hour carries."""

    high: float | None = None
    low: float | None = None
    sunrise: datetime.datetime | None = None
    sunset: datetime.datetime | None = None
    max_chance_of_rain: int | None = None


class DayForecast(BaseModel):
    """All hourly forecasts grouped for one calendar day."""

    date: datetime.date
    hours: list[HourForecast]
    summary: DailySummary | None = None


class MultiDayForecast(BaseModel):
    """Top-level container returned by a weather client."""

    days: list[DayForecast]
    timezone: str | None = None

    def upcoming_hours(
        self, count: int, *, now: datetime.datetime | None = None
    ) -> list[HourForecast]:
        """Return the next *count* hourly slots at or after *now*.

        "Now" is evaluated in the forecast's own timezone, so asking for Tokyo
        from New York still starts at the next hour in Tokyo. Falls back to the
        first *count* slots when the whole forecast is behind us, so a panel
        always has something to show.

        :param count: How many hours to return.
        :param now: Reference time; defaults to the current local time at the
            forecast location.
        """
        flat = [hour for day in self.days for hour in day.hours]
        if not flat:
            return []

        reference = now if now is not None else self.local_now()
        cutoff = reference.replace(minute=0, second=0, microsecond=0)
        if cutoff.tzinfo != flat[0].time.tzinfo:
            cutoff = cutoff.replace(tzinfo=flat[0].time.tzinfo)

        upcoming = [hour for hour in flat if hour.time >= cutoff]
        return (upcoming or flat)[:count]

    def local_now(self) -> datetime.datetime:
        """Current wall-clock time at the forecast location.

        Falls back to this machine's local time when the provider did not name
        a timezone or names one this system does not know.
        """
        if self.timezone:
            try:
                return datetime.datetime.now(ZoneInfo(self.timezone)).replace(
                    tzinfo=None
                )
            except (ZoneInfoNotFoundError, ValueError):
                pass
        return datetime.datetime.now()

    @property
    def today(self) -> DayForecast | None:
        """The first day in the forecast, which is today for a normal request."""
        return self.days[0] if self.days else None
