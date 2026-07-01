"""Stock quote client protocol.

Follows the same two-phase pattern as weather and news clients.
"""

from typing import Protocol, Any
from abc import abstractmethod
from .schemas import StockQuotes


class StockClient(Protocol):
    """Protocol for stock quote providers."""

    @abstractmethod
    def _make_request(self, params) -> Any:
        """Send an authenticated HTTP request to the provider API.

        :param params: Query parameters (e.g. symbol list).
        :return: Parsed JSON response body.
        """

    @abstractmethod
    def set_current_stock_quotes(self) -> None:
        """Fetch latest quotes from the provider and cache them on the client."""

    @abstractmethod
    def get_current_stock_quotes(self) -> StockQuotes:
        """Return quotes cached by the most recent ``set_current_stock_quotes`` call."""
        ...
