"""Noozra News API client implementation.

Fetches categorized article headlines from https://noozra.com/api/articles.
No API key required.
"""

import httpx
from pydantic import BaseModel, ValidationError

from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.news.base import NewsClient
from mydash.client.news.providers.noozra.errors import (
    HeadlineSettingError,
    MissingArticlesError,
    MissingNewsHeadlinesError,
    ParameterSettingError,
)
from mydash.client.news.schemas import HeadLine, NewsHeadlines


class NoozraParams(BaseModel):
    """Query parameters for the Noozra articles endpoint."""

    category: str


class NoozraClient(NewsClient):
    """Fetch and cache news headlines from the Noozra API."""

    def __init__(self):
        self.url = httpx.URL("https://noozra.com/api/articles")
        self.news_headlines: NewsHeadlines | None = None

    def set_news_headlines(self, category: str) -> None:
        try:
            params = NoozraParams(category=category)
        except ValidationError as err:
            raise ParameterSettingError(validation_err=err)

        raw_news_headlines = HttpApiClient().make_request(
            url=self.url, request_method="GET", parameters=params.model_dump()
        )

        articles = raw_news_headlines.get("articles")
        if articles is None:
            raise MissingArticlesError(url=self.url.__str__())

        # ----------------------------------------------
        # TODO: Encapsulate this into a function
        # ---------------------------------------------

        # Map each API article dict to a validated HeadLine model.
        self.news_headlines = NewsHeadlines(headlines=[])

        for article in articles:
            try:
                new_headline = HeadLine(
                    headline=article.get("headline"),
                    publication=article.get("source"),
                    description=article.get("description"),
                    source_url=article.get("url"),
                    category=article.get("category"),
                    published_time=article.get("published_at"),
                )
            except ValidationError as err:
                raise HeadlineSettingError(article=article, validation_err=err)
            self.news_headlines.headlines.append(new_headline)

    def get_news_headlines(self) -> NewsHeadlines:
        if self.news_headlines is not None:
            return self.news_headlines
        else:
            raise MissingNewsHeadlinesError()
