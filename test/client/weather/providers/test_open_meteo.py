"""Tests for mydash.client.weather.open_meteo."""

import asyncio

from unittest.mock import AsyncMock, MagicMock

import pytest

from mydash.models.geocoding import Coordinates
from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.weather.factory import get_weather_client
from mydash.client.weather.providers.open_meteo.errors import (
    CoordinateSettingError,
    HourForecastSettingError,
    MissingCoordinatesError,
    MissingWeatherForecastError,
    ParameterSettingError,
    ResponseError,
)
from mydash.models.weather import DayForecast, HourForecast, MultiDayForecast

# =====================================
# ***** Testing 'set_coordinates' ***** | TESTING COMPLETE : 07/09/26
# =====================================


# Test case: Invalid Coordinate Input -> raise CoordinateSettingError
@pytest.mark.parametrize(
    argnames="mock_bad_input, expected_error",
    argvalues=[
        (None, CoordinateSettingError),
        (2, CoordinateSettingError),
        ("bobby", CoordinateSettingError),
    ],
)
def test_set_coordinates_invalid_input_raise_coordinate_setting_error(
    mock_bad_input, expected_error
):
    weather_client = get_weather_client()

    with pytest.raises(expected_error) as err:
        weather_client.set_coordinates(mock_bad_input)
    assert isinstance(err.value, expected_error)


# Test case: Valid Coordinate Input -> sets coordinates 'self.coordinates'
@pytest.mark.parametrize(
    argnames="mock_valid_input, expected_result",
    argvalues=[
        (
            Coordinates(latitude=90, longitude=20),
            Coordinates(latitude=90, longitude=20),
        ),
        (
            Coordinates(latitude=60, longitude=80),
            Coordinates(latitude=60, longitude=80),
        ),
        (
            Coordinates(latitude=20, longitude=50),
            Coordinates(latitude=20, longitude=50),
        ),
        (
            Coordinates(latitude=30, longitude=20),
            Coordinates(latitude=30, longitude=20),
        ),
    ],
)
def test_set_coordinates_valid_input_set_coordinates(mock_valid_input, expected_result):
    weather_client = get_weather_client()
    weather_client.set_coordinates(mock_valid_input)

    assert weather_client.coordinates == expected_result


# =======================================
# ***** Testing 'get_coordinates' ***** |
# =======================================


# Test Case: Valid Coordinates have been set -> Return Coordinates
@pytest.mark.parametrize(
    argnames="mock_coordinates, expected_results",
    argvalues=[
        (
            Coordinates(latitude=50, longitude=50),
            Coordinates(latitude=50, longitude=50),
        ),
        (
            Coordinates(latitude=20, longitude=50),
            Coordinates(latitude=20, longitude=50),
        ),
        (
            Coordinates(latitude=50, longitude=30),
            Coordinates(latitude=50, longitude=30),
        ),
        (
            Coordinates(latitude=50, longitude=50),
            Coordinates(latitude=50, longitude=50),
        ),
    ],
)
def test_get_coordinates_valid_coordinates_return_coordinates(
    mock_coordinates, expected_results
):
    weather_client = get_weather_client()
    weather_client.set_coordinates(coordinates=mock_coordinates)
    client_coordinates = weather_client.get_coordinates()

    assert client_coordinates == expected_results


# Test Case: No Coordinates have been set -> Raise MissingCoordinatesError
def test_get_coordinates_no_coordinates_raise_missing_coordinates_error():
    weather_client = get_weather_client()

    with pytest.raises(MissingCoordinatesError) as err:
        weather_client.get_coordinates()
    assert isinstance(err.value, MissingCoordinatesError)


# ============================================
# ***** Testing 'set_weather_forecast' ***** |
# ============================================


# Test Case: Bad Parameters lead to validation error -> Raise ParameterSettingError
@pytest.mark.parametrize(
    argnames="mock_coordinates, mock_forecast_length, mock_backwardcast_length, expected_error",
    argvalues=[
        (Coordinates(latitude=20, longitude=20), None, 1, ParameterSettingError),
        (Coordinates(latitude=20, longitude=20), 1, None, ParameterSettingError),
        (
            Coordinates(latitude=20, longitude=20),
            "some_thing",
            1,
            ParameterSettingError,
        ),
        (
            Coordinates(latitude=20, longitude=20),
            1,
            "some_thing",
            ParameterSettingError,
        ),
        (Coordinates(latitude=20, longitude=20), -20, 1, ParameterSettingError),
        (Coordinates(latitude=20, longitude=20), 1, -20, ParameterSettingError),
        (Coordinates(latitude=20, longitude=20), None, None, ParameterSettingError),
        (
            Coordinates(latitude=20, longitude=20),
            "some_thing",
            -20,
            ParameterSettingError,
        ),
        (
            Coordinates(latitude=20, longitude=20),
            -20,
            "some_thing",
            ParameterSettingError,
        ),
    ],
)
def test_set_weather_forecast_bad_parameter_values_raise_parameter_setting_error(
    mock_coordinates, mock_forecast_length, mock_backwardcast_length, expected_error
):
    weather_client = get_weather_client()
    weather_client.set_coordinates(mock_coordinates)
    with pytest.raises(expected_error) as err:
        asyncio.run(
            weather_client.set_weather_forecast(
            forecast_length=mock_forecast_length,
            backwardcast_length=mock_backwardcast_length,
            )
        )
    assert isinstance(err.value, expected_error)


