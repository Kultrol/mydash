"""News orchestration: a thin pass-through to the configured news client."""

from __future__ import annotations

from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.news.base import DEFAULT_HEADLINE_LIMIT, NewsClient
from mydash.client.news.factory import get_news_client
from mydash.models.news import NewsHeadlines


class NewsService:
    """Fetch headlines for a category through the configured provider."""

    def __init__(
        self,
        news_provider: str = "noozra",
        *,
        http_client: HttpApiClient | None = None,
    ) -> None:
        """Build the news client for *news_provider*.

        :param news_provider: News factory key (e.g. ``noozra``).
        :param http_client: Shared HTTP client to reuse connections and cache.
        """
        self.news_client: NewsClient = get_news_client(
            provider=news_provider, http_client=http_client
        )

    async def fetch_news(
        self, category: str, *, limit: int = DEFAULT_HEADLINE_LIMIT
    ) -> NewsHeadlines:
        """Return headlines for *category*, newest first.

        :param category: Category to request.
        :param limit: Maximum headlines to return.
        """
        return await self.news_client.fetch_headlines(category, limit=limit)
