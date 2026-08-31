"""Open-Meteo Forecast API client implementation.

Free, keyless hourly weather via https://api.open-meteo.com/v1/forecast.

Forecasts are requested with ``timezone=auto``, so every timestamp is local to
the place being forecast, and with a small ``daily`` block so panels can show
today's high, low, and daylight without a second request.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import httpx
from pydantic import ValidationError

from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.weather.base import WeatherClient
from mydash.client.weather.providers.open_meteo.errors import (
    DayForecastSettingError,
    HourForecastSettingError,
    ParameterSettingError,
    ResponseError,
)
from mydash.client.weather.providers.open_meteo.schemas import (
    UNITS_PRESETS,
    Parameters,
    WeatherUnitsPreset,
)
from mydash.models.geocoding import Coordinates
from mydash.models.weather import (
    DailySummary,
    DayForecast,
    HourForecast,
    MultiDayForecast,
)
from mydash.storage.cache import TTL

FORECAST_URL = httpx.URL("https://api.open-meteo.com/v1/forecast")

#: Open-Meteo timestamp formats: minute precision for hourly, plain date for daily.
_TIME_FORMAT = "%Y-%m-%dT%H:%M"
_DATE_FORMAT = "%Y-%m-%d"

# Hourly response keys → HourForecast field names.
_HOURLY_FIELDS: dict[str, str] = {
    "temperature_2m": "temperature",
    "apparent_temperature": "feels_like_temperature",
    "cloud_cover": "cloud_cover",
    "wind_speed_10m": "wind_speed",
    "precipitation_probability": "chance_of_rain",
    "precipitation": "amount_of_rain",
    "weather_code": "weather_code",
    "uv_index": "uv_index",
}


class OpenMeteoClient(WeatherClient):
    """Fetch and parse multi-day hourly forecasts from Open-Meteo."""

    def __init__(self, http_client: HttpApiClient | None = None) -> None:
        """Build the client.

        :param http_client: Shared HTTP client; one is created per instance
            when omitted.
        """
        self.url = FORECAST_URL
        self.http_client = http_client if http_client is not None else HttpApiClient()

    async def fetch_forecast(
        self,
        coordinates: Coordinates,
        *,
        days: int = 1,
        past_days: int = 0,
        units: WeatherUnitsPreset = "metric",
    ) -> MultiDayForecast:
        """Fetch an hourly forecast for *coordinates*, grouped by local day.

        :param coordinates: Location to forecast.
        :param days: Forward days to request from Open-Meteo.
        :param past_days: Past days to include.
        :param units: ``metric`` (default) or ``imperial``.
        :raises ParameterSettingError: If the query cannot be built.
        :raises ResponseError: If the response is missing expected series.
        """
        params = self._build_parameters(
            coordinates=coordinates, days=days, past_days=past_days, units=units
        )

        response = await self.http_client.make_request(
            url=self.url,
            request_method="GET",
            parameters=params.to_params(),
            cache_ttl=TTL["weather"],
        )

        hourly = response.get("hourly")
        if not hourly or "time" not in hourly:
            raise ResponseError(query=params, api_response=response)

        summaries = _parse_daily(response.get("daily"))
        days_out = _group_hours_by_day(hourly, params, summaries)

        return MultiDayForecast(days=days_out, timezone=response.get("timezone"))

    def _build_parameters(
        self,
        *,
        coordinates: Coordinates,
        days: int,
        past_days: int,
        units: WeatherUnitsPreset,
    ) -> Parameters:
        """Build validated :class:`Parameters`, including unit preset mapping.

        :raises ParameterSettingError: If *units* is unknown or validation fails.
        """
        unit_fields = UNITS_PRESETS.get(units)
        if unit_fields is None:
            raise ValueError(
                f"invalid weather units {units!r}; expected one of "
                f"{sorted(UNITS_PRESETS)}"
            )
        try:
            return Parameters(
                coordinates=coordinates,
                forecast_days=days,
                past_days=past_days,
                temperature_unit=unit_fields["temperature_unit"],  # type: ignore[arg-type]
                wind_speed_unit=unit_fields["wind_speed_unit"],  # type: ignore[arg-type]
                precipitation_unit=unit_fields["precipitation_unit"],  # type: ignore[arg-type]
            )
        except ValidationError as err:
            raise ParameterSettingError(validation_err=err) from err


def _group_hours_by_day(
    hourly: dict[str, Any],
    params: Parameters,
    summaries: dict[date, DailySummary],
) -> list[DayForecast]:
    """Turn Open-Meteo's parallel hourly arrays into per-day forecasts."""
    times = hourly["time"]
    grouped: dict[date, list[HourForecast]] = {}

    for index, raw_time in enumerate(times):
        try:
            when = datetime.strptime(raw_time, _TIME_FORMAT)
        except (TypeError, ValueError) as err:
            raise ResponseError(query=params, api_response=hourly, error=err) from err

        try:
            values = {
                field: hourly[key][index] for key, field in _HOURLY_FIELDS.items()
            }
        except (KeyError, IndexError, TypeError) as err:
            raise ResponseError(query=params, api_response=hourly, error=err) from err

        try:
            hour = HourForecast(time=when, **values)
        except ValidationError as err:
            raise HourForecastSettingError(err) from err

        grouped.setdefault(when.date(), []).append(hour)

    try:
        return [
            DayForecast(date=day, hours=hours, summary=summaries.get(day))
            for day, hours in grouped.items()
        ]
    except ValidationError as err:
        raise DayForecastSettingError(err) from err


def _parse_daily(daily: Any) -> dict[date, DailySummary]:
    """Parse the optional ``daily`` block into per-date summaries.

    The daily block is a bonus, not a requirement: anything unparsable here is
    dropped so a missing sunrise never costs you the forecast.
    """
    if not isinstance(daily, dict) or not daily.get("time"):
        return {}

    summaries: dict[date, DailySummary] = {}
    for index, raw_date in enumerate(daily["time"]):
        try:
            day = datetime.strptime(raw_date, _DATE_FORMAT).date()
        except (TypeError, ValueError):
            continue
        summaries[day] = DailySummary(
            high=_at(daily, "temperature_2m_max", index),
            low=_at(daily, "temperature_2m_min", index),
            max_chance_of_rain=_at(daily, "precipitation_probability_max", index),
            sunrise=_time_at(daily, "sunrise", index),
            sunset=_time_at(daily, "sunset", index),
        )
    return summaries


def _at(daily: dict[str, Any], key: str, index: int) -> Any:
    """Return ``daily[key][index]`` when present, else ``None``."""
    series = daily.get(key)
    if not isinstance(series, list) or index >= len(series):
        return None
    return series[index]


def _time_at(daily: dict[str, Any], key: str, index: int) -> datetime | None:
    """Parse a daily timestamp such as sunrise/sunset, tolerating junk."""
    raw = _at(daily, key, index)
    if not isinstance(raw, str):
        return None
    try:
        return datetime.strptime(raw, _TIME_FORMAT)
    except ValueError:
        return None