# Test Case: Bad API responses(e.g. missing keys) -> Raise ResponseError
@pytest.mark.parametrize(
    argnames="mock_coordinates, mock_forecast_length, mock_backwardcast_length, mock_response, expected_error",
    argvalues=[
        (
            Coordinates(latitude=20, longitude=20),
            1,
            1,
            {},
            ResponseError,
        ),
        (
            Coordinates(latitude=20, longitude=20),
            1,
            1,
            {"hourly": []},
            ResponseError,
        ),
        (
            Coordinates(latitude=20, longitude=20),
            1,
            1,
            {"hourly": {"time": ["2026-07-08T00:00"]}},
            ResponseError,
        ),
        (
            Coordinates(latitude=20, longitude=20),
            1,
            1,
            {
                "hourly": {
                    "time": ["2026-07-08T00:00"],
                    "apparent_temperature": [20.4],
                    "precipitation_probability": [0],
                    "precipitation": [0],
                    "weather_code": [1],
                    "cloud_cover": [63],
                    "wind_speed_10m": [12.7],
                    "uv_index": [1.55],
                }
            },
            ResponseError,
        ),
    ],
)
def test_set_weather_forecast_bad_api_response_raise_response_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_coordinates,
    mock_forecast_length,
    mock_backwardcast_length,
    mock_response,
    expected_error,
):
    weather_client = get_weather_client()
    weather_client.set_coordinates(mock_coordinates)

    mock_api_response = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(HttpApiClient, "make_request", mock_api_response)

    with pytest.raises(expected_error) as err:
        asyncio.run(
            weather_client.set_weather_forecast(
            forecast_length=mock_forecast_length,
            backwardcast_length=mock_backwardcast_length,
            )
        )
    assert isinstance(err.value, expected_error)


# Test Case: Validation error when creating a 'hour_forecast' instance -> Raise HourForecastSettingError
@pytest.mark.parametrize(
    argnames="mock_coordinates, mock_forecast_length, mock_backwardcast_length, mock_response, expected_error",
    argvalues=[
        (
            Coordinates(latitude=20, longitude=20),
            1,
            1,
            {
                "hourly": {
                    "time": ["2026-07-08T00:00"],
                    "temperature_2m": ["something"],
                    "apparent_temperature": [20.4],
                    "precipitation_probability": [0],
                    "precipitation": [0],
                    "weather_code": [1],
                    "cloud_cover": [63],
                    "wind_speed_10m": [12.7],
                    "uv_index": [1.55],
                }
            },
            HourForecastSettingError,
        ),
        (
            Coordinates(latitude=20, longitude=20),
            1,
            1,
            {
                "hourly": {
                    "time": ["2026-07-08T00:00"],
                    "temperature_2m": [20.3],
                    "apparent_temperature": [20.4],
                    "precipitation_probability": [0],
                    "precipitation": [0],
                    "weather_code": [None],
                    "cloud_cover": [63],
                    "wind_speed_10m": [12.7],
                    "uv_index": [1.55],
                }
            },
            HourForecastSettingError,
        ),
        (
            Coordinates(latitude=20, longitude=20),
            1,
            1,
            {
                "hourly": {
                    "time": ["2026-07-08T00:00"],
                    "temperature_2m": [20.4],
                    "apparent_temperature": [20.4],
                    "precipitation_probability": [0],
                    "precipitation": [0],
                    "weather_code": [1],
                    "cloud_cover": [{"some key": "some value"}],
                    "wind_speed_10m": [12.7],
                    "uv_index": [None],
                }
            },
            HourForecastSettingError,
        ),
        (
            Coordinates(latitude=20, longitude=20),
            1,
            1,
            {
                "hourly": {
                    "time": ["2026-07-08T00:00"],
                    "temperature_2m": [20.3],
                    "apparent_temperature": [20.4],
                    "precipitation_probability": [0],
                    "precipitation": [0],
                    "weather_code": [1],
                    "cloud_cover": [None],
                    "wind_speed_10m": [12.7],
                    "uv_index": [1.55],
                }
            },
            HourForecastSettingError,
        ),
    ],
)
def test_set_weather_forecast_hour_forecast_validation_failure_raise_hour_forecast_setting_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_coordinates,
    mock_forecast_length,
    mock_backwardcast_length,
    mock_response,
    expected_error,
):
    weather_client = get_weather_client()
    weather_client.set_coordinates(mock_coordinates)

    mock_api_response = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(HttpApiClient, "make_request", mock_api_response)

    with pytest.raises(expected_error) as err:
        asyncio.run(
            weather_client.set_weather_forecast(
            forecast_length=mock_forecast_length,
            backwardcast_length=mock_backwardcast_length,
            )
        )
    assert isinstance(err.value, expected_error)


