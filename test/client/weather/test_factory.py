"""Tests for mydash.client.weather.factory.

Target: get_weather_client(provider, **config)
Strategy: direct instantiation checks; no HTTP mocking needed.
"""

# --- Factory ---
#
# TODO(testing): default/no provider returns OpenMeteoClient instance —
#   assert isinstance(get_weather_client(), OpenMeteoClient)
#
# TODO(testing): unknown provider raises ValueError — parametrize invalid names