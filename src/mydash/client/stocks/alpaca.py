from typing import Any

from mydash.client.stocks.base import StockClient
from mydash.client.stocks.schemas import StockQuotes, StockQuote

import httpx

from pydantic import BaseModel
from rich.console import Console


import os



console = Console()


class AlpacaParams(BaseModel):
    symbols : list[str]

class AlpacaHeaders(BaseModel):
    api_key : str | None
    api_secret : str | None
    accept : str


class AlpacaClient(StockClient):

    def __init__(self):
        self.client = httpx.Client()
        self.url = "https://data.alpaca.markets/v2/stocks/bars/latest?symbols=SPY"
        if os.getenv("STOCK_ALPACA_API_KEY_ID") is not None or os.getenv("STOCK_ALPACA_API_SECRET_KEY") is not None:
            self.headers = AlpacaHeaders(
                api_key=os.getenv("STOCK_APCA_API_KEY_ID"),
                api_secret=os.getenv("STOCK_APCA_API_SECRET_KEY"),
                accept="application/json"
            )
        else:
            raise ValueError

        self.stock_quotes = StockQuotes(quotes=[])





    def _make_request(self, params: AlpacaParams) -> Any:
        try:
            if os.getenv("STOCK_ALPACA_API_KEY_ID") is not None or os.getenv("STOCK_ALPACA_API_SECRET_KEY") is not None:
                headers = {
                    "APCA-API-KEY-ID" : self.headers.api_key,
                    "APCA-API-SECRET-KEY" : self.headers.api_secret,
                "accept" : self.headers.accept
                }
                response = self.client.get(self.url, params=params.model_dump(), headers=headers)
                return response.json()
            else:
                console.print(f"Api key is of type: {type(os.getenv("STOCK_ALPACA_API_KEY_ID"))} | Api secret is of type: {type(os.getenv("STOCK_ALPACA_API_SECRET_KEY"))}")
                raise ValueError
        except httpx.HTTPError as err:
            console.log(f"Encountered an HTTPError at {err.request.url}: {err}\n")
            console.print_exception(show_locals=True)


    def set_current_stock_quotes(self) -> None:
        params = AlpacaParams(symbols=["SPY","AAPL", "MSFT"])
        response = self._make_request(params=params)
        for ticker in AlpacaParams.symbols:
            self.stock_quotes.quotes.append(StockQuote(
                ticker_name = ticker,
                ask_price = response[ticker]["ap"],
                bid_price = response[ticker]["bp"],
                time = response[ticker]["t"]
            ))
        return None


    def get_current_stock_quotes(self) -> StockQuotes:
        return self.stock_quotes