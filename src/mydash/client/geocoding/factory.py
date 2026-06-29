from .base import GeocodingClient
from .open_meteo import OpenMeteoClient

def get_geocoding_client(provider : str = "open-meteo", **config) -> GeocodingClient:
    if provider == "open-meteo":
        return OpenMeteoClient()
    else:
        raise ValueError(f"Unknown geocoding provider: {provider}")