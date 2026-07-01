"""Tests for mydash.client.geocoding.factory.

Target: get_geocoding_client(provider, **config)
Strategy: direct instantiation checks; no HTTP mocking needed.
"""

# --- Factory ---
#
# TODO(testing): default/no provider returns OpenMeteoClient instance —
#   assert isinstance(get_geocoding_client(), OpenMeteoClient)
#
# TODO(testing): unknown provider raises ValueError — parametrize edge cases:
#   "-", ".", "some_thing", "openMeteo", "fake_provider"