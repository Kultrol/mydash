"""Factory for geocoding client instances.

Selects a concrete provider implementation by name. The ``**config`` kwargs are
reserved for future per-provider settings (API keys, timeouts, base URLs).
"""

from mydash.client.geocoding.base import GeocodingClient
from mydash.client.geocoding.providers.open_meteo import OpenMeteoClient


def get_geocoding_client(provider: str = "open-meteo", **config) -> GeocodingClient:
    """Return a geocoding client for the given *provider*.

    :param provider: Provider identifier. Currently only ``"open-meteo"`` is supported.
    :param config: Reserved for future provider-specific configuration.
    :raises ValueError: If *provider* is not recognized.
    """
    if provider == "open-meteo":
        return OpenMeteoClient()
    else:
        raise ValueError(f"Unknown geocoding provider: {provider}")
