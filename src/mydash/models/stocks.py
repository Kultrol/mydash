"""Pydantic models for stock quote and stock bar data.

Field names map to Alpaca latest-quotes response keys:
    ask_price ← ap, bid_price ← bp, time ← t
    open <- o, close <- c, time <- t
"""

import datetime

from pydantic import BaseModel


class StockQuote(BaseModel):
    """Latest bid/ask quote for a single ticker."""

    ticker_name: str
    ask_price: float
    bid_price: float
    time: datetime.datetime


class StockQuotes(BaseModel):
    """Collection of quotes returned by ``get_current_stock_quotes``."""

    quotes: list[StockQuote]


class StockBar(BaseModel):
    ticker_name: str
    open: float
    close: float
    time: datetime.datetime


class StockBars(BaseModel):
    """Collection of Bars returned by ``get_current_stock_bars``."""

    bars: list[StockBar]
