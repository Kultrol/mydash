"""Alpaca Markets stock data client implementation.

Fetches latest bar/quote data from https://data.alpaca.markets.
Requires API credentials set in environment variables (see stocks/factory.py).
"""

import os
from typing import Any, Dict

import httpx
from pydantic import BaseModel, ValidationError

from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.stocks.base import StockClient
from mydash.client.stocks.providers.alpaca.errors import (
    HeaderValidationError,
    MissingStockBarsError,
    MissingStockQuotesError,
    ParameterSettingError,
    ResponseError,
    StockBarsSettingError,
    StockQuotesSettingError,
)
from mydash.client.stocks.schemas import StockBar, StockBars, StockQuote, StockQuotes


class AlpacaParams(BaseModel):
    """Query parameters for the Alpaca latest-bars endpoint."""

    symbols: list[str]

    def to_query_params(self) -> dict[str, str]:
        """Serialize symbols as a comma-separated string for the Alpaca API."""
        return {"symbols": ",".join(self.symbols)}


class AlpacaHeaders(BaseModel):
    """Authentication headers for Alpaca API requests."""

    api_key: str
    api_secret: str
    content_type: str


class AlpacaClient(StockClient):
    """Fetch and cache latest stock quotes from Alpaca Markets."""

    def __init__(self):
        self.quotes_url = httpx.URL(
            "https://data.alpaca.markets/v2/stocks/quotes/latest"
        )
        self.bars_url = httpx.URL("https://data.alpaca.markets/v2/stocks/bars/latest")
        self.stock_quotes: StockQuotes | None = None
        self.stock_bars: StockBars | None = None

    def _header_validation(
        self,
        content_type: str = "application/json",
    ) -> AlpacaHeaders:
        api_key = os.getenv("STOCK_ALPACA_API_KEY_ID")
        api_secret = os.getenv("STOCK_ALPACA_API_SECRET_KEY")
        if api_key is not None and api_secret is not None:
            return AlpacaHeaders(
                api_key=api_key,
                api_secret=api_secret,
                content_type=content_type,
            )
        else:
            raise HeaderValidationError(
                api_key_type=type(api_key),
                api_secret_type=type(api_secret),
                type_of_content_type=type(content_type),
            )

    def _parameter_validation(self, symbols: list[str]) -> AlpacaParams:
        try:
            return AlpacaParams(symbols=symbols)
        except ValidationError as err:
            raise ParameterSettingError(validation_err=err)

    def set_current_stock_quotes(self, symbols: list[str]) -> None:
        params = self._parameter_validation(symbols=symbols)
        headers = self._header_validation()
        response = HttpApiClient().make_request(
            url=self.quotes_url,
            request_method="GET",
            parameters=params.to_query_params(),
            headers=httpx.Headers(
                {
                    "APCA-API-KEY-ID": headers.api_key,
                    "APCA-API-SECRET-KEY": headers.api_secret,
                    "ACCEPT": headers.content_type,
                }
            ),
        )

        if not response.get("quotes", None):
            raise ResponseError(query=params, api_response=response)
        else:
            quotes: Dict[str, Any] = response["quotes"]

        # ------------------------------------------------------
        # TODO: Encapsulate this into a function
        # ------------------------------------------------------
        self.stock_quotes = StockQuotes(quotes=[])
        for ticker in params.symbols:
            if not quotes.get(ticker, None):
                raise ResponseError(query=params, api_response=response)
            else:
                ticker_quote: Dict[str, Any] = quotes[ticker]

            try:
                ticker_ask_price = ticker_quote["ap"]
                ticker_bid_price = ticker_quote["bp"]
                ticker_time = ticker_quote["t"]
            except KeyError as err:
                raise ResponseError(query=params, api_response=response, error=err)

            try:
                stock_quote = StockQuote(
                    ticker_name=ticker,
                    ask_price=ticker_ask_price,
                    bid_price=ticker_bid_price,
                    time=ticker_time,
                )
            except ValidationError as err:
                raise StockQuotesSettingError(err)

            self.stock_quotes.quotes.append(stock_quote)
        return None

    def get_current_stock_quotes(self) -> StockQuotes:
        if self.stock_quotes is not None:
            return self.stock_quotes
        else:
            raise MissingStockQuotesError()

    def set_current_stock_bars(self, symbols: list[str]) -> None:
        params = self._parameter_validation(symbols=symbols)
        headers = self._header_validation()
        response: Dict[str, Any] = HttpApiClient().make_request(
            url=self.bars_url,
            request_method="GET",
            parameters=params.to_query_params(),
            headers=httpx.Headers(
                {
                    "APCA-API-KEY-ID": headers.api_key,
                    "APCA-API-SECRET-KEY": headers.api_secret,
                    "ACCEPT": headers.content_type,
                }
            ),
        )

        # ------------------------------------------------------
        # TODO: Encapsulate this into a function
        # ------------------------------------------------------

        if not response.get("bars", None):
            raise ResponseError(query=params, api_response=response)
        else:
            bars: Dict[str, Any] = response["bars"]

        self.stock_bars = StockBars(bars=[])
        for ticker in params.symbols:
            try:
                bar: Dict[str, Any] = bars[ticker]
            except KeyError as err:
                raise ResponseError(query=params, api_response=response, error=err)

            try:
                open = bar["o"]
                close = bar["c"]
                time = bar["t"]
            except KeyError as err:
                raise ResponseError(query=params, api_response=response, error=err)

            try:
                stock_bar: StockBar = StockBar(
                    ticker_name=ticker, open=open, close=close, time=time
                )
            except ValidationError as err:
                raise StockBarsSettingError(err)
            self.stock_bars.bars.append(stock_bar)
        return None

    def get_current_stock_bars(self):
        if self.stock_bars is not None:
            return self.stock_bars
        else:
            raise MissingStockBarsError()
