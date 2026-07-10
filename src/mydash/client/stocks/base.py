"""Stock quote client protocol.

Follows the same two-phase pattern as weather and news clients.
"""

from abc import abstractmethod
from typing import Protocol

from mydash.client.stocks.schemas import StockBars, StockQuotes


class StockClient(Protocol):
    """Protocol for stock quote providers."""

    @abstractmethod
    def set_current_stock_quotes(self, symbols: list[str]) -> None:
        """Fetch latest quotes from the provider and cache them on the client."""

    @abstractmethod
    def get_current_stock_quotes(self) -> StockQuotes:
        """Return quotes cached by the most recent ``set_current_stock_quotes`` call."""
        ...

    @abstractmethod
    def set_current_stock_bars(self, symbols: list[str]) -> None: ...

    @abstractmethod
    def get_current_stock_bars(self) -> StockBars: ...
