import asyncio

from mydash.client.stocks.factory import get_stock_client
from mydash.models.stocks import StockBars, StockQuotes


class StocksService:
    def __init__(self, stock_ticker_symbols: list[str], stock_provider: str = "alpaca"):
        self.stock_client = get_stock_client(provider=stock_provider)
        self.symbols: list[str] = stock_ticker_symbols

    async def fetch_stock_bars_and_quotes(self) -> tuple[StockQuotes, StockBars]:
        await asyncio.gather(
            self.stock_client.set_current_stock_quotes(symbols=self.symbols),
            self.stock_client.set_current_stock_bars(symbols=self.symbols),
        )
        stock_quotes = self.stock_client.get_current_stock_quotes()
        stock_bars = self.stock_client.get_current_stock_bars()
        return stock_quotes, stock_bars
