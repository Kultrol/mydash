import httpx
from typing import Any
from rich.console import Console
from .base import GeocodingClient
from .schemas import Coordinates


class OpenMeteoClient(GeocodingClient):

        def __init__(self):
            self.client = httpx.Client()
            self.url = "https://geocoding-api.open-meteo.com/v1/search"
            self.timeout = 10

        def _make_request(self, params) -> Any:
            try:
                res = self.client.get(self.url, params = params, timeout=self.timeout)
                res.raise_for_status()
                return res.json()
            except httpx.HTTPError as err:
                Console().log(f"HTTP Exception for {err.request.url} - {err}")

        def get_coordinates(self, city: str) -> Coordinates:
            params = {"name" : city.lower()}
            coordinate_data = self._make_request(params=params)
            return Coordinates(
                latitude= coordinate_data["results"][0]["latitude"],
                longitude= coordinate_data["results"][0]["longitude"]
            )
