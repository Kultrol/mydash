"""Tests for the Open-Meteo geocoding provider.

Strategy: inject a FakeHttpClient (see test/conftest.py) so parsing, ranking,
and error mapping are tested without HTTP.
"""

import asyncio

import pytest

from mydash.client.geocoding.base_errors import (
    CityNotFoundError,
    GeocodingClientError,
)
from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.geocoding.providers.open_meteo.errors import (
    OpenMeteoCityNotFoundError,
    OpenMeteoResponseError,
    ParameterSettingError,
)
from mydash.client.geocoding.providers.open_meteo.open_meteo import OpenMeteoClient
from mydash.models.geocoding import Place
from mydash.storage.cache import TTL
from test.conftest import FakeHttpClient


def _result(name="Miami", latitude=25.7617, longitude=-80.1918, **extra):
    return {
        "name": name,
        "latitude": latitude,
        "longitude": longitude,
        "country": "United States",
        "country_code": "US",
        "admin1": "Florida",
        "timezone": "America/New_York",
        "population": 441003,
        **extra,
    }


def _search(http, city="Miami", **kwargs):
    return asyncio.run(OpenMeteoClient(http_client=http).search(city, **kwargs))


# --- happy path -----------------------------------------------------------


def test_search_returns_parsed_places():
    http = FakeHttpClient({"results": [_result()]})

    places = _search(http)

    assert len(places) == 1
    place = places[0]
    assert isinstance(place, Place)
    assert place.name == "Miami"
    assert place.coordinates.latitude == 25.7617
    assert place.coordinates.longitude == -80.1918
    assert place.country == "United States"
    assert place.country_code == "US"
    assert place.region == "Florida"
    assert place.timezone == "America/New_York"
    assert place.population == 441003


def test_search_preserves_provider_ranking():
    http = FakeHttpClient(
        {
            "results": [
                _result(
                    name="Springfield",
                    admin1="Missouri",
                    latitude=37.2,
                    longitude=-93.3,
                ),
                _result(
                    name="Springfield",
                    admin1="Illinois",
                    latitude=39.8,
                    longitude=-89.6,
                ),
            ]
        }
    )

    places = _search(http, "Springfield")

    assert [place.region for place in places] == ["Missouri", "Illinois"]


def test_place_label_reads_as_a_sentence():
    http = FakeHttpClient({"results": [_result()]})

    assert _search(http)[0].label == "Miami, Florida, United States"


def test_place_label_skips_missing_parts():
    http = FakeHttpClient({"results": [_result(admin1=None, country=None)]})

    assert _search(http)[0].label == "Miami"


def test_search_sends_query_parameters_and_caches():
    http = FakeHttpClient({"results": [_result()]})

    _search(http, "  Miami  ", limit=3)

    params = http.parameters()
    assert params["name"] == "Miami"
    assert params["count"] == 3
    assert params["format"] == "json"
    assert http.calls[0]["cache_ttl"] == TTL["geocoding"]


def test_search_defaults_to_five_results():
    http = FakeHttpClient({"results": [_result()]})

    _search(http)

    assert http.parameters()["count"] == 5


# --- resilient parsing ----------------------------------------------------


def test_results_without_coordinates_are_skipped():
    http = FakeHttpClient(
        {
            "results": [
                {"name": "No coordinates here"},
                _result(name="Miami"),
            ]
        }
    )

    places = _search(http)

    assert [place.name for place in places] == ["Miami"]


def test_results_with_out_of_range_coordinates_are_skipped():
    http = FakeHttpClient(
        {"results": [_result(latitude=999), _result(name="Miami")]}
    )

    assert [place.name for place in _search(http)] == ["Miami"]


def test_all_results_unusable_raises_response_error():
    http = FakeHttpClient({"results": [{"name": "nothing usable"}]})

    with pytest.raises(OpenMeteoResponseError):
        _search(http)


def test_non_list_results_raise_response_error():
    http = FakeHttpClient({"results": {"name": "Miami"}})

    with pytest.raises(OpenMeteoResponseError):
        _search(http)


# --- error paths ----------------------------------------------------------


@pytest.mark.parametrize("payload", [{}, {"results": []}, {"results": None}])
def test_no_matches_raise_city_not_found(payload):
    http = FakeHttpClient(payload)

    with pytest.raises(OpenMeteoCityNotFoundError) as err:
        _search(http, "Nowheresville")

    assert err.value.query == "Nowheresville"
    assert isinstance(err.value, CityNotFoundError)
    assert isinstance(err.value, GeocodingClientError)


@pytest.mark.parametrize("city", ["", "   "])
def test_blank_city_raises_parameter_setting_error(city):
    http = FakeHttpClient()

    with pytest.raises(ParameterSettingError):
        _search(http, city)


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_out_of_range_limit_raises_parameter_setting_error(limit):
    http = FakeHttpClient()

    with pytest.raises(ParameterSettingError):
        _search(http, limit=limit)


def test_http_errors_propagate():
    http = FakeHttpClient(RuntimeError("network down"))

    with pytest.raises(RuntimeError, match="network down"):
        _search(http)


# --- factory wiring -------------------------------------------------------


def test_factory_passes_the_shared_http_client_through():
    http = FakeHttpClient({"results": [_result()]})
    client = get_geocoding_client("open-meteo", http_client=http)

    assert client.http_client is http
    assert asyncio.run(client.search("Miami"))[0].name == "Miami"
