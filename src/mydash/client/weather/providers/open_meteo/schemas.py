from typing import Any, Literal

from pydantic import BaseModel, Field

from mydash.client.geocoding.schemas import Coordinates

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


class Parameters(BaseModel):
    coordinates: Coordinates
    hourly: list[HourlyVariable] = Field(default_factory=lambda: list(DEFAULT_HOURLY))
    past_days: int = Field(default=1, ge=0, le=3)
    forecast_days: int = Field(default=1, ge=1, le=92)

    def to_params(self) -> dict[str, Any]:
        return {
            "latitude": self.coordinates.latitude,
            "longitude": self.coordinates.longitude,
            "hourly": self.hourly,
            "past_days": self.past_days,
            "forecast_days": self.forecast_days,
        }
