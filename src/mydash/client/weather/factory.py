"""Factory for weather client instances.

Selects a concrete provider by name. Add new providers here as implementations
are created (e.g. WeatherAPI, OpenWeatherMap).
"""

from .base import WeatherClient
from .open_meteo import OpenMeteoClient


def get_weather_client(provider: str = "open-meteo", **config) -> WeatherClient:
    """Return a weather client for the given *provider*.

    :param provider: Provider identifier. Currently only ``"open-meteo"`` is supported.
    :param config: Reserved for future provider-specific configuration.
    :raises ValueError: If *provider* is not recognized.
    """
    if provider == "open-meteo":
        return OpenMeteoClient()
    else:
        raise ValueError(f"Unknown weather provider: {provider}")