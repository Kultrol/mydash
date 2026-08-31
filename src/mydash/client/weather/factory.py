"""Factory for weather client instances.

Selects a concrete provider by name. Add new providers here as implementations
are created (e.g. WeatherAPI, OpenWeatherMap).
"""

from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.weather.base import WeatherClient
from mydash.client.weather.base_errors import WeatherFactoryError
from mydash.client.weather.providers.open_meteo.open_meteo import OpenMeteoClient


def get_weather_client(
    provider: str = "open-meteo",
    *,
    http_client: HttpApiClient | None = None,
) -> WeatherClient:
    """Return a weather client for the given *provider*.

    :param provider: Provider identifier. Currently only ``"open-meteo"`` is supported.
    :param http_client: Shared HTTP client to reuse connections and cache.
    :raises WeatherFactoryError: If *provider* is not recognized.
    """
    if provider == "open-meteo":
        return OpenMeteoClient(http_client=http_client)
    raise WeatherFactoryError(provider=provider)
