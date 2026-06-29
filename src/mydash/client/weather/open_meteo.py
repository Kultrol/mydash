from typing import Any

from .base import WeatherClient
from src.mydash.client.geocoding.schemas import Coordinates
from .schemas import MultiDayForecast, DayForecast, HourForecast
from datetime import datetime
from rich.console import Console

import httpx


class OpenMeteoClient(WeatherClient):

    def __init__(self):
        self.client = httpx.Client()
        self.url = "https://api.open-meteo.com/v1/forecast"
        self.timeout = 10

        self.coordinates : Coordinates = None
        self.weather_forecast : MultiDayForecast = None


    def _make_request(self, params) -> Any:
        try:
            res = self.client.get(self.url, params = params, timeout= self.timeout)
            res.raise_for_status()
            return res.json()

        except httpx.HTTPError as err:
            Console().log(f"HTTP Exception for {err.request.url} - {err}")

    def set_coordinates(self, coordinates : Coordinates) -> None:
        self.coordinates : Coordinates = coordinates

    def set_weather_forecast(self, forecast_length: int = 1) -> None:
            params = {
                "latitude": self.coordinates.latitude,
                "longitude": self.coordinates.longitude,
                "hourly": ["temperature_2m", "apparent_temperature", "precipitation_probability", "precipitation",
                           "weather_code", "cloud_cover", "wind_speed_10m", "uv_index"],
                "past_days": 1,
                "forecast_days": forecast_length,
            }

            #Calling the api with parameters
            weather_data = self._make_request(params)


            current_day = DayForecast(month=0, day=0, hours=[])
            weather_forecast: MultiDayForecast = MultiDayForecast(days=[])



            for index in range(0, len(weather_data["hourly"]["time"])):

                #Loading weather data
                hourly_data = weather_data["hourly"]
                time: datetime = datetime.strptime(hourly_data["time"][index], "%Y-%m-%dT%H:%M")
                temperature = hourly_data["temperature_2m"][index]
                feels_like_temperature: float = hourly_data["apparent_temperature"][index]
                cloud_cover: int = hourly_data["cloud_cover"][index]
                wind_speed: float = hourly_data["wind_speed_10m"][index]
                chance_of_rain: int = hourly_data["precipitation_probability"][index]
                amount_of_rain: float = hourly_data["precipitation"][index]
                weather_code: int = hourly_data["weather_code"][index]
                uv_index: float = hourly_data["uv_index"][index]

                #Once a given day forecast has been loaded, i.e. all its hour forecast have been loaded, the 'current_day'
                # resets with a new DayForecast instance.
                if current_day.day != time.day:
                    #Append the previous day forecast before resetting 'current_day' with a new instance.
                    if index != 0:
                        weather_forecast.days.append(current_day)

                    current_day = DayForecast(month=time.month, day=time.day, hours=[])


                #Each hour forecast is loaded and added to the current day forecast
                current_day.hours.append(HourForecast(
                    hour=str(time.hour),
                    temperature=temperature,
                    feels_like_temperature=feels_like_temperature,
                    cloud_cover=cloud_cover,
                    wind_speed=wind_speed,
                    chance_of_rain=chance_of_rain,
                    amount_of_rain=amount_of_rain,
                    weather_code=weather_code,
                    uv_index=uv_index
                ))

            self.weather_forecast = weather_forecast
            return None

    def get_weather_forecast(self) -> MultiDayForecast:
        return self.weather_forecast


