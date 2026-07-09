"""Tests for mydash.client.geocoding.factory."""

import pytest

from mydash.client.geocoding.base import GeocodingClient
from mydash.client.geocoding.base_errors import GeocodingFactoryError
from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.geocoding.providers.open_meteo.open_meteo import OpenMeteoClient


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
        ("", GeocodingFactoryError),
        (None, GeocodingFactoryError),
        (2102, GeocodingFactoryError),
        ("open_meteo", GeocodingFactoryError),
        ("bad", GeocodingFactoryError),
    ],
)
def test_get_gecoding_client_invalid_provider(mock_provider, expected_result) -> None:
    with pytest.raises(GeocodingFactoryError):
        get_geocoding_client(mock_provider)