# ============================================
# ***** Testing 'get_weather_forecast' ***** |
# ============================================


# Test Case: Missing Weather(i.e. 'self.weather_forecast == None') -> Raise MissingWeatherForecastError
def test_get_weather_forecast_missing_weather_raise_missing_weather_forecast_error():
    weather_client = get_weather_client()

    with pytest.raises(MissingWeatherForecastError) as err:
        weather_client.get_weather_forecast()
    assert isinstance(err.value, MissingWeatherForecastError)


# Test Case: Valid weather forecast set by 'set_weather_forecast' -> Return MultiDayForecast
@pytest.mark.parametrize(
    argnames="mock_coordinates, mock_forecast_length, mock_backwardcast_length, mock_response, expected_result",
    argvalues=[
        (
            Coordinates(latitude=20, longitude=20),
            1,
            1,
            {
                "hourly": {
                    "time": ["2026-07-08T00:00"],
                    "temperature_2m": [23.4],
                    "apparent_temperature": [20.4],
                    "precipitation_probability": [0],
                    "precipitation": [0],
                    "weather_code": [1],
                    "cloud_cover": [63],
                    "wind_speed_10m": [12.7],
                    "uv_index": [1.55],
                }
            },
            MultiDayForecast(
                days=[
                    DayForecast(
                        month=7,
                        day=8,
                        hours=[
                            HourForecast(
                                hour=0,
                                temperature=23.4,
                                feels_like_temperature=20.4,
                                cloud_cover=63,
                                wind_speed=12.7,
                                chance_of_rain=0,
                                amount_of_rain=0,
                                weather_code=1,
                                uv_index=1.55,
                            )
                        ],
                    )
                ]
            ),
        )
    ],
)
def test_get_weather_found_weather_return_weather_forecast(
    monkeypatch: pytest.MonkeyPatch,
    mock_coordinates,
    mock_forecast_length,
    mock_backwardcast_length,
    mock_response,
    expected_result: MultiDayForecast,
):
    weather_client = get_weather_client("open-meteo")

    weather_client.set_coordinates(mock_coordinates)

    mock_api_response = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(HttpApiClient, "make_request", mock_api_response)

    asyncio.run(
        weather_client.set_weather_forecast(
        forecast_length=mock_forecast_length,
        backwardcast_length=mock_backwardcast_length,
        )
    )

    weather_forecast = weather_client.get_weather_forecast()

    request_params = mock_api_response.call_args.kwargs["parameters"]
    assert request_params["temperature_unit"] == "celsius"
    assert request_params["wind_speed_unit"] == "kmh"
    assert request_params["precipitation_unit"] == "mm"

    assert weather_forecast.days[0].day == expected_result.days[0].day
    assert weather_forecast.days[0].month == expected_result.days[0].month
    assert (
        weather_forecast.days[0].hours[0].amount_of_rain
        == expected_result.days[0].hours[0].amount_of_rain
    )
    assert (
        weather_forecast.days[0].hours[0].chance_of_rain
        == expected_result.days[0].hours[0].chance_of_rain
    )
    assert (
        weather_forecast.days[0].hours[0].cloud_cover
        == expected_result.days[0].hours[0].cloud_cover
    )
    assert (
        weather_forecast.days[0].hours[0].feels_like_temperature
        == expected_result.days[0].hours[0].feels_like_temperature
    )
    assert (
        weather_forecast.days[0].hours[0].temperature
        == expected_result.days[0].hours[0].temperature
    )
    assert (
        weather_forecast.days[0].hours[0].uv_index
        == expected_result.days[0].hours[0].uv_index
    )
    assert (
        weather_forecast.days[0].hours[0].weather_code
        == expected_result.days[0].hours[0].weather_code
    )
    assert (
        weather_forecast.days[0].hours[0].wind_speed
        == expected_result.days[0].hours[0].wind_speed
    )
    assert (
        weather_forecast.days[0].hours[0].hour == expected_result.days[0].hours[0].hour
    )
    assert isinstance(weather_forecast, MultiDayForecast)


def test_set_weather_forecast_imperial_units_in_request_params(
    monkeypatch: pytest.MonkeyPatch,
):
    weather_client = get_weather_client("open-meteo")
    weather_client.set_coordinates(Coordinates(latitude=20, longitude=20))

    mock_response = {
        "hourly": {
            "time": ["2026-07-08T00:00"],
            "temperature_2m": [74.0],
            "apparent_temperature": [72.0],
            "precipitation_probability": [0],
            "precipitation": [0],
            "weather_code": [1],
            "cloud_cover": [10],
            "wind_speed_10m": [8.0],
            "uv_index": [1.0],
        }
    }
    mock_api_response = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(HttpApiClient, "make_request", mock_api_response)

    asyncio.run(
        weather_client.set_weather_forecast(
        forecast_length=1,
        backwardcast_length=0,
        units="imperial",
        )
    )

    request_params = mock_api_response.call_args.kwargs["parameters"]
    assert request_params["temperature_unit"] == "fahrenheit"
    assert request_params["wind_speed_unit"] == "mph"
    assert request_params["precipitation_unit"] == "inch"
