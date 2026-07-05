"""Geocoding client protocol.

Defines the contract for resolving human-readable place names to coordinates.
Downstream weather clients consume :class:`~mydash.client.geocoding.schemas.Coordinates`.
"""

from abc import abstractmethod
from typing import Any, Protocol

import httpx

from mydash.client.geocoding.schemas import Coordinates


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
        self.coordinates: Coordinates

    @abstractmethod
    def set_coordinates(self, city: str) -> None:
        """Resolve and cache coordinates for *city* on the client instance.

        :param city: Human-readable place name (e.g. "Miami").
        """

    def get_coordinates(self) -> Coordinates:
        """Resolve *city* to latitude/longitude without requiring prior ``set_coordinates``.

        :param city: Human-readable place name.
        :return: Validated :class:`Coordinates` for the best-matching result.
        """
        ...
