"""Tests for mydash.client.geocoding.factory.

Target: get_geocoding_client(provider, **config)
Strategy: direct instantiation checks; no HTTP mocking needed.
"""

import pytest

from mydash.client.geocoding.base import GeocodingClient
from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.geocoding.providers.open_meteo import OpenMeteoClient


@pytest.mark.parametrize(
    argnames="mock_provider, expected_result",
    argvalues=[("open-meteo", OpenMeteoClient)],
)
def test_get_gecoding_client_valid_provider(mock_provider, expected_result) -> None:
    geocoding_client: GeocodingClient = get_geocoding_client(mock_provider)
    assert isinstance(geocoding_client, expected_result)


@pytest.mark.parametrize(
    argnames="mock_provider, expected_result",
    argvalues=[
        ("", ValueError),
        (None, ValueError),
        (2102, ValueError),
        ("open_meteo", ValueError),
        ("bad", ValueError),
    ],
)
def test_get_gecoding_client_invalid_provider(mock_provider, expected_result) -> None:
    with pytest.raises(ValueError):
        get_geocoding_client(mock_provider)
