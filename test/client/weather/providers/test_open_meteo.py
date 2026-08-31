"""Tests for the Open-Meteo weather provider.

Strategy: inject a FakeHttpClient (see test/conftest.py) and assert on the
query mydash sends and the forecast it parses back.
"""

import asyncio
from datetime import date, datetime

import pytest
from pydantic import ValidationError

from mydash.client.weather.base_errors import WeatherClientError
from mydash.client.weather.factory import get_weather_client
from mydash.client.weather.providers.open_meteo.errors import (
    HourForecastSettingError,
    ParameterSettingError,
    ResponseError,
)
from mydash.client.weather.providers.open_meteo.open_meteo import OpenMeteoClient
from mydash.client.weather.providers.open_meteo.schemas import UNITS_PRESETS
from mydash.models.geocoding import Coordinates
from mydash.models.weather import MultiDayForecast
from mydash.storage.cache import TTL
from test.conftest import FakeHttpClient

MIAMI = Coordinates(latitude=25.7617, longitude=-80.1918)

HOURLY_KEYS = (
    "temperature_2m",
    "apparent_temperature",
    "precipitation_probability",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "uv_index",
)


def _hourly(times: list[str]) -> dict:
    """Build parallel hourly arrays matching *times*."""
    count = len(times)
    return {
        "time": times,
        "temperature_2m": [20.0 + index for index in range(count)],
        "apparent_temperature": [21.0 + index for index in range(count)],
        "precipitation_probability": [10 * index for index in range(count)],
        "precipitation": [0.1 * index for index in range(count)],
        "weather_code": [0] * count,
        "cloud_cover": [5 * index for index in range(count)],
        "wind_speed_10m": [3.0] * count,
        "uv_index": [4.0] * count,
    }


def _daily(days: list[str]) -> dict:
    return {
        "time": days,
        "temperature_2m_max": [31.0] * len(days),
        "temperature_2m_min": [22.0] * len(days),
        "precipitation_probability_max": [40] * len(days),
        "sunrise": [f"{day}T06:45" for day in days],
        "sunset": [f"{day}T19:55" for day in days],
    }


def _payload(times=None, days=None, timezone="America/New_York") -> dict:
    times = times or ["2026-08-30T00:00", "2026-08-30T01:00", "2026-08-31T00:00"]
    days = days or ["2026-08-30", "2026-08-31"]
    return {"timezone": timezone, "hourly": _hourly(times), "daily": _daily(days)}


def _fetch(http, **kwargs) -> MultiDayForecast:
    return asyncio.run(
        OpenMeteoClient(http_client=http).fetch_forecast(MIAMI, **kwargs)
    )


# --- request shape --------------------------------------------------------


def test_request_sends_coordinates_units_and_local_timezone():
    http = FakeHttpClient(_payload())

    _fetch(http, days=2, past_days=1, units="imperial")

    params = http.parameters()
    assert params["latitude"] == MIAMI.latitude
    assert params["longitude"] == MIAMI.longitude
    assert params["forecast_days"] == 2
    assert params["past_days"] == 1
    assert params["timezone"] == "auto"
    for key in HOURLY_KEYS:
        assert key in params["hourly"]
    assert "temperature_2m_max" in params["daily"]
    assert "sunrise" in params["daily"]
    assert http.calls[0]["cache_ttl"] == TTL["weather"]


@pytest.mark.parametrize("units", sorted(UNITS_PRESETS))
def test_unit_presets_map_to_provider_fields(units):
    http = FakeHttpClient(_payload())

    _fetch(http, units=units)

    params = http.parameters()
    expected = UNITS_PRESETS[units]
    assert params["temperature_unit"] == expected["temperature_unit"]
    assert params["wind_speed_unit"] == expected["wind_speed_unit"]
    assert params["precipitation_unit"] == expected["precipitation_unit"]


def test_unknown_units_raise_value_error():
    http = FakeHttpClient()

    with pytest.raises(ValueError, match="invalid weather units"):
        _fetch(http, units="kelvin")


@pytest.mark.parametrize("days, past_days", [(0, 0), (17, 0), (1, 4), (1, -1)])
def test_out_of_range_day_counts_raise_parameter_setting_error(days, past_days):
    http = FakeHttpClient()

    with pytest.raises(ParameterSettingError):
        _fetch(http, days=days, past_days=past_days)


# --- parsing --------------------------------------------------------------


