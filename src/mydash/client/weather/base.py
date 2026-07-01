"""Weather client protocol.

Clients follow a two-phase pattern: ``set_*`` methods fetch and cache data from
the provider; ``get_*`` methods return the cached result without making new requests.
"""

from abc import abstractmethod
from typing import Protocol, runtime_checkable, Any

from mydash.client.weather.schemas import MultiDayForecast


@runtime_checkable
class WeatherClient(Protocol):
    """Protocol for weather forecast providers.

    Typical usage:
        1. Set coordinates (via ``set_coordinates`` on the concrete client).
        2. Call ``set_weather_forecast(forecast_length)`` to fetch and parse data.
        3. Call ``get_weather_forecast()`` to read the cached :class:`MultiDayForecast`.
    """

    @abstractmethod
    def _make_request(self, params) -> Any:
        """Send an HTTP request to the provider API.

        :param params: Query parameters dict forwarded to the provider.
        :return: Parsed JSON response body.
        """
        ...

    @abstractmethod
    def set_weather_forecast(self, forecast_length: int = 0) -> None:
        """Fetch and cache an hourly forecast for the configured number of days.

        :param forecast_length: Number of forecast days to request from the provider.
        """
        ...

    @abstractmethod
    def get_weather_forecast(self) -> MultiDayForecast:
        """Return the forecast cached by the most recent ``set_weather_forecast`` call."""
        ...