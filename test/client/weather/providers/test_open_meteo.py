"""Tests for mydash.client.weather.open_meteo."""

import pytest

from mydash.client.geocoding.schemas import Coordinates
from mydash.client.weather.factory import get_weather_client
from mydash.client.weather.providers.open_meteo.errors import CoordinateSettingError

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


