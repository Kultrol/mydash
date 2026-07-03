"""Open-Meteo Geocoding API client implementation.

Free, keyless geocoding via https://geocoding-api.open-meteo.com/v1/search.
Results are ranked by relevance; this client takes the first (closest) match.
"""

from typing import Any

import httpx
from pydantic import BaseModel
from rich.console import Console

from .base import GeocodingClient
from .schemas import Coordinates


# Open-Meteo's Geocoding API is mature, so its query parameters are modeled here
# and expected to remain stable across API versions.
class OpenMeteoParams(BaseModel):
    """Validated query parameters for the Open-Meteo Geocoding search endpoint."""

    name: str = ""


class OpenMeteoClient(GeocodingClient):
    """Resolve city names to coordinates using the Open-Meteo Geocoding API."""

    def __init__(self):
        self.client = httpx.Client()
        self.url = httpx.URL("https://geocoding-api.open-meteo.com/v1/search")
        self.timeout = 10
        self.coordinates: Coordinates = Coordinates(latitude=0, longitude=0)

    def _make_request(self, params: dict[Any, Any]) -> Any:
        if params.get("name") is None or params.get("name") == "":
            Console().print(
                "Parameter key - 'name', has an empty value or None. "
                "Please provide a valid value with the key 'name'."
            )
            raise ValueError

        try:
            res = self.client.get(self.url, params=params, timeout=self.timeout)
            res.raise_for_status()
            return res.json()
        except httpx.HTTPStatusError as err:
            Console().print(f"Status Error occured: {err.response.status_code}")
            raise err
        except httpx.HTTPError as err:
            raise err
        except Exception as err:
            raise err

    def set_coordinates(self, city: str) -> None:
        """Resolve and cache coordinates for *city* on this client instance."""
        param_validation = OpenMeteoParams(name=city)
        coordinate_data = self._make_request(params=param_validation.model_dump())
        if coordinate_data.get("results") is None:
            Console().print(
                f"City - '{city}', could not be found. "
                "Please try again and provide a valid city name."
            )
            raise ValueError

        self.coordinates = Coordinates(
            latitude=coordinate_data["results"][0]["latitude"],
            longitude=coordinate_data["results"][0]["longitude"],
        )

    # Open-Meteo ranks results by relevance; index 0 is the closest match to the query.
    def get_coordinates(self) -> Coordinates:
        return self.coordinates
