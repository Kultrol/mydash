"""Stock data client protocol.

Symbols in, quotes or bars out. Symbols the provider had no data for come back
in the result's ``missing`` list rather than as an exception.
"""

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from mydash.models.stocks import StockBars, StockQuotes


@runtime_checkable
class StockClient(Protocol):
    """Protocol for stock market data providers."""

    @abstractmethod
    async def fetch_quotes(self, symbols: list[str]) -> StockQuotes:
        """Fetch the latest bid/ask quote for each symbol.

        :param symbols: Ticker symbols to look up.
        :raises StockClientError: If the request cannot be made at all.
        """
        ...

    @abstractmethod
    async def fetch_bars(self, symbols: list[str]) -> StockBars:
        """Fetch the latest daily bar for each symbol.

        :param symbols: Ticker symbols to look up.
        :raises StockClientError: If the request cannot be made at all.
        """
        ...
