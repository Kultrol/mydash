from mydash.client.geocoding.base_errors import (
    CityNotFoundError,
    CoordinatesNotFoundError,
    GeocodingClientError,
)


class OpenMeteoClientError(GeocodingClientError): ...


class OpenMeteoCityNotFoundError(OpenMeteoClientError, CityNotFoundError):
    def __init__(self, city):
        super().__init__(
            f"City - '{city}', could not be found. "
            "Please try again and provide a valid city name."
        )


class OpenMeteoCoordinatesNotFoundError(OpenMeteoClientError, CoordinatesNotFoundError):
    def __init__(self, coordinates):
        super().__init__(
            f"Coordinates not found. Current coordinate:  type:{type(coordinates)!r}, value:{coordinates!r}"
        )
