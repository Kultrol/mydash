"""Weather orchestration: turn a location into a forecast.

The brief already knows its coordinates (they are stored alongside the city),
so the common path makes exactly one request. ``fetch_for_city`` is the
slower path, for a one-off ``--city`` override that has never been geocoded.
"""

from __future__ import annotations

from typing import Literal

from mydash.client.geocoding.base import GeocodingClient
from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.weather.base import WeatherClient
from mydash.client.weather.factory import get_weather_client
from mydash.models.geocoding import Coordinates, Place
from mydash.models.weather import MultiDayForecast

WeatherUnits = Literal["metric", "imperial"]

DEFAULT_FORECAST_DAYS = 2


class WeatherService:
    """Fetch forecasts, geocoding first only when coordinates are unknown."""

    def __init__(
        self,
        weather_provider: str = "open-meteo",
        geocoding_provider: str = "open-meteo",
        *,
        http_client: HttpApiClient | None = None,
    ) -> None:
        """Build clients for the given provider names.

        :param weather_provider: Weather factory key (e.g. ``open-meteo``).
        :param geocoding_provider: Geocoding factory key (e.g. ``open-meteo``).
        :param http_client: Shared HTTP client to reuse connections and cache.
        """
        self.weather_client: WeatherClient = get_weather_client(
            provider=weather_provider, http_client=http_client
        )
        self.geocoding_provider = geocoding_provider
        self.http_client = http_client

    async def fetch_forecast(
        self,
        coordinates: Coordinates,
        *,
        days: int = DEFAULT_FORECAST_DAYS,
        units: WeatherUnits = "metric",
    ) -> MultiDayForecast:
        """Return an hourly forecast for known *coordinates*.

        Two days by default so an evening brief can still show tomorrow
        morning instead of running out of hours at midnight.
        """
        return await self.weather_client.fetch_forecast(
            coordinates, days=days, units=units
        )

    async def fetch_for_city(
        self,
        city: str,
        *,
        days: int = DEFAULT_FORECAST_DAYS,
        units: WeatherUnits = "metric",
    ) -> tuple[Place, MultiDayForecast]:
        """Geocode *city*, then fetch its forecast.

        :returns: The matched place and its forecast, so callers can show
            which "Springfield" they got.
        """
        client: GeocodingClient = get_geocoding_client(
            provider=self.geocoding_provider, http_client=self.http_client
        )
        place = (await client.search(city, limit=1))[0]
        forecast = await self.fetch_forecast(
            place.coordinates, days=days, units=units
        )
        return place, forecast
