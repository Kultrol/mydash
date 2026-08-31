"""Factory for geocoding client instances.

Selects a concrete provider implementation by name.
"""

from mydash.client.geocoding.base import GeocodingClient
from mydash.client.geocoding.base_errors import GeocodingFactoryError
from mydash.client.geocoding.providers.open_meteo.open_meteo import OpenMeteoClient


def get_geocoding_client(provider: str = "open-meteo") -> GeocodingClient:
    """Return a geocoding client for the given *provider*.

    :param provider: Provider identifier. Currently only ``"open-meteo"`` is supported.
    :raises ValueError: If *provider* is not recognized.
    """
    if provider == "open-meteo":
        return OpenMeteoClient()
    else:
        raise GeocodingFactoryError(provider=provider)
