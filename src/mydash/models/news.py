"""Pydantic models for news headline data."""

import datetime

from pydantic import BaseModel


class HeadLine(BaseModel):
    """A single news article headline with metadata."""

    headline: str
    publication: str
    description: str | None
    source_url: str
    category: str
    # Noozra returns ISO datetime strings; Pydantic coerces to datetime.datetime.
    published_time: datetime.datetime


class NewsHeadlines(BaseModel):
    """Collection of headlines returned by ``get_news_headlines``."""

    headlines: list[HeadLine]
