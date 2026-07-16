"""News client protocol.

Mirrors the weather client two-phase pattern: fetch via ``set_news_headlines``,
read via ``get_news_headlines``.
"""

from abc import abstractmethod
from typing import Protocol

from mydash.core.models.news import NewsHeadlines


class NewsClient(Protocol):
    """Protocol for news headline providers."""

    @abstractmethod
    async def set_news_headlines(self, category: str) -> None:
        """Fetch headlines from the provider and cache them on the client instance.

        :param category: News category to request from the provider.
        """

    @abstractmethod
    def get_news_headlines(self) -> NewsHeadlines:
        """Return headlines cached by the most recent ``set_news_headlines`` call."""
        ...
