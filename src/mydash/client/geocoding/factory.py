"""Factory for geocoding client instances.

Selects a concrete provider implementation by name.
"""

from mydash.client.geocoding.base import GeocodingClient
from mydash.client.geocoding.base_errors import GeocodingFactoryError
from mydash.client.geocoding.providers.open_meteo.open_meteo import OpenMeteoClient
from mydash.client.http_api.http_api import HttpApiClient


def get_geocoding_client(
    provider: str = "open-meteo",
    *,
    http_client: HttpApiClient | None = None,
) -> GeocodingClient:
    """Return a geocoding client for the given *provider*.

    :param provider: Provider identifier. Currently only ``"open-meteo"`` is supported.
    :param http_client: Shared HTTP client to reuse connections and cache.
    :raises GeocodingFactoryError: If *provider* is not recognized.
    """
    if provider == "open-meteo":
        return OpenMeteoClient(http_client=http_client)
    raise GeocodingFactoryError(provider=provider)
