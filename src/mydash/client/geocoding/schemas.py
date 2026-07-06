"""Pydantic models for geocoding domain data.

``Coordinates`` is shared with the weather client — set them on a weather client
via ``set_coordinates`` before fetching a forecast.
"""

from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    """Latitude/longitude pair returned by a geocoding lookup."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-90, le=90)
