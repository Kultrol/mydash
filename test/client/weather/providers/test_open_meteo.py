"""Tests for mydash.client.weather.open_meteo."""

import pytest

from mydash.client.geocoding.schemas import Coordinates
from mydash.client.weather.factory import get_weather_client
from mydash.client.weather.providers.open_meteo.errors import (
    CoordinateSettingError,
    MissingCoordinatesError,
)

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
