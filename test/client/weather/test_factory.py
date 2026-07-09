"""Tests for mydash.client.weather.factory."""

import pytest

from mydash.client.weather.base import WeatherClient
from mydash.client.weather.base_errors import WeatherFactoryError
from mydash.client.weather.factory import get_weather_client


# Test Case: Valid Provider -> Returns client instance
@pytest.mark.parametrize(
    argnames="mock_provider, expected_provider",
    argvalues=[
        ("open-meteo", "OpenMeteoClient"),
    ],
)
def test_get_weather_client_valid_provider_return_weather_client_instance(
    mock_provider, expected_provider
):
    weather_client: WeatherClient = get_weather_client(mock_provider)
    assert weather_client.__class__.__name__ == expected_provider


# Test Case: Invalid Provider -> Raises WeatherFactoryError
@pytest.mark.parametrize(
    argnames="mock_provider, expected_error",
    argvalues=[
        (2, WeatherFactoryError),
        ("hoopla", WeatherFactoryError),
        ({}, WeatherFactoryError),
        (None, WeatherFactoryError),
    ],
)
def test_get_weather_client_invalid_provider_raise_weather_factory_error(
    mock_provider, expected_error
):
    with pytest.raises(expected_error) as err:
        get_weather_client(mock_provider)
    assert isinstance(err.value, expected_error)