def test_hours_are_grouped_into_calendar_days():
    forecast = _fetch(FakeHttpClient(_payload()))

    assert [day.date for day in forecast.days] == [
        date(2026, 8, 30),
        date(2026, 8, 31),
    ]
    assert len(forecast.days[0].hours) == 2
    assert len(forecast.days[1].hours) == 1


def test_hour_fields_are_mapped_from_provider_keys():
    forecast = _fetch(FakeHttpClient(_payload()))

    hour = forecast.days[0].hours[0]
    assert hour.time == datetime(2026, 8, 30, 0, 0)
    assert hour.hour == 0
    assert hour.temperature == 20.0
    assert hour.feels_like_temperature == 21.0
    assert hour.chance_of_rain == 0
    assert hour.cloud_cover == 0
    assert hour.wind_speed == 3.0
    assert hour.uv_index == 4.0


def test_timezone_is_carried_on_the_forecast():
    forecast = _fetch(FakeHttpClient(_payload(timezone="Asia/Tokyo")))

    assert forecast.timezone == "Asia/Tokyo"


def test_daily_summary_is_attached_to_its_day():
    forecast = _fetch(FakeHttpClient(_payload()))

    summary = forecast.days[0].summary
    assert summary is not None
    assert summary.high == 31.0
    assert summary.low == 22.0
    assert summary.max_chance_of_rain == 40
    assert summary.sunrise == datetime(2026, 8, 30, 6, 45)
    assert summary.sunset == datetime(2026, 8, 30, 19, 55)


def test_missing_daily_block_is_tolerated():
    payload = _payload()
    del payload["daily"]

    forecast = _fetch(FakeHttpClient(payload))

    assert forecast.days[0].summary is None
    assert forecast.days[0].hours  # the hourly forecast still arrived


def test_unparsable_daily_entries_are_skipped():
    payload = _payload()
    payload["daily"]["sunrise"] = ["not a time", "also not a time"]
    payload["daily"]["temperature_2m_max"] = [31.0, 30.0]

    summary = _fetch(FakeHttpClient(payload)).days[0].summary

    assert summary is not None
    assert summary.sunrise is None
    assert summary.high == 31.0


def test_daily_block_shorter_than_the_hourly_range_is_tolerated():
    payload = _payload(days=["2026-08-30"])

    forecast = _fetch(FakeHttpClient(payload))

    assert forecast.days[0].summary is not None
    assert forecast.days[1].summary is None


# --- error paths ----------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [{}, {"hourly": {}}, {"hourly": None}, {"hourly": {"temperature_2m": [1.0]}}],
)
def test_missing_hourly_series_raises_response_error(payload):
    with pytest.raises(ResponseError) as err:
        _fetch(FakeHttpClient(payload))

    assert isinstance(err.value, WeatherClientError)
    assert "Response error" in str(err.value)


def test_missing_hourly_field_raises_response_error():
    payload = _payload()
    del payload["hourly"]["uv_index"]

    with pytest.raises(ResponseError):
        _fetch(FakeHttpClient(payload))


def test_short_hourly_series_raises_response_error():
    payload = _payload()
    payload["hourly"]["temperature_2m"] = [20.0]  # shorter than "time"

    with pytest.raises(ResponseError):
        _fetch(FakeHttpClient(payload))


def test_unparsable_hourly_timestamp_raises_response_error():
    payload = _payload()
    payload["hourly"]["time"] = ["yesterday", "today", "tomorrow"]

    with pytest.raises(ResponseError):
        _fetch(FakeHttpClient(payload))


def test_invalid_hour_values_raise_hour_forecast_setting_error():
    payload = _payload()
    payload["hourly"]["temperature_2m"] = ["warm", "warmer", "warmest"]

    with pytest.raises(HourForecastSettingError):
        _fetch(FakeHttpClient(payload))


def test_http_errors_propagate():
    with pytest.raises(RuntimeError, match="network down"):
        _fetch(FakeHttpClient(RuntimeError("network down")))


# --- coordinates ----------------------------------------------------------


@pytest.mark.parametrize(
    "latitude, longitude", [(91, 0), (-91, 0), (0, 181), (0, -181)]
)
def test_out_of_range_coordinates_are_rejected_by_the_model(latitude, longitude):
    with pytest.raises(ValidationError):
        Coordinates(latitude=latitude, longitude=longitude)


# --- factory wiring -------------------------------------------------------


def test_factory_passes_the_shared_http_client_through():
    http = FakeHttpClient(_payload())
    client = get_weather_client("open-meteo", http_client=http)

    assert client.http_client is http
    assert asyncio.run(client.fetch_forecast(MIAMI)).days
