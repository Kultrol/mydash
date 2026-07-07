class WeatherClientError(Exception): ...


class WeatherFactoryError(Exception):
    def __init__(self, provider: str):
        super().__init__(
            f"Unknown Provider: {provider}. Please choose a valid provider"
        )
