"""Tests for the Open-Meteo weather forecast client."""

import pytest

from mydash.client.geocoding.schemas import Coordinates
from mydash.client.weather.factory import get_weather_client
from mydash.client.weather.schemas import HourForecast


def test_set_weather_forecast_without_coordinates_raises_value_error():
    client = get_weather_client("open-meteo")

    with pytest.raises(ValueError, match="Coordinates must be set"):
        client.set_weather_forecast()


def test_set_weather_forecast_appends_final_day(mocker):
    client = get_weather_client("open-meteo")
    client.set_coordinates(Coordinates(latitude=25.76, longitude=-80.19))

    mock_response = {
        "hourly": {
            "time": [
                "2026-07-01T10:00",
                "2026-07-01T11:00",
                "2026-07-02T10:00",
            ],
            "temperature_2m": [30.0, 31.0, 29.0],
            "apparent_temperature": [32.0, 33.0, 31.0],
            "precipitation_probability": [10, 20, 30],
            "precipitation": [0.0, 0.1, 0.2],
            "weather_code": [0, 1, 2],
            "cloud_cover": [5, 10, 15],
            "wind_speed_10m": [3.0, 4.0, 5.0],
            "uv_index": [1.0, 2.0, 3.0],
        }
    }
    mocker.patch.object(client, "_make_request", return_value=mock_response)

    client.set_weather_forecast(forecast_length=2)
    forecast = client.get_weather_forecast()

    assert len(forecast.days) == 2
    assert forecast.days[0].day == 1
    assert forecast.days[1].day == 2
    assert len(forecast.days[0].hours) == 2
    assert len(forecast.days[1].hours) == 1


def test_set_weather_forecast_hour_is_int(mocker):
    client = get_weather_client("open-meteo")
    client.set_coordinates(Coordinates(latitude=25.76, longitude=-80.19))

    mock_response = {
        "hourly": {
            "time": ["2026-07-01T14:00"],
            "temperature_2m": [30.0],
            "apparent_temperature": [32.0],
            "precipitation_probability": [10],
            "precipitation": [0.0],
            "weather_code": [0],
            "cloud_cover": [5],
            "wind_speed_10m": [3.0],
            "uv_index": [1.0],
        }
    }
    mocker.patch.object(client, "_make_request", return_value=mock_response)

    client.set_weather_forecast()
    hour = client.get_weather_forecast().days[0].hours[0]

    assert isinstance(hour, HourForecast)
    assert hour.hour == 14
    assert isinstance(hour.hour, int)
