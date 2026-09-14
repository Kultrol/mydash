"""Pydantic models for geocoding domain data.

``Coordinates`` is what the weather client needs; ``Place`` is what a person
needs in order to tell two Springfields apart.
"""

from pydantic import BaseModel, Field

from mydash.models.text import CleanStr


class Coordinates(BaseModel):
    """Latitude/longitude pair returned by a geocoding lookup."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Place(BaseModel):
    """One geocoding match, with enough context to disambiguate it.

    Providers rank matches by relevance, so a search returns several of these
    and the caller decides — silently taking the first hit is how you end up
    with the weather for Springfield, Missouri when you meant Illinois.

    The names come from the provider and end up in panel titles and in your
    stored config, so they are :data:`~mydash.models.text.CleanStr`.
    """

    name: CleanStr
    coordinates: Coordinates
    country: CleanStr | None = None
    country_code: CleanStr | None = None
    region: CleanStr | None = None
    timezone: CleanStr | None = None
    population: int | None = None

    @property
    def label(self) -> str:
        """Human-readable one-liner, e.g. ``Springfield, Illinois, United States``."""
        parts = [self.name, self.region, self.country]
        return ", ".join(part for part in parts if part)
