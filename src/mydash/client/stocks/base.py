from typing import Protocol, Any
from abc import abstractmethod
from .schemas import StockQuotes



class StockClient(Protocol):

    def _make_request(self, params) -> Any:
        """

        :return:
        """

    def set_current_stock_quotes(self) -> None:
        """

        :return:
        """

    def get_current_stock_quotes(self) -> StockQuotes:
        """

        :return:
        """