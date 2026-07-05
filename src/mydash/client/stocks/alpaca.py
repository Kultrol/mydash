"""Alpaca Markets stock data client implementation.

Fetches latest bar/quote data from https://data.alpaca.markets.
Requires API credentials set in environment variables (see stocks/factory.py).
"""

import os
from typing import Any, Dict

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel
from rich.console import Console

from mydash.client.stocks.base import StockClient
from mydash.client.stocks.schemas import StockBar, StockBars, StockQuote, StockQuotes

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
        self.quotes_url = httpx.URL(
            "https://data.alpaca.markets/v2/stocks/quotes/latest"
        )
        self.bars_url = httpx.URL("https://data.alpaca.markets/v2/stocks/bars/latest")
        # Call load_dotenv in a different location. Not in this file.
        # TODO(architecture): load_dotenv() in __init__ couples client construction to
        # process env — explore centralizing env loading (factory or app bootstrap).
        load_dotenv()
        if (
            os.getenv("STOCK_ALPACA_API_KEY_ID") is not None
            and os.getenv("STOCK_ALPACA_API_SECRET_KEY") is not None
        ):
            self.headers = AlpacaHeaders(
                api_key=os.getenv("STOCK_ALPACA_API_KEY_ID"),
                api_secret=os.getenv("STOCK_ALPACA_API_SECRET_KEY"),
                accept="application/json",
            )
        else:
            console.print(
                "Alpaca API key or secret not found. Please proivde a API key and secret to the environment variables."
            )
            raise ValueError

        self.stock_quotes = StockQuotes(quotes=[])
        self.stock_bars = StockBars(bars=[])

    def _make_request(self, url: httpx.URL, params: AlpacaParams) -> Any:
        try:
            headers = {
                "APCA-API-KEY-ID": self.headers.api_key,
                "APCA-API-SECRET-KEY": self.headers.api_secret,
                "content-type": self.headers.accept,
            }
            # TODO(correctness): no request timeout — can hang indefinitely on slow networks.
            response = self.client.get(
                url, params=params.to_query_params(), headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as err:
            console.log(f"Encountered an HTTPError at {err.request.url}: {err}\n")
            console.print_exception(show_locals=True)
            raise

    def set_current_stock_quotes(self) -> None:
        params = AlpacaParams(symbols=["SPY", "AAPL", "MSFT"])
        response = self._make_request(url=self.quotes_url, params=params)
        quotes: Dict[Any, Any] = response.get("quotes", response)
        # TODO(correctness): quotes list is appended without reset — repeated fetches
        # accumulate stale entries.
        for ticker in params.symbols:
            self.stock_quotes.quotes.append(
                StockQuote(
                    ticker_name=ticker,
                    ask_price=quotes[ticker]["ap"],
                    bid_price=quotes[ticker]["bp"],
                    time=quotes[ticker]["t"],
                )
            )
        return None

    def get_current_stock_quotes(self) -> StockQuotes:
        return self.stock_quotes

    def set_current_stock_bars(self) -> None:
        params = AlpacaParams(symbols=["SPY", "AAPL", "MSFT"])
        response = self._make_request(url=self.bars_url, params=params)
        bars: Dict[Any, Any] = response.get("bars", response)
        # TODO(correctness): bars list is appended without reset — repeated fetches
        # accumulate stale entries.
        for ticker in params.symbols:
            self.stock_bars.bars.append(
                StockBar(
                    ticker_name=ticker,
                    open=bars[ticker]["o"],
                    close=bars[ticker]["c"],
                    time=bars[ticker]["t"],
                )
            )
        return None

    def get_current_stock_bars(self):
        return self.stock_bars
