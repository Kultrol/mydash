"""Pydantic models for geocoding domain data.

``Coordinates`` is shared with the weather client — set them on a weather client
via ``set_coordinates`` before fetching a forecast.
"""

from pydantic import BaseModel


class Coordinates(BaseModel):
    """Latitude/longitude pair returned by a geocoding lookup."""

    latitude: float
    longitude: float


# Open-Meteo's Geocoding API is mature, so its query parameters are modeled here
# and expected to remain stable across API versions.
class GeocodingParams(BaseModel):
    """Validated query parameters for the Open-Meteo Geocoding search endpoint."""

    name: str = ""