"""Open-Meteo Geocoding API client implementation.

Free, keyless geocoding via https://geocoding-api.open-meteo.com/v1/search.
Results come back ranked by relevance and are returned in that order, so the
caller can show a person the choice between two same-named towns.

Answers are cached for a month — cities do not move.
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from mydash.client.geocoding.base import DEFAULT_RESULT_LIMIT, GeocodingClient
from mydash.client.geocoding.providers.open_meteo.errors import (
    OpenMeteoCityNotFoundError,
    OpenMeteoResponseError,
    ParameterSettingError,
)
from mydash.client.http_api.http_api import HttpApiClient
from mydash.models.geocoding import Coordinates, Place
from mydash.storage.cache import TTL

SEARCH_URL = httpx.URL("https://geocoding-api.open-meteo.com/v1/search")
#: Open-Meteo rejects counts outside this range.
MAX_RESULT_LIMIT = 100


class OpenMeteoParams(BaseModel):
    """Validated query parameters for the Open-Meteo Geocoding search endpoint."""

    name: str = Field(min_length=1)
    count: int = Field(default=DEFAULT_RESULT_LIMIT, ge=1, le=MAX_RESULT_LIMIT)
    language: str = "en"
    format: str = "json"

    def to_params(self) -> dict[str, Any]:
        """Build the flat query-parameter dict for the HTTP client."""
        return self.model_dump()


class OpenMeteoClient(GeocodingClient):
    """Resolve city names to ranked places using the Open-Meteo Geocoding API."""

    def __init__(self, http_client: HttpApiClient | None = None) -> None:
        """Build the client.

        :param http_client: Shared HTTP client; one is created per instance
            when omitted.
        """
        self.url = SEARCH_URL
        self.http_client = http_client if http_client is not None else HttpApiClient()

    async def search(
        self, city: str, *, limit: int = DEFAULT_RESULT_LIMIT
    ) -> list[Place]:
        """Return places matching *city*, best match first.

        :param city: Place name to look up.
        :param limit: Maximum matches to return.
        :raises ParameterSettingError: If *city* or *limit* is unusable.
        :raises OpenMeteoCityNotFoundError: If nothing matched.
        :raises OpenMeteoResponseError: If the response shape is unusable.
        """
        try:
            params = OpenMeteoParams(name=city.strip(), count=limit)
        except ValidationError as err:
            raise ParameterSettingError(err) from err

        response = await self.http_client.make_request(
            url=self.url,
            request_method="GET",
            parameters=params.to_params(),
            cache_ttl=TTL["geocoding"],
        )

        raw_results = response.get("results")
        if not raw_results:
            raise OpenMeteoCityNotFoundError(params.name, response)
        if not isinstance(raw_results, list):
            raise OpenMeteoResponseError(
                message="Received malformed data from Open-Meteo API",
                details=raw_results,
            )

        # Skip individual results that are missing coordinates rather than
        # discarding a whole page of otherwise good matches.
        places = [
            place
            for place in (_parse_place(result) for result in raw_results)
            if place is not None
        ]
        if not places:
            raise OpenMeteoResponseError(
                message=f"No usable coordinates in Open-Meteo results for {city!r}",
                details=raw_results,
            )
        return places


def _parse_place(result: Any) -> Place | None:
    """Convert one raw Open-Meteo result into a :class:`Place`, or ``None``."""
    if not isinstance(result, dict):
        return None
    try:
        coordinates = Coordinates(
            latitude=result["latitude"], longitude=result["longitude"]
        )
        return Place(
            name=result.get("name") or "",
            coordinates=coordinates,
            country=result.get("country"),
            country_code=result.get("country_code"),
            region=result.get("admin1"),
            timezone=result.get("timezone"),
            population=result.get("population"),
        )
    except (KeyError, TypeError, ValidationError):
        return None
