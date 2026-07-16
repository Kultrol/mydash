from pydantic import ValidationError

from mydash.core.client.weather.base_errors import WeatherClientError


class OpenMeteoWeatherError(WeatherClientError): ...


class CoordinateSettingError(OpenMeteoWeatherError):
    def __init__(self, invalid_input):
        super().__init__(
            f"Invalid input provided - {type(invalid_input)}, could not set coordinates. Input should be of type - Coordinates."
        )


class ParameterSettingError(OpenMeteoWeatherError):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set parameters. Error occured: {validation_err.errors}"
        )


class MissingCoordinatesError(OpenMeteoWeatherError):
    def __init__(self):
        super().__init__(
            "Coordinates not found. Coordinates must be set before fetching a weather forecast by using 'set_coordinates' method."
        )


class MissingWeatherForecastError(OpenMeteoWeatherError):
    def __init__(self):
        super().__init__(
            "Weather Forecast not found. Must fetch weather forecast by calling 'set_weather_forecast'."
        )


class HourForecastSettingError(OpenMeteoWeatherError):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set stock bars. Error occured: {validation_err.errors}"
        )


class DayForecastSettingError(OpenMeteoWeatherError):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set stock bars. Error occured: {validation_err.errors}"
        )


class ResponseError(OpenMeteoWeatherError):
    def __init__(self, query, api_response, error: None | KeyError = None):
        if error is not None:
            super().__init__(
                f"Response error occurred. \n Parameters provided: {query} \n API Response: {api_response} \n\n Error: {error}"
            )
