"""Geocoding client protocol.

Defines the contract for resolving human-readable place names to coordinates.
Downstream weather clients consume :class:`~mydash.core.models.geocoding.Coordinates`.
"""

from abc import abstractmethod
from typing import Protocol

import httpx

from mydash.core.models.geocoding import Coordinates


class GeocodingClient(Protocol):
    """Protocol for geocoding providers.

    Supports two usage styles:
        - Stateless: call ``get_coordinates(city)`` directly (current Open-Meteo impl).
        - Stateful: call ``set_coordinates(city)`` then read cached result (not yet
          implemented on all providers).
    """

    @abstractmethod
    def __init__(self) -> None:
        self.url: httpx.URL
        self.coordinates: Coordinates | None

    @abstractmethod
    async def set_coordinates(self, city: str) -> None:
        """Resolve and cache coordinates for *city* on the client instance.

        :param city: Human-readable place name (e.g. "Miami").
        """

    def get_coordinates(self) -> Coordinates:
        """Return coordinates cached by the most recent ``set_coordinates`` call.

        :return: Validated :class:`Coordinates` for the best-matching result.
        """
        ...
