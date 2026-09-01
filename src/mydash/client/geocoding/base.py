"""Geocoding client protocol.

One call in, ranked matches out. Downstream weather clients consume the
:class:`~mydash.models.geocoding.Coordinates` on the chosen
:class:`~mydash.models.geocoding.Place`.
"""

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from mydash.models.geocoding import Place

#: Matches requested when the caller does not say otherwise.
DEFAULT_RESULT_LIMIT = 5


@runtime_checkable
class GeocodingClient(Protocol):
    """Protocol for geocoding providers."""

    @abstractmethod
    async def search(
        self, city: str, *, limit: int = DEFAULT_RESULT_LIMIT
    ) -> list[Place]:
        """Resolve *city* to ranked candidate places.

        :param city: Human-readable place name (e.g. "Miami").
        :param limit: Maximum matches to return, best first.
        :returns: At least one place; providers raise when nothing matches.
        :raises CityNotFoundError: If the provider has no match for *city*.
        """
        ...
