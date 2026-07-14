from typing import Any, Literal

from pydantic import BaseModel, Field

from mydash.models.geocoding import Coordinates

HourlyVariable = Literal[
    "temperature_2m",
    "apparent_temperature",
    "precipitation_probability",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "uv_index",
]

TemperatureUnit = Literal["celsius", "fahrenheit"]
WindSpeedUnit = Literal["kmh", "ms", "mph", "kn"]
PrecipitationUnit = Literal["mm", "inch"]
WeatherUnitsPreset = Literal["metric", "imperial"]

DEFAULT_HOURLY: list[HourlyVariable] = [
    "temperature_2m",
    "apparent_temperature",
    "precipitation_probability",
    "precipitation",
    "weather_code",
    "cloud_cover",
    "wind_speed_10m",
    "uv_index",
]

UNITS_PRESETS: dict[WeatherUnitsPreset, dict[str, str]] = {
    "metric": {
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    },
    "imperial": {
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
    },
}


class Parameters(BaseModel):
    coordinates: Coordinates
    hourly: list[HourlyVariable] = Field(default_factory=lambda: list(DEFAULT_HOURLY))
    past_days: int = Field(default=1, ge=0, le=3)
    forecast_days: int = Field(default=1, ge=1, le=92)
    temperature_unit: TemperatureUnit = "celsius"
    wind_speed_unit: WindSpeedUnit = "kmh"
    precipitation_unit: PrecipitationUnit = "mm"

    def to_params(self) -> dict[str, Any]:
        return {
            "latitude": self.coordinates.latitude,
            "longitude": self.coordinates.longitude,
            "hourly": self.hourly,
            "past_days": self.past_days,
            "forecast_days": self.forecast_days,
            "temperature_unit": self.temperature_unit,
            "wind_speed_unit": self.wind_speed_unit,
            "precipitation_unit": self.precipitation_unit,
        }
