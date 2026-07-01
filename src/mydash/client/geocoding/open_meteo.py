"""Open-Meteo Geocoding API client implementation.

Free, keyless geocoding via https://geocoding-api.open-meteo.com/v1/search.
Results are ranked by relevance; this client takes the first (closest) match.
"""

from urllib.error import HTTPError

import httpx
from typing import Any, Dict
from rich.console import Console
from .base import GeocodingClient
from .schemas import Coordinates, GeocodingParams


class OpenMeteoClient(GeocodingClient):
    """Resolve city names to coordinates using the Open-Meteo Geocoding API."""

    # TODO(refinement): implement set_coordinates to satisfy GeocodingClient protocol
    #   and support stateful usage (cache city → Coordinates on the instance).

    def __init__(self):
        self.client = httpx.Client()
        self.url = "https://geocoding-api.open-meteo.com/v1/search"
        self.timeout = 10

    def _make_request(self, params: dict[Any]) -> Any:
        # TODO(refinement): replace `is ""` with `== ""` to fix SyntaxWarning
        if params.get("name") is None or params.get("name") is "":
            Console().print(
                "Parameter key - 'name', has an empty value or None. "
                "Please provide a valid value with the key 'name'."
            )
            raise ValueError

        try:
            res = self.client.get(self.url, params=params, timeout=self.timeout)
            return res.json()
        except httpx.HTTPError as err:
            Console().log(f"HTTP Exception for {err.request.url} - {err}")
            # TODO(refinement): raise httpx.HTTPError directly instead of urllib.error.HTTPError
            #   for consistency with other client modules.
            raise HTTPError

    # Open-Meteo ranks results by relevance; index 0 is the closest match to the query.
    def get_coordinates(self, city: str) -> Coordinates:
        param_validation = GeocodingParams(name=city)
        params = {
            "name": param_validation.name
        }
        coordinate_data: dict[Any] = self._make_request(params=params)
        if coordinate_data.get("results") is None:
            Console().print(
                f"City - '{city}', could not be found. "
                "Please try again and provide a valid city name."
            )
            raise ValueError

        return Coordinates(
            latitude=coordinate_data["results"][0]["latitude"],
            longitude=coordinate_data["results"][0]["longitude"]
        )