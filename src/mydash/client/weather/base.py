"""Weather client protocol.

Clients follow a two-phase pattern: ``set_*`` methods fetch and cache data from
the provider; ``get_*`` methods return the cached result without making new requests.
"""

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from mydash.models.geocoding import Coordinates
from mydash.models.weather import MultiDayForecast


@runtime_checkable
class WeatherClient(Protocol):
    """Protocol for weather forecast providers.

    Typical usage:
        1. Set coordinates (via ``set_coordinates`` on the concrete client).
        2. Call ``set_weather_forecast(forecast_length)`` to fetch and parse data.
        3. Call ``get_weather_forecast()`` to read the cached :class:`MultiDayForecast`.
    """

    @abstractmethod
    def __init__(self):
        self.coordinates: Coordinates | None

    @abstractmethod
    def set_coordinates(self, coordinates: Coordinates) -> None:
        """Set coordinates provided to the provider API for the weather client

        :params coordinates: Coordinates of the place of interest
        """

    @abstractmethod
    def get_coordinates(self) -> Coordinates:
        """Get coordinates from the weather client"""

    @abstractmethod
    def set_weather_forecast(
        self, forecast_length: int, backwardcast_length: int
    ) -> None:
        """Fetch and cache an hourly forecast for the configured number of days.

        :param forecast_length: Number of forecast days to request from the provider.
        """
        ...

    @abstractmethod
    def get_weather_forecast(self) -> MultiDayForecast:
        """Return the forecast cached by the most recent ``set_weather_forecast`` call."""
        ...
