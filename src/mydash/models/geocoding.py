"""Pydantic models for geocoding domain data.

``Coordinates`` is what the weather client needs; ``Place`` is what a person
needs in order to tell two Springfields apart.
"""

from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    """Latitude/longitude pair returned by a geocoding lookup."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Place(BaseModel):
    """One geocoding match, with enough context to disambiguate it.

    Providers rank matches by relevance, so a search returns several of these
    and the caller decides — silently taking the first hit is how you end up
    with the weather for Springfield, Missouri when you meant Illinois.
    """

    name: str
    coordinates: Coordinates
    country: str | None = None
    country_code: str | None = None
    region: str | None = None
    timezone: str | None = None
    population: int | None = None

    @property
    def label(self) -> str:
        """Human-readable one-liner, e.g. ``Springfield, Illinois, United States``."""
        parts = [self.name, self.region, self.country]
        return ", ".join(part for part in parts if part)
