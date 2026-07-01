"""Noozra News API client implementation.

Fetches categorized article headlines from https://noozra.com/api/articles.
No API key required.
"""

from typing import Any

from mydash.client.news.base import NewsClient
from mydash.client.news.schemas import NewsHeadlines, HeadLine

from rich.console import Console

from pydantic import BaseModel, ValidationError

import httpx


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
            return response.json()
        except httpx.HTTPError as err:
            console.print(f"Encountered an HTTPError at {err.request.url}: {err}\n")
            console.print_exception(show_locals=True)
            # TODO(refinement): call response.raise_for_status() and re-raise instead of
            #   returning None, which causes TypeError in set_news_headlines.

    def set_news_headlines(self) -> None:
        try:
            # TODO(refinement): category is hardcoded; accept as parameter or CLI option
            params = NoozraParams(category="politics")
            raw_news_headlines = self._make_request(params=params)
            # Map each API article dict to a validated HeadLine model.
            for article in raw_news_headlines["articles"]:
                self.news_headlines.headlines.append(
                    HeadLine(
                        headline=article["headline"],
                        publication=article["source"],
                        description=article["description"],
                        source_url=article["url"],
                        category=article["category"],
                        published_time=article["published_at"]
                    )
                )
        except ValidationError as err:
            console.log(f"Noozra Params Validation Error: {err}")
            console.print_exception(show_locals=True)

    def get_news_headlines(self) -> NewsHeadlines:
        return self.news_headlines