"""Open-Meteo Geocoding API client implementation.

Free, keyless geocoding via https://geocoding-api.open-meteo.com/v1/search.
Results are ranked by relevance; this client takes the first (closest) match.
"""

import httpx
from pydantic import BaseModel, ValidationError

from mydash.client.geocoding.base import GeocodingClient
from mydash.client.geocoding.providers.open_meteo.errors import (
    CoordinatesSettingError,
    OpenMeteoCityNotFoundError,
    OpenMeteoCoordinatesNotFoundError,
    ParameterSettingError,
)
from mydash.client.geocoding.schemas import Coordinates
from mydash.client.http_api.http_api import HttpApiClient


# Open-Meteo's Geocoding API is mature, so its query parameters are modeled here
# and expected to remain stable across API versions.
class OpenMeteoParams(BaseModel):
    """Validated query parameters for the Open-Meteo Geocoding search endpoint."""

    name: str = ""


class OpenMeteoClient(GeocodingClient):
    """Resolve city names to coordinates using the Open-Meteo Geocoding API."""

    def __init__(self):
        self.url = httpx.URL("https://geocoding-api.open-meteo.com/v1/search")
        self.coordinates: Coordinates | None = None

    def set_coordinates(self, city: str) -> None:
        """Resolve and cache coordinates for *city* on this client instance."""

        # Validating Parameter Values
        try:
            params = OpenMeteoParams(
                name=city
            )  # Pydantic OpenMeteo parameter validation
        except ValidationError as err:
            raise ParameterSettingError(err)

        # Creating an HttpApiClient and making a request to the api.
        coordinate_data = HttpApiClient().make_request(
            url=self.url, request_method="GET", parameters=params.model_dump()
        )

        # Handles case in which the response does not return expected results.
        if coordinate_data.get("results") is None:
            raise OpenMeteoCityNotFoundError(params.name)

        # Validating Coordinates
        try:
            self.coordinates = Coordinates(
                latitude=coordinate_data["results"][0]["latitude"],
                longitude=coordinate_data["results"][0]["longitude"],
            )
        except ValidationError as err:
            raise CoordinatesSettingError(err)

    # Open-Meteo ranks results by relevance; index 0 is the closest match to the query.
    def get_coordinates(self) -> Coordinates:
        if self.coordinates is not None:
            return self.coordinates
        else:
            raise OpenMeteoCoordinatesNotFoundError(coordinates=self.coordinates)
