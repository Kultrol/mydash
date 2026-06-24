
from .base import WeatherClient
from .open_meteo import OpenMeteoClient

def get_weather_client(provider : str = "open-meteo", **config) -> WeatherClient:
    if provider == "open-meteo":
        return OpenMeteoClient()
    else:
        raise ValueError(f"Unknown weather provider: {provider}") 