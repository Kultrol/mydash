from mydash.client.weather.base_errors import WeatherClientError


class OpenMeteoWeatherError(WeatherClientError): ...


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
