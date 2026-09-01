"""News client protocol.

Category in, headlines out — newest first, deduplicated, and capped.
"""

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from mydash.models.news import NewsHeadlines

#: Headlines requested when the caller does not say otherwise.
DEFAULT_HEADLINE_LIMIT = 20


@runtime_checkable
class NewsClient(Protocol):
    """Protocol for news headline providers."""

    @abstractmethod
    async def fetch_headlines(
        self, category: str, *, limit: int = DEFAULT_HEADLINE_LIMIT
    ) -> NewsHeadlines:
        """Fetch headlines for *category*, most recent first.

        :param category: News category to request from the provider.
        :param limit: Maximum headlines to return.
        :raises NewsClientError: If the provider returns nothing usable.
        """
        ...
