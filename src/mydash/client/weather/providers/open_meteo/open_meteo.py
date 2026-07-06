"""Open-Meteo Forecast API client implementation.

Free, keyless hourly weather via https://api.open-meteo.com/v1/forecast.
Requires coordinates to be set before fetching (typically from the geocoding client).
"""

from datetime import datetime

import httpx

from mydash.client.geocoding.schemas import Coordinates
from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.weather.base import WeatherClient
from mydash.client.weather.providers.open_meteo.schemas import Parameters
from mydash.client.weather.schemas import DayForecast, HourForecast, MultiDayForecast


class OpenMeteoClient(WeatherClient):
    """Fetch and parse multi-day hourly forecasts from Open-Meteo."""

    def __init__(self):
        self.url = httpx.URL("https://api.open-meteo.com/v1/forecast")
        self.coordinates: Coordinates | None = None
        self.weather_forecast: MultiDayForecast | None = None

    def set_coordinates(self, coordinates: Coordinates) -> None:
        """Store coordinates for subsequent forecast requests."""
        self.coordinates = coordinates

    def set_weather_forecast(
        self,
        forecast_length: int = 1,
        backwardcast_length: int = 1,
    ) -> None:
        if self.coordinates is None:
            raise MissingCoordinatesError(
                "Coordinates must be set before fetching a weather forecast."
            )

        params = Parameters(coordinates=self.coordinates)
        weather_data = HttpApiClient().make_request(
            url=self.url, request_method="GET", parameters=params.to_params()
        )

        # ------------------------------------------------
        # Encapsulate the below logic in its own function.
        # ------------------------------------------------
        current_day = DayForecast(month=0, day=0, hours=[])

        weather_forecast: MultiDayForecast = MultiDayForecast(days=[])

        for index in range(0, len(weather_data["hourly"]["time"])):
            hourly_data = weather_data["hourly"]
            time: datetime = datetime.strptime(
                hourly_data["time"][index], "%Y-%m-%dT%H:%M"
            )
            temperature = hourly_data["temperature_2m"][index]
            feels_like_temperature: float = hourly_data["apparent_temperature"][index]
            cloud_cover: int = hourly_data["cloud_cover"][index]
            wind_speed: float = hourly_data["wind_speed_10m"][index]
            chance_of_rain: int = hourly_data["precipitation_probability"][index]
            amount_of_rain: float = hourly_data["precipitation"][index]
            weather_code: int = hourly_data["weather_code"][index]
            uv_index: float = hourly_data["uv_index"][index]

            # When the calendar day changes, finalize the previous day and start a new one.
            if current_day.day != time.day and current_day.month != time.month:
                if index != 0:
                    weather_forecast.days.append(current_day)
                current_day = DayForecast(month=time.month, day=time.day, hours=[])

            current_day.hours.append(
                HourForecast(
                    hour=time.hour,
                    temperature=temperature,
                    feels_like_temperature=feels_like_temperature,
                    cloud_cover=cloud_cover,
                    wind_speed=wind_speed,
                    chance_of_rain=chance_of_rain,
                    amount_of_rain=amount_of_rain,
                    weather_code=weather_code,
                    uv_index=uv_index,
                )
            )

        weather_forecast.days.append(current_day)
        self.weather_forecast = weather_forecast
        # ----------------------------------------

        return None

    def get_weather_forecast(self) -> MultiDayForecast:
        if self.weather_forecast is None:
            raise MissingWeatherForecast(
                "Weather Forecast not found. Must fetch weather forecast by calling 'set_weather_forecast'."
            )
        return self.weather_forecast
