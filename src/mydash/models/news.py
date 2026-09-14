"""Pydantic models for news headline data.

Every string here is written by the provider, or by whoever it syndicates, so
each one is a :data:`~mydash.models.text.CleanStr`.
"""

import datetime

from pydantic import BaseModel

from mydash.models.text import CleanStr


class HeadLine(BaseModel):
    """A single news article headline with metadata."""

    headline: CleanStr
    publication: CleanStr
    description: CleanStr | None
    source_url: CleanStr
    category: CleanStr
    # Noozra returns ISO datetime strings; Pydantic coerces to datetime.datetime.
    published_time: datetime.datetime


class NewsHeadlines(BaseModel):
    """Collection of headlines returned by ``get_news_headlines``."""

    headlines: list[HeadLine]
