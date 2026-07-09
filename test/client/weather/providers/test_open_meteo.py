"""Tests for mydash.client.weather.open_meteo.

Target: OpenMeteoClient
Usage pattern: set_coordinates(Coordinates) then set_weather_forecast() then get_weather_forecast()
Strategy: patch _make_request with sample hourly JSON; use Coordinates from geocoding.schemas
Depends on: conftest.sample_hourly_forecast
"""

from unittest.mock import MagicMock

import httpx
import pytest

from mydash.client.weather.factory import get_weather_client


# --- Coordinate guards ---
def test_set_weather_forecast_missing_coordinates_raises_value_error():
    weather_client = get_weather_client()

    with pytest.raises(ValueError) as err:
        weather_client.set_weather_forecast()
    assert isinstance(err.value, ValueError)


def test_get_weather_forecast_missing_coordinates_raises_value_error():
    weather_client = get_weather_client()

    with pytest.raises(ValueError) as err:
        weather_client.get_weather_forecast()
    assert isinstance(err.value, ValueError)


def make_bad_response(status_code: int) -> httpx.Response:
    request = httpx.Request("GET", "https://example.com/some/endpoint")
    return httpx.Response(status_code=status_code, request=request)


@pytest.mark.parametrize(
    argnames="status_code", argvalues=[400, 401, 403, 404, 429, 500, 502, 503]
)
def test__make_request_bad_response_raise_http_status_error(
    monkeypatch: pytest.MonkeyPatch, status_code
) -> None:
    weather_client = get_weather_client()

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = make_bad_response(status_code)

    monkeypatch.setattr(weather_client, "client", mock_client)

    with pytest.raises(httpx.HTTPStatusError) as err:
        weather_client._make_request({})
    assert err.value.response.status_code == status_code, (
        f"Raised:{err.value.response.status_code} and expected: {status_code}"
    )
