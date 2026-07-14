"""Open-Meteo Forecast API client implementation.

Free, keyless hourly weather via https://api.open-meteo.com/v1/forecast.
Requires coordinates to be set before fetching (typically from the geocoding client).
"""

from datetime import datetime

import httpx
from pydantic import ValidationError

from mydash.models.geocoding import Coordinates
from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.weather.base import WeatherClient
from mydash.client.weather.providers.open_meteo.errors import (
    CoordinateSettingError,
    DayForecastSettingError,
    HourForecastSettingError,
    MissingCoordinatesError,
    MissingWeatherForecastError,
    ParameterSettingError,
    ResponseError,
)
from mydash.client.weather.providers.open_meteo.schemas import (
    UNITS_PRESETS,
    Parameters,
    WeatherUnitsPreset,
)
from mydash.models.weather import DayForecast, HourForecast, MultiDayForecast


class OpenMeteoClient(WeatherClient):
    """Fetch and parse multi-day hourly forecasts from Open-Meteo."""

    def __init__(self):
        self.url = httpx.URL("https://api.open-meteo.com/v1/forecast")
        self.coordinates: Coordinates | None = None
        self.weather_forecast: MultiDayForecast | None = None

    def set_coordinates(self, coordinates: Coordinates) -> None:
        """Store coordinates for subsequent forecast requests."""
        if type(coordinates) is Coordinates:
            self.coordinates = coordinates
        else:
            raise CoordinateSettingError(coordinates)

    def get_coordinates(self) -> Coordinates:
        if self.coordinates is not None:
            return self.coordinates
        else:
            raise MissingCoordinatesError()

    def _validate_weather_forecast_params(
        self,
        coordinates: Coordinates,
        forecast_length: int,
        backwardcast_length: int,
        units: WeatherUnitsPreset = "metric",
    ) -> Parameters:
        if units not in UNITS_PRESETS:
            raise ValueError(
                f"invalid weather units {units!r}; expected one of "
                f"{sorted(UNITS_PRESETS)}"
            )
        unit_fields = UNITS_PRESETS[units]
        try:
            return Parameters(
                coordinates=coordinates,
                forecast_days=forecast_length,
                past_days=backwardcast_length,
                temperature_unit=unit_fields["temperature_unit"],  # type: ignore[arg-type]
                wind_speed_unit=unit_fields["wind_speed_unit"],  # type: ignore[arg-type]
                precipitation_unit=unit_fields["precipitation_unit"],  # type: ignore[arg-type]
            )
        except ValidationError as err:
            raise ParameterSettingError(validation_err=err)

    def set_weather_forecast(
        self,
        forecast_length: int = 1,
        backwardcast_length: int = 1,
        units: WeatherUnitsPreset = "metric",
    ) -> None:

        params = self._validate_weather_forecast_params(
            coordinates=self.get_coordinates(),
            forecast_length=forecast_length,
            backwardcast_length=backwardcast_length,
            units=units,
        )

        weather_data = HttpApiClient().make_request(
            url=self.url, request_method="GET", parameters=params.to_params()
        )

        if not weather_data.get("hourly", None):
            raise ResponseError(query=params, api_response=weather_data)
        else:
            hourly_data = weather_data["hourly"]

        try:
            hourly_time = hourly_data["time"]
        except KeyError as err:
            raise ResponseError(query=params, api_response=hourly_data, error=err)

        current_day = DayForecast(month=0, day=0, hours=[])
        weather_forecast: MultiDayForecast = MultiDayForecast(days=[])

        for index in range(0, len(hourly_time)):
            try:
                time: datetime = datetime.strptime(hourly_time[index], "%Y-%m-%dT%H:%M")
                temperature = hourly_data["temperature_2m"][index]
                feels_like_temperature: float = hourly_data["apparent_temperature"][
                    index
                ]
                cloud_cover: int = hourly_data["cloud_cover"][index]
                wind_speed: float = hourly_data["wind_speed_10m"][index]
                chance_of_rain: int = hourly_data["precipitation_probability"][index]
                amount_of_rain: float = hourly_data["precipitation"][index]
                weather_code: int = hourly_data["weather_code"][index]
                uv_index: float = hourly_data["uv_index"][index]
            except KeyError as err:
                raise ResponseError(query=params, api_response=hourly_data, error=err)

            # When the calendar day changes, finalize the previous day and start a new one.
            if (current_day.day, current_day.month) != (time.day, time.month):
                if index != 0:
                    weather_forecast.days.append(current_day)

                try:
                    current_day = DayForecast(month=time.month, day=time.day, hours=[])
                except ValidationError as err:
                    raise DayForecastSettingError(err)

            try:
                hour_forecast = HourForecast(
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
            except ValidationError as err:
                raise HourForecastSettingError(err)

            current_day.hours.append(hour_forecast)

        weather_forecast.days.append(current_day)
        self.weather_forecast = weather_forecast
        # ----------------------------------------

        return None

    def get_weather_forecast(self) -> MultiDayForecast:
        if self.weather_forecast is None:
            raise MissingWeatherForecastError()
        return self.weather_forecast
