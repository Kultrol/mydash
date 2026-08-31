"""Open-Meteo Forecast API query parameter models.

Maps domain inputs (coordinates, day ranges, unit presets) to the query dict
accepted by ``HttpApiClient.make_request``. Unit presets follow Open-Meteo
docs: temperature, wind speed, and precipitation move together.
"""

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

DailyVariable = Literal[
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
    "sunrise",
    "sunset",
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

# Whole-day figures the hourly series cannot give us: today's range, the
# rain outlook, and daylight.
DEFAULT_DAILY: list[DailyVariable] = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
    "sunrise",
    "sunset",
]

# High-level presets → Open-Meteo temperature / wind / precipitation query params.
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
    """Validated Open-Meteo forecast query parameters."""

    coordinates: Coordinates
    hourly: list[HourlyVariable] = Field(default_factory=lambda: list(DEFAULT_HOURLY))
    daily: list[DailyVariable] = Field(default_factory=lambda: list(DEFAULT_DAILY))
    past_days: int = Field(default=0, ge=0, le=3)
    forecast_days: int = Field(default=1, ge=1, le=16)
    temperature_unit: TemperatureUnit = "celsius"
    wind_speed_unit: WindSpeedUnit = "kmh"
    precipitation_unit: PrecipitationUnit = "mm"
    # "auto" asks Open-Meteo to timestamp the series in the location's own
    # timezone, so "the next six hours" means six hours *there*.
    timezone: str = "auto"

    def to_params(self) -> dict[str, Any]:
        """Build the flat query-parameter dict for the HTTP client."""
        return {
            "latitude": self.coordinates.latitude,
            "longitude": self.coordinates.longitude,
            "hourly": ",".join(self.hourly),
            "daily": ",".join(self.daily),
            "past_days": self.past_days,
            "forecast_days": self.forecast_days,
            "temperature_unit": self.temperature_unit,
            "wind_speed_unit": self.wind_speed_unit,
            "precipitation_unit": self.precipitation_unit,
            "timezone": self.timezone,
        }
