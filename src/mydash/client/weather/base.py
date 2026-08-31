"""Weather client protocol.

Coordinates in, forecast out. Resolving a place name to coordinates is the
geocoding client's job, so weather clients hold no location state.
"""

from abc import abstractmethod
from typing import Literal, Protocol, runtime_checkable

from mydash.models.geocoding import Coordinates
from mydash.models.weather import MultiDayForecast

WeatherUnits = Literal["metric", "imperial"]


@runtime_checkable
class WeatherClient(Protocol):
    """Protocol for weather forecast providers."""

    @abstractmethod
    async def fetch_forecast(
        self,
        coordinates: Coordinates,
        *,
        days: int = 1,
        past_days: int = 0,
        units: WeatherUnits = "metric",
    ) -> MultiDayForecast:
        """Fetch an hourly forecast for *coordinates*.

        :param coordinates: Location to forecast.
        :param days: Forecast days to request.
        :param past_days: Past days to include.
        :param units: Unit preset — ``metric`` or ``imperial``.
        :returns: Hourly forecast grouped by day, in the location's timezone.
        """
        ...
