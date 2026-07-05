"""Noozra News API client implementation.

Fetches categorized article headlines from https://noozra.com/api/articles.
No API key required.
"""

from typing import Any

import httpx
from pydantic import BaseModel
from rich.console import Console

from mydash.client.news.base import NewsClient
from mydash.client.news.schemas import HeadLine, NewsHeadlines


class NoozraParams(BaseModel):
    """Query parameters for the Noozra articles endpoint."""

    category: str


console = Console()


class NoozraClient(NewsClient):
    """Fetch and cache news headlines from the Noozra API."""

    def __init__(self):
        self.client = httpx.Client()
        self.url = "https://noozra.com/api/articles"
        self.timeout = 10
        self.news_headlines = NewsHeadlines(headlines=[])

    def _make_request(self, params: NoozraParams) -> Any:
        try:
            response = self.client.get(
                self.url, params=params.model_dump(), timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as err:
            console.print(f"Encountered an HTTPError at {err.request.url}: {err}\n")
            console.print_exception(show_locals=True)
            raise

    def set_news_headlines(self, category: str) -> None:
        params = NoozraParams(category=category)
        raw_news_headlines = self._make_request(params=params)
        if raw_news_headlines.get("articles") is None:
            raise ValueError

        # Map each API article dict to a validated HeadLine model.
        self.news_headlines = NewsHeadlines(headlines=[])
        for article in raw_news_headlines["articles"]:
            new_headline = HeadLine(
                headline=article.get("headline"),
                publication=article.get("source"),
                description=article.get("description"),
                source_url=article.get("url"),
                category=article.get("category"),
                published_time=article.get("published_at"),
            )
            self.news_headlines.headlines.append(new_headline)

    def get_news_headlines(self) -> NewsHeadlines:
        return self.news_headlines
