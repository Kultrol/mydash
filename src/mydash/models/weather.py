"""Pydantic models for weather forecast data.

Field names map to Open-Meteo hourly parameters requested in ``OpenMeteoClient``:
    temperature_2m, apparent_temperature, precipitation_probability,
    precipitation, weather_code, cloud_cover, wind_speed_10m, uv_index
"""

from pydantic import BaseModel


class HourForecast(BaseModel):
    """Single-hour weather snapshot within a day."""

    hour: int
    temperature: float
    feels_like_temperature: float
    cloud_cover: int
    wind_speed: float
    chance_of_rain: int
    amount_of_rain: float
    weather_code: int
    uv_index: float


class DayForecast(BaseModel):
    """All hourly forecasts grouped for one calendar day."""

    month: int
    day: int
    hours: list[HourForecast]


class MultiDayForecast(BaseModel):
    """Top-level container returned by ``get_weather_forecast``."""

    days: list[DayForecast]
