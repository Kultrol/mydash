from mydash.client.geocoding.base import GeocodingClient
from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.weather.base import WeatherClient
from mydash.client.weather.factory import get_weather_client
from mydash.models.geocoding import Coordinates
from mydash.services.brief import MultiDayForecast


class WeatherService:
    """Weather Service that orchestrates weather related logic and returns expected weather models."""

    def __init__(
        self,
        weather_provider: str = "open-meteo",
        geocoding_provider: str = "open-meteo",
    ):
        self.weather_client: WeatherClient = get_weather_client(
            provider=weather_provider
        )
        self.geocoding_client: GeocodingClient = get_geocoding_client(
            provider=geocoding_provider
        )

    def fetch_today_weather_forecast(self, city: str) -> MultiDayForecast:
        self.geocoding_client.set_coordinates(city=city)
        coordinates: Coordinates = self.geocoding_client.get_coordinates()
        self.weather_client.set_coordinates(coordinates=coordinates)
        self.weather_client.set_weather_forecast(
            forecast_length=1, backwardcast_length=0
        )
        return self.weather_client.get_weather_forecast()
