"""Alpaca Markets stock data client implementation.

Fetches latest bar/quote data from https://data.alpaca.markets.
Requires API credentials set in environment variables (see stocks/factory.py).
"""

from typing import Any

from mydash.client.stocks.base import StockClient
from mydash.client.stocks.schemas import StockQuotes, StockQuote

import httpx

from pydantic import BaseModel
from rich.console import Console

import os


console = Console()


class AlpacaParams(BaseModel):
    """Query parameters for the Alpaca latest-bars endpoint."""

    symbols: list[str]

    def to_query_params(self) -> dict[str, str]:
        """Serialize symbols as a comma-separated string for the Alpaca API."""
        return {"symbols": ",".join(self.symbols)}


class AlpacaHeaders(BaseModel):
    """Authentication headers for Alpaca API requests."""

    api_key: str | None
    api_secret: str | None
    accept: str


class AlpacaClient(StockClient):
    """Fetch and cache latest stock quotes from Alpaca Markets."""

    def __init__(self):
        self.client = httpx.Client()
        self.url = "https://data.alpaca.markets/v2/stocks/bars/latest"
        if os.getenv("STOCK_ALPACA_API_KEY_ID") is not None or os.getenv("STOCK_ALPACA_API_SECRET_KEY") is not None:
            self.headers = AlpacaHeaders(
                api_key=os.getenv("STOCK_ALPACA_API_KEY_ID"),
                api_secret=os.getenv("STOCK_ALPACA_API_SECRET_KEY"),
                accept="application/json"
            )
        else:
            raise ValueError

        self.stock_quotes = StockQuotes(quotes=[])

    def _make_request(self, params: AlpacaParams) -> Any:
        try:
            if os.getenv("STOCK_ALPACA_API_KEY_ID") is not None or os.getenv("STOCK_ALPACA_API_SECRET_KEY") is not None:
                headers = {
                    "APCA-API-KEY-ID": self.headers.api_key,
                    "APCA-API-SECRET-KEY": self.headers.api_secret,
                    "accept": self.headers.accept
                }
                response = self.client.get(self.url, params=params.to_query_params(), headers=headers)
                response.raise_for_status()
                return response.json()
            else:
                console.print(
                    f"Api key is of type: {type(os.getenv('STOCK_ALPACA_API_KEY_ID'))} | "
                    f"Api secret is of type: {type(os.getenv('STOCK_ALPACA_API_SECRET_KEY'))}"
                )
                raise ValueError
        except httpx.HTTPError as err:
            console.log(f"Encountered an HTTPError at {err.request.url}: {err}\n")
            console.print_exception(show_locals=True)
            raise

    def set_current_stock_quotes(self) -> None:
        params = AlpacaParams(symbols=["SPY", "AAPL", "MSFT"])
        response = self._make_request(params=params)
        bars = response.get("bars", response)
        for ticker in params.symbols:
            self.stock_quotes.quotes.append(StockQuote(
                ticker_name=ticker,
                ask_price=bars[ticker]["ap"],
                bid_price=bars[ticker]["bp"],
                time=bars[ticker]["t"]
            ))
        return None

    def get_current_stock_quotes(self) -> StockQuotes:
        return self.stock_quotes
