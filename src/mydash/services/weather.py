"""Weather orchestration: geocode a city, then fetch today's forecast."""

from typing import Literal

from mydash.client.geocoding.base import GeocodingClient
from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.weather.base import WeatherClient
from mydash.client.weather.factory import get_weather_client
from mydash.models.geocoding import Coordinates
from mydash.models.weather import MultiDayForecast

WeatherUnits = Literal["metric", "imperial"]


class WeatherService:
    """Orchestrate geocoding + weather clients into domain forecast models."""

    def __init__(
        self,
        weather_provider: str = "open-meteo",
        geocoding_provider: str = "open-meteo",
    ):
        """Build clients for the given provider names.

        :param weather_provider: Weather factory key (e.g. ``open-meteo``).
        :param geocoding_provider: Geocoding factory key (e.g. ``open-meteo``).
        """
        self.weather_client: WeatherClient = get_weather_client(
            provider=weather_provider
        )
        self.geocoding_client: GeocodingClient = get_geocoding_client(
            provider=geocoding_provider
        )

    async def fetch_today_weather_forecast(
        self,
        city: str,
        units: WeatherUnits = "metric",
    ) -> MultiDayForecast:
        """Resolve *city* to coordinates and return a one-day hourly forecast.

        Flow: geocode → set weather coordinates → fetch forecast with *units*.

        :param city: Place name for the geocoding client.
        :param units: ``metric`` or ``imperial`` (passed through to the provider).
        :returns: Parsed multi-day container (typically one calendar day).
        """
        await self.geocoding_client.set_coordinates(city=city)
        coordinates: Coordinates = self.geocoding_client.get_coordinates()
        self.weather_client.set_coordinates(coordinates=coordinates)
        await self.weather_client.set_weather_forecast(
            forecast_length=1,
            backwardcast_length=0,
            units=units,
        )
        return self.weather_client.get_weather_forecast()
