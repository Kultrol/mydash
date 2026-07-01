"""News client protocol.

Mirrors the weather client two-phase pattern: fetch via ``set_news_headlines``,
read via ``get_news_headlines``.
"""

from typing import Protocol, Any
from abc import abstractmethod
from .schemas import NewsHeadlines


class NewsClient(Protocol):
    """Protocol for news headline providers."""

    @abstractmethod
    def _make_request(self, params) -> Any:
        """Send an HTTP request to the provider API.

        :param params: Query parameters (shape varies by provider).
        :return: Parsed JSON response body.
        """

    @abstractmethod
    def set_news_headlines(self, category: str = "politics") -> None:
        """Fetch headlines from the provider and cache them on the client instance.

        :param category: News category to request from the provider.
        """

    @abstractmethod
    def get_news_headlines(self) -> NewsHeadlines:
        """Return headlines cached by the most recent ``set_news_headlines`` call."""
        ...
