class GeocodingClientError(Exception): ...


class CoordinatesNotFoundError(GeocodingClientError): ...


class CityNotFoundError(GeocodingClientError): ...


class GeocodingFactoryError(Exception):
    def __init__(self, provider: str):
        super().__init__(
            f"Unknown Provider: {provider}. Please choose a valid provider"
        )
