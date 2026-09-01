"""Pydantic models for stock quote and stock bar data.

Field names map to Alpaca latest-quotes response keys:
    ask_price ← ap, bid_price ← bp, time ← t
    open <- o, close <- c, time <- t

Collections carry a ``missing`` list so a symbol the provider had nothing for
(a typo, a delisting, an unsupported ticker) is reported next to the symbols
that worked, instead of failing the whole request.
"""

import datetime

from pydantic import BaseModel, Field


class StockQuote(BaseModel):
    """Latest bid/ask quote for a single ticker."""

    ticker_name: str
    ask_price: float
    bid_price: float
    time: datetime.datetime


class StockQuotes(BaseModel):
    """Collection of quotes returned by a stock client."""

    quotes: list[StockQuote]
    missing: list[str] = Field(default_factory=list)


class StockBar(BaseModel):
    ticker_name: str
    open: float
    close: float
    time: datetime.datetime


class StockBars(BaseModel):
    """Collection of bars returned by a stock client."""

    bars: list[StockBar]
    missing: list[str] = Field(default_factory=list)
