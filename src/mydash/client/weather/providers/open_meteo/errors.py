from pydantic import ValidationError

from mydash.client.weather.base_errors import WeatherClientError


class OpenMeteoWeatherError(WeatherClientError): ...


class ParameterSettingError(OpenMeteoWeatherError):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set parameters. Error occured: {validation_err.errors}"
        )


class HourForecastSettingError(OpenMeteoWeatherError):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set hour forecast. Error occured: {validation_err.errors}"
        )


class DayForecastSettingError(OpenMeteoWeatherError):
    def __init__(self, validation_err: ValidationError):
        super().__init__(
            f"Failure to set day forecast. Error occured: {validation_err.errors}"
        )


class ResponseError(OpenMeteoWeatherError):
    def __init__(self, query, api_response, error: Exception | None = None):
        message = (
            f"Response error occurred. \n Parameters provided: {query} "
            f"\n API Response: {api_response}"
        )
        if error is not None:
            message = f"{message} \n\n Error: {error}"
        super().__init__(message)
