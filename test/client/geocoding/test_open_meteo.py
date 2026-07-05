"""Tests for mydash.client.geocoding.open_meteo.

Target: OpenMeteoClient (stateful API)
Usage pattern: set_coordinates(city) fetches and caches; get_coordinates() reads cache.
Strategy: mock client.client.get or patch _make_request; use mock_urls fixture.
Depends on: conftest.mock_urls, conftest.sample_geocoding_response
"""

from unittest.mock import MagicMock

import httpx
import pytest
from pydantic import ValidationError

from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.geocoding.schemas import Coordinates


# --- _make_request / HTTP errors ---
# Pydantic checks that the provided value is of type 'str'.
# If the provided value is not, then pydantic will raise a validation error.
@pytest.mark.parametrize(
    argnames="mock_city, mock_expected_result",
    argvalues=[(None, ValidationError), ("", ValueError), (2, ValidationError)],
)
def test__make_request(mock_city, mock_expected_result):
    geocoding_client = get_geocoding_client()
    with pytest.raises(mock_expected_result):
        assert isinstance(
            geocoding_client.set_coordinates(mock_city), mock_expected_result
        )


def make_bad_response(status_code: int) -> httpx.Response:
    request = httpx.Request("GET", "https://example.com/some/endpoint")
    return httpx.Response(status_code=status_code, request=request)


@pytest.mark.parametrize(
    argnames="status_code", argvalues=[400, 401, 403, 404, 429, 500, 502, 503]
)
def test__make_request_raises_http_status_error(monkeypatch, status_code):
    geocoding_client = get_geocoding_client()

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = make_bad_response(status_code)

    monkeypatch.setattr(geocoding_client, "client", mock_client)

    with pytest.raises(httpx.HTTPStatusError) as err:
        geocoding_client._make_request({"name": "Miami"})
    assert err.value.response.status_code == status_code, (
        f"Raised:{err.value.response.status_code} and expected: {status_code}"
    )


@pytest.mark.parametrize(
    argnames="mock_city, mock_coordinates, expected_coordinates",
    argvalues=[
        (
            "Miami",
            Coordinates(latitude=25.7743, longitude=-80.1937),
            Coordinates(latitude=25.7743, longitude=-80.1937),
        ),
        (
            "Berlin",
            Coordinates(latitude=52.5244, longitude=13.4105),
            Coordinates(latitude=52.5244, longitude=13.4105),
        ),
        (
            "São Paulo",
            Coordinates(latitude=-23.5475, longitude=-46.6361),
            Coordinates(latitude=-23.5475, longitude=-46.6361),
        ),
    ],
)
def test_set_coordinates_valid_city(
    monkeypatch,
    mock_city: str,
    mock_coordinates: Coordinates,
    expected_coordinates: Coordinates,
) -> None:
    geocoding_client = get_geocoding_client()

    mock_make_request = MagicMock(
        return_value={"results": [mock_coordinates.model_dump()]}
    )

    monkeypatch.setattr(geocoding_client, "_make_request", mock_make_request)

    geocoding_client.set_coordinates(mock_city)

    assert geocoding_client.coordinates.latitude == expected_coordinates.latitude
    assert geocoding_client.coordinates.longitude == expected_coordinates.longitude
    mock_make_request.assert_called_once()


@pytest.mark.parametrize(
    argnames="mock_city, expected_error",
    argvalues=[
        (None, ValidationError),
        ("", ValueError),
        (2, ValidationError),
        ({"name": "miami"}, ValidationError),
    ],
)
def test_set_coordinate_invalid_city_input(mock_city, expected_error):
    geocoding_client = get_geocoding_client()
    with pytest.raises(expected_error) as err:
        geocoding_client.set_coordinates(mock_city)
    assert isinstance(err.value, expected_error)


@pytest.mark.parametrize(
    argnames="mock_city, mock_response, expected_error",
    argvalues=[
        ("Miami", {}, ValueError),
        ("Abscond", {"error": "hello"}, ValueError),
    ],
)
def test_set_coordinates_response_no_results_raises_value_error(
    monkeypatch, mock_city, mock_response, expected_error
):
    geocoding_client = get_geocoding_client()

    mock_make_request = MagicMock(return_value=mock_response)
    monkeypatch.setattr(geocoding_client, "_make_request", mock_make_request)

    with pytest.raises(expected_exception=expected_error) as err:
        geocoding_client.set_coordinates(mock_city)
    assert isinstance(err.value, expected_error)


@pytest.mark.parametrize(
    argnames="mock_city, mock_latitude, mock_longitude", argvalues=[("Miami", 0, 0)]
)
def test_get_coordinates(monkeypatch, mock_city, mock_latitude, mock_longitude):
    geocoding_client = get_geocoding_client()

    mock_make_request = MagicMock(
        return_value={
            "results": [{"latitude": mock_latitude, "longitude": mock_longitude}]
        }
    )
    monkeypatch.setattr(geocoding_client, "_make_request", mock_make_request)
    geocoding_client.set_coordinates(mock_city)

    result_coordinates = geocoding_client.get_coordinates()
    assert result_coordinates.__class__.__name__ == "Coordinates"
    assert result_coordinates.latitude == mock_latitude
    assert result_coordinates.longitude == mock_longitude
