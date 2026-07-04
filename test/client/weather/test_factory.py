"""Tests for mydash.client.weather.factory.

Target: get_weather_client(provider, **config)
Strategy: direct instantiation checks; no HTTP mocking needed.
"""

import pytest

from src.mydash.client.weather.base import WeatherClient
from src.mydash.client.weather.factory import get_weather_client


# --- Factory ---
@pytest.mark.parametrize(
    argnames="mock_provider, expected_provider",
    argvalues=[
        (None, "OpenMeteoClient"),
        ("open-meteo", "OpenMeteoClient"),
        ("", "OpenMeteoClient"),
    ],
)
def test_get_weather_client_valid_provider_return_weather_client_instance(
    mock_provider, expected_provider
):
    weather_client: WeatherClient = get_weather_client(mock_provider)
    assert weather_client.__class__.__name__ == expected_provider


# TODO(testing): unknown provider raises ValueError — parametrize invalid names
@pytest.mark.parametrize(
    argnames="mock_provider, expected_error",
    argvalues=[
        (2, ValueError),
        ("hoopla", ValueError),
        ({}, ValueError),
    ],
)
def test_get_weather_client_invalid_provider_raise_value_error(
    mock_provider, expected_error
):
    with pytest.raises(expected_error) as err:
        get_weather_client(mock_provider)
    assert isinstance(err.value, expected_error)
