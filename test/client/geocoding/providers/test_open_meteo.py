"""Tests for mydash.client.geocoding.open_meteo."""

import asyncio

from unittest.mock import AsyncMock, MagicMock

import pytest

from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.geocoding.providers.open_meteo.errors import (
    CoordinatesSettingError,
    OpenMeteoCityNotFoundError,
    OpenMeteoCoordinatesNotFoundError,
    OpenMeteoResponseError,
    ParameterSettingError,
)
from mydash.models.geocoding import Coordinates
from mydash.client.http_api.http_api import HttpApiClient

# =============================================
# ******* Tests for 'set_coordinates' ********
# =============================================


# ------------------------------
# Stage 1: City Input Validation | TESTING COMPLETE : 07/08/26
# ------------------------------
# NOTE This test has been refactored.
@pytest.mark.parametrize(
    argnames="mock_city, expected_error",
    argvalues=[
        (None, ParameterSettingError),
        (2, ParameterSettingError),
        ({"name": "miami"}, ParameterSettingError),
    ],
)
def test_set_coordinate_invalid_city_input_raise_parameter_setting_error(
    mock_city, expected_error
):
    geocoding_client = get_geocoding_client()
    with pytest.raises(expected_error) as err:
        asyncio.run(geocoding_client.set_coordinates(mock_city))
    assert isinstance(err.value, expected_error)


# --------------------------
# Stage 2: Response Checking | TESTING COMPLETE : 07/08/26
# --------------------------


# NOTE: Tests CityNotFoundError path for missing data from api response.
@pytest.mark.parametrize(
    argnames="mock_city, mock_results,expected_error",
    argvalues=[
        ("bad_city_input", {"results": None}, OpenMeteoCityNotFoundError),
        ("bad_city_input", {"results": []}, OpenMeteoCityNotFoundError),
        ("bad_city_input", {"results": {}}, OpenMeteoCityNotFoundError),
        ("bad_city_input", {"results": ()}, OpenMeteoCityNotFoundError),
    ],
)
def test_set_coordinates_missing_coord_raise_city_not_found_error(
    monkeypatch: pytest.MonkeyPatch, mock_city, mock_results, expected_error
):
    geocoding_client = get_geocoding_client()

    mock_response = AsyncMock(return_value=mock_results)
    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    with pytest.raises(expected_error) as err:
        asyncio.run(geocoding_client.set_coordinates(city=mock_city))
    assert isinstance(err.value, expected_error)


# NOTE: Tests ResposneError path for malformed data that leads to validation errors.
@pytest.mark.parametrize(
    argnames="mock_city, mock_results, expected_error",
    argvalues=[
        ("bad_city_input", {"results": [1, 2, 3]}, OpenMeteoResponseError),
        (
            "bad_city_input",
            {"results": ({"latitude": 80.21, "longitude": None}, 2)},
            OpenMeteoResponseError,
        ),
        ("bad_city_input", {"results": [(1, 2, 3)]}, OpenMeteoResponseError),
        (
            "bad_city_input",
            {"results": {"latitude": 80.21, "longitude": None}},
            OpenMeteoResponseError,
        ),
    ],
)
def test_set_coordinates_received_malformed_data_raise_response_error(
    monkeypatch: pytest.MonkeyPatch, mock_city, mock_results, expected_error
):
    geocoding_client = get_geocoding_client()

    mock_reponse = AsyncMock(return_value=mock_results)
    monkeypatch.setattr(HttpApiClient, "make_request", mock_reponse)

    with pytest.raises(expected_error) as err:
        asyncio.run(geocoding_client.set_coordinates(mock_city))
    assert isinstance(err.value, expected_error)


# --------------------------------------
# Stage 3: Setting Coordinate Validation |  TESTING COMPLETE : 07/08/26
# --------------------------------------


# NOTE: Tests 'happy path' in which valid coordinates are set
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
def test_set_coordinates_valid_coordinates(
    monkeypatch,
    mock_city: str,
    mock_coordinates: Coordinates,
    expected_coordinates: Coordinates,
) -> None:
    geocoding_client = get_geocoding_client()

    mock_make_request = AsyncMock(
        return_value={"results": [mock_coordinates.model_dump()]}
    )

    monkeypatch.setattr(HttpApiClient, "make_request", mock_make_request)

    asyncio.run(geocoding_client.set_coordinates(mock_city))

    if geocoding_client.coordinates is not None:
        assert geocoding_client.coordinates.latitude == expected_coordinates.latitude
        assert geocoding_client.coordinates.longitude == expected_coordinates.longitude
        mock_make_request.assert_called_once()


# NOTE: Tests validation failure of api_response to Coordinates
@pytest.mark.parametrize(
    argnames="mock_city, mock_bad_data, expected_error",
    argvalues=[
        (
            "Miami",
            {"latitude": 52.5244, "longitude": None},
            CoordinatesSettingError,
        ),
        (
            "Berlin",
            {"latitude": 52.5244, "longitude": None},
            CoordinatesSettingError,
        ),
        (
            "Paris",
            {"latitude": None, "longitude": 67.3},
            CoordinatesSettingError,
        ),
        (
            "São Paulo",
            {"foo": 52.5244, "longitude": None},
            CoordinatesSettingError,
        ),
        (
            "Kyoto",
            {"latitude": 52.5244, "foo": None},
            CoordinatesSettingError,
        ),
        (
            "Kansas City",
            {"foo": "bad_value", "longitude": 32.2},
            CoordinatesSettingError,
        ),
        (
            "Daytona",
            {"latitude": 52.5244, "foo": "bad_value"},
            CoordinatesSettingError,
        ),
    ],
)
def test_set_coordinates_invalid_coordinates_raises_coordinates_setting_error(
    monkeypatch: pytest.MonkeyPatch, mock_city, mock_bad_data, expected_error
) -> None:
    geocoding_client = get_geocoding_client()

    mock_response = AsyncMock(return_value={"results": [mock_bad_data]})
    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    with pytest.raises(expected_exception=CoordinatesSettingError) as err:
        asyncio.run(geocoding_client.set_coordinates(mock_city))
    assert isinstance(err.value, expected_error)


# =============================================
# ******* Tests for 'get_coordinates' ******** |  TESTING COMPLETE : 07/08/26
# =============================================
# NOTE: Tests 'happy path' in which 'self.coordinates' is of Coordinate type
@pytest.mark.parametrize(
    argnames="mock_city, mock_latitude, mock_longitude",
    argvalues=[("Miami", 0, 0)],
)
def test_get_coordinates_valid_coordinates(
    monkeypatch, mock_city, mock_latitude, mock_longitude
):
    geocoding_client = get_geocoding_client()

    mock_make_request = AsyncMock(
        return_value={
            "results": [{"latitude": mock_latitude, "longitude": mock_longitude}]
        }
    )
    monkeypatch.setattr(HttpApiClient, "make_request", mock_make_request)
    asyncio.run(geocoding_client.set_coordinates(mock_city))

    result_coordinates = geocoding_client.get_coordinates()
    assert result_coordinates.__class__.__name__ == "Coordinates"
    assert result_coordinates.latitude == mock_latitude
    assert result_coordinates.longitude == mock_longitude


# NOTE: Tests case in which 'self.coordinates' is of type None, which should raise OpenMeteoCoordinatesNotFoundError
def test_get_coordinates_missing_coordinates_raise_coordinates_not_found_error():
    geocoding_client = get_geocoding_client()
    with pytest.raises(OpenMeteoCoordinatesNotFoundError) as err:
        geocoding_client.get_coordinates()
    assert isinstance(err.value, OpenMeteoCoordinatesNotFoundError)
