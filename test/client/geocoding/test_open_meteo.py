"""Tests for the Open-Meteo geocoding client.

Covers coordinate resolution for valid cities (mocked API responses) and error
handling for invalid input. HTTP-layer error tests are stubbed pending fixtures.

TODO(testing): add test suites for weather, news, stocks, and CLI modules.
TODO(testing): create test/conftest.py with shared fixtures (mock_urls, httpx mocks).
TODO(config): move pytest and pytest-mock from runtime deps to a dev group in pyproject.toml.
"""

from typing import Any
from urllib.error import HTTPError

import pytest
from pydantic import ValidationError
from pytest_mock import MockFixture

import httpx

from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.geocoding.schemas import Coordinates


def test__make_request_invalid_request_return_raised_staus_error(mocker, mock_urls):
    # TODO(testing): add mock_urls fixture (e.g. in conftest.py) and finish this test
    ...


@pytest.mark.parametrize(
    "mock_results, mock_city, mock_latitude, mock_longitude",
    [
        ({"results": [{"latitude": 25.7617, "longitude": -80.1918}]}, "Miami", 25.7617, -80.1918),
        ({"results": [{"latitude": 52.52437, "longitude": 13.41053}]}, "Berlin", 52.52437, 13.41053),
        ({"results": [{"latitude": -23.5475, "longitude": -46.63611}]}, "São Paulo", -23.5475, -46.63611),
        ({"results": [{"latitude": 35.6895, "longitude": 139.69171}]}, "Tokyo", 35.6895, 139.69171),
    ]
)
def test_get_coordinates_valid_city_return_coordinates(
    mocker: MockFixture,
    mock_results,
    mock_city: str,
    mock_latitude: float,
    mock_longitude: float,
) -> None:
    client = get_geocoding_client("open-meteo")
    mocker.patch.object(client, "_make_request", return_value=mock_results)

    result = client.get_coordinates(mock_city)

    assert isinstance(result, Coordinates)
    assert result.latitude == mock_latitude
    assert result.longitude == mock_longitude


@pytest.mark.parametrize(
    "city, error_type",
    [
        ("abracadabra", ValueError),
        ("bob is your uncle", ValueError),
        (2, ValidationError),
        ("", ValueError),
    ],
)
def test_get_coordinates_invalid_city_return_raised_error(city: str, error_type):
    client = get_geocoding_client("open-meteo")
    with pytest.raises(error_type) as err:
        client.get_coordinates(city)
    assert err.type is error_type