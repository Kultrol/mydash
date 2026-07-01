"""Tests for mydash.client.geocoding.open_meteo.

Target: OpenMeteoClient (stateful API)
Usage pattern: set_coordinates(city) fetches and caches; get_coordinates() reads cache.
Strategy: mock client.client.get or patch _make_request; use mock_urls fixture.
Depends on: conftest.mock_urls, conftest.sample_geocoding_response
"""

# --- _make_request / HTTP errors ---
#
# TODO(testing): empty or None "name" param raises ValueError before HTTP call
#
# TODO(testing): HTTP 500 from client.client.get propagates httpx.HTTPError —
#   build httpx.HTTPStatusError with mock_urls["geocoding"]

# --- set_coordinates ---
#
# TODO(testing): valid mocked response caches correct Coordinates on instance —
#   patch _make_request with results array; assert client.coordinates lat/lon
#
# TODO(testing): response with no "results" key raises ValueError —
#   patch _make_request returning {} or {"results": None}

# --- get_coordinates ---
#
# TODO(testing): returns cached Coordinates after set_coordinates (no city arg) —
#   call set_coordinates("Miami") with mocked response, then get_coordinates()

# --- OpenMeteoParams validation ---
#
# TODO(testing): invalid city type (e.g. int) raises ValidationError via
#   OpenMeteoParams pydantic model when passed to set_coordinates