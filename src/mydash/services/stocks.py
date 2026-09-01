"""Stocks orchestration: fetch quotes and bars for the configured watch list."""

from __future__ import annotations

import asyncio

from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.stocks.base import StockClient
from mydash.client.stocks.factory import get_stock_client
from mydash.models.stocks import StockBars, StockQuotes


class StocksService:
    """Fetch the market data the brief needs for a set of symbols."""

    def __init__(
        self,
        stock_ticker_symbols: list[str],
        stock_provider: str = "alpaca",
        *,
        http_client: HttpApiClient | None = None,
    ) -> None:
        """Build the stock client for *stock_provider*.

        :param stock_ticker_symbols: Watch-list symbols to fetch.
        :param stock_provider: Stocks factory key (e.g. ``alpaca``).
        :param http_client: Shared HTTP client to reuse connections and cache.
        """
        self.stock_client: StockClient = get_stock_client(
            provider=stock_provider, http_client=http_client
        )
        self.symbols: list[str] = list(stock_ticker_symbols)

    async def fetch_stock_bars_and_quotes(self) -> tuple[StockQuotes, StockBars]:
        """Fetch quotes and bars concurrently.

        An empty watch list short-circuits: no symbols means nothing to ask
        for, and no reason to need credentials.
        """
        if not self.symbols:
            return StockQuotes(quotes=[]), StockBars(bars=[])

        quotes, bars = await asyncio.gather(
            self.stock_client.fetch_quotes(self.symbols),
            self.stock_client.fetch_bars(self.symbols),
        )
        return quotes, bars
