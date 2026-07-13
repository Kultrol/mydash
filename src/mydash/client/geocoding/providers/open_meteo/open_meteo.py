"""Open-Meteo Geocoding API client implementation.

Free, keyless geocoding via https://geocoding-api.open-meteo.com/v1/search.
Results are ranked by relevance; this client takes the first (closest) match.
"""

from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from mydash.client.geocoding.base import GeocodingClient
from mydash.client.geocoding.providers.open_meteo.errors import (
    CoordinatesSettingError,
    OpenMeteoCityNotFoundError,
    OpenMeteoCoordinatesNotFoundError,
    OpenMeteoResponseError,
    ParameterSettingError,
)
from mydash.models.geocoding import Coordinates
from mydash.client.http_api.http_api import HttpApiClient


# Open-Meteo's Geocoding API is mature, so its query parameters are modeled here
# and expected to remain stable across API versions.
class OpenMeteoParams(BaseModel):
    """Validated query parameters for the Open-Meteo Geocoding search endpoint."""

    name: str = ""


class OpenMeteoResponse(BaseModel):
    """Validated response for the Open-Meteo Geocoding search endpoint"""

    results: list[dict[str, Any]]


class OpenMeteoClient(GeocodingClient):
    """Resolve city names to coordinates using the Open-Meteo Geocoding API."""

    def __init__(self):
        self.url = httpx.URL("https://geocoding-api.open-meteo.com/v1/search")
        self.coordinates: Coordinates | None = None

    def set_coordinates(self, city: str) -> None:
        """Resolve and cache coordinates for *city* on this client instance."""

        try:
            params = OpenMeteoParams(name=city)
        except ValidationError as err:
            raise ParameterSettingError(err)

        api_response = HttpApiClient().make_request(
            url=self.url, request_method="GET", parameters=params.model_dump()
        )

        raw_results = api_response.get("results", None)

        if not raw_results:
            raise OpenMeteoCityNotFoundError(params.name, api_response)

        # Tries to validate that raw_results is of type list[Dict[str,Any]]
        try:
            response = OpenMeteoResponse(results=raw_results)
        except ValidationError as err:
            raise OpenMeteoResponseError(
                message="Received malformed data from Open-Meteo API",
                details=err.errors(),
            )

        coordinate_data = response.results[0]

        try:
            self.coordinates = Coordinates.model_validate(
                {
                    "latitude": coordinate_data.get("latitude"),
                    "longitude": coordinate_data.get("longitude"),
                }
            )
        except ValidationError as err:
            raise CoordinatesSettingError(err)

    # Open-Meteo ranks results by relevance; index 0 is the closest match to the query.
    def get_coordinates(self) -> Coordinates:
        if self.coordinates is not None:
            return self.coordinates
        else:
            raise OpenMeteoCoordinatesNotFoundError(coordinates=self.coordinates)
