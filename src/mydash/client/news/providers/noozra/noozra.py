"""Noozra News API client implementation.

Fetches categorized article headlines from https://noozra.com/api/articles.
No API key required.

One malformed article should not cost you the whole news panel, so articles
that fail validation are skipped; the client only gives up when nothing at all
is usable. Results are deduplicated by URL and returned newest first.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.news.base import DEFAULT_HEADLINE_LIMIT, NewsClient
from mydash.client.news.providers.noozra.errors import (
    MissingArticlesError,
    NoUsableArticlesError,
    ParameterSettingError,
)
from mydash.models.news import HeadLine, NewsHeadlines
from mydash.storage.cache import TTL

ARTICLES_URL = httpx.URL("https://noozra.com/api/articles")


class NoozraParams(BaseModel):
    """Query parameters for the Noozra articles endpoint."""

    category: str = Field(min_length=1)

    def to_params(self) -> dict[str, Any]:
        """Build the flat query-parameter dict for the HTTP client."""
        return self.model_dump()


class NoozraClient(NewsClient):
    """Fetch news headlines from the Noozra API."""

    def __init__(self, http_client: HttpApiClient | None = None) -> None:
        """Build the client.

        :param http_client: Shared HTTP client; one is created per instance
            when omitted.
        """
        self.url = ARTICLES_URL
        self.http_client = http_client if http_client is not None else HttpApiClient()

    async def fetch_headlines(
        self, category: str, *, limit: int = DEFAULT_HEADLINE_LIMIT
    ) -> NewsHeadlines:
        """Return headlines for *category*, newest first.

        :param category: Category to request (case-insensitive).
        :param limit: Maximum headlines to return; values below 1 return none.
        :raises ParameterSettingError: If *category* is blank.
        :raises MissingArticlesError: If the provider returned no articles.
        :raises NoUsableArticlesError: If no article had the required fields.
        """
        try:
            params = NoozraParams(category=category.strip().lower())
        except ValidationError as err:
            raise ParameterSettingError(validation_err=err) from err

        response = await self.http_client.make_request(
            url=self.url,
            request_method="GET",
            parameters=params.to_params(),
            cache_ttl=TTL["news"],
        )

        articles = response.get("articles")
        if not articles:
            raise MissingArticlesError(url=str(self.url), category=params.category)

        headlines = _parse_articles(articles, category=params.category)
        if not headlines:
            raise NoUsableArticlesError(url=str(self.url), details=articles)

        headlines.sort(key=_published_key, reverse=True)
        return NewsHeadlines(headlines=headlines[: max(0, limit)])


def _published_key(headline: HeadLine) -> datetime:
    """Sort key that survives a mix of aware and naive timestamps."""
    when = headline.published_time
    return when if when.tzinfo is not None else when.replace(tzinfo=UTC)


def _parse_articles(articles: Any, *, category: str) -> list[HeadLine]:
    """Parse usable articles, dropping duplicates and malformed entries."""
    if not isinstance(articles, list):
        return []

    headlines: list[HeadLine] = []
    seen: set[str] = set()
    for article in articles:
        headline = _parse_article(article, category=category)
        if headline is None or headline.source_url in seen:
            continue
        seen.add(headline.source_url)
        headlines.append(headline)
    return headlines


def _parse_article(article: Any, *, category: str) -> HeadLine | None:
    """Convert one raw article into a :class:`HeadLine`, or ``None``.

    Providers do not always echo the category back, so the requested one
    stands in — losing a headline over a redundant field would be silly.
    """
    if not isinstance(article, dict):
        return None
    try:
        return HeadLine(
            headline=article.get("headline"),
            publication=article.get("source"),
            description=article.get("description"),
            source_url=article.get("url"),
            category=article.get("category") or category,
            published_time=article.get("published_at"),
        )
    except ValidationError:
        return None
