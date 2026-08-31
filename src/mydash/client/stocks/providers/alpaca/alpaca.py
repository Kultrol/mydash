"""Alpaca Markets stock data client implementation.

Fetches the latest quotes and daily bars from https://data.alpaca.markets.
Requires API credentials in the environment:

    STOCK_ALPACA_API_KEY_ID
    STOCK_ALPACA_API_SECRET_KEY

A symbol Alpaca returns nothing for — a typo, a delisting, a ticker outside
your data plan — lands in the result's ``missing`` list. One bad symbol should
cost you that row, not the whole markets panel.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.stocks.base import StockClient
from mydash.client.stocks.providers.alpaca.errors import (
    MissingCredentialsError,
    ParameterSettingError,
    ResponseError,
)
from mydash.models.stocks import StockBar, StockBars, StockQuote, StockQuotes
from mydash.storage.cache import TTL

QUOTES_URL = httpx.URL("https://data.alpaca.markets/v2/stocks/quotes/latest")
BARS_URL = httpx.URL("https://data.alpaca.markets/v2/stocks/bars/latest")

API_KEY_ENV_VAR = "STOCK_ALPACA_API_KEY_ID"
API_SECRET_ENV_VAR = "STOCK_ALPACA_API_SECRET_KEY"


class AlpacaParams(BaseModel):
    """Query parameters for the Alpaca latest-quotes and latest-bars endpoints."""

    symbols: list[str] = Field(min_length=1)

    def to_query_params(self) -> dict[str, str]:
        """Serialize symbols as a comma-separated string for the Alpaca API."""
        return {"symbols": ",".join(self.symbols)}


class AlpacaClient(StockClient):
    """Fetch latest quotes and bars from Alpaca Markets."""

    def __init__(self, http_client: HttpApiClient | None = None) -> None:
        """Build the client.

        :param http_client: Shared HTTP client; one is created per instance
            when omitted, so quotes and bars reuse a connection.
        """
        self.quotes_url = QUOTES_URL
        self.bars_url = BARS_URL
        self.http_client = http_client if http_client is not None else HttpApiClient()

    # -- credentials ----------------------------------------------------

    @staticmethod
    def credentials() -> tuple[str, str]:
        """Return the Alpaca key and secret from the environment.

        :raises MissingCredentialsError: If either is unset or blank.
        """
        api_key = os.getenv(API_KEY_ENV_VAR) or ""
        api_secret = os.getenv(API_SECRET_ENV_VAR) or ""
        missing = [
            name
            for name, value in (
                (API_KEY_ENV_VAR, api_key),
                (API_SECRET_ENV_VAR, api_secret),
            )
            if not value.strip()
        ]
        if missing:
            raise MissingCredentialsError(missing)
        return api_key, api_secret

    def _headers(self) -> httpx.Headers:
        """Build the authenticated request headers."""
        api_key, api_secret = self.credentials()
        return httpx.Headers(
            {
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": api_secret,
                "ACCEPT": "application/json",
            }
        )

    @staticmethod
    def _validate(symbols: list[str]) -> AlpacaParams:
        """Validate the requested symbols.

        :raises ParameterSettingError: If *symbols* is empty or not a list of
            strings.
        """
        try:
            return AlpacaParams(symbols=symbols)
        except ValidationError as err:
            raise ParameterSettingError(validation_err=err) from err

    # -- requests -------------------------------------------------------

    async def fetch_quotes(self, symbols: list[str]) -> StockQuotes:
        """Return the latest bid/ask per symbol, plus any symbols with no data."""
        params = self._validate(symbols)
        response = await self._get(self.quotes_url, params)
        entries = _series(response, "quotes", params)

        quotes: list[StockQuote] = []
        missing: list[str] = []
        for ticker in params.symbols:
            quote = _parse_quote(ticker, entries.get(ticker))
            if quote is None:
                missing.append(ticker)
            else:
                quotes.append(quote)
        return StockQuotes(quotes=quotes, missing=missing)

    async def fetch_bars(self, symbols: list[str]) -> StockBars:
        """Return the latest daily bar per symbol, plus any symbols with no data."""
        params = self._validate(symbols)
        response = await self._get(self.bars_url, params)
        entries = _series(response, "bars", params)

        bars: list[StockBar] = []
        missing: list[str] = []
        for ticker in params.symbols:
            bar = _parse_bar(ticker, entries.get(ticker))
            if bar is None:
                missing.append(ticker)
            else:
                bars.append(bar)
        return StockBars(bars=bars, missing=missing)

    async def _get(self, url: httpx.URL, params: AlpacaParams) -> dict[str, Any]:
        """Send an authenticated GET for *params* against *url*."""
        return await self.http_client.make_request(
            url=url,
            request_method="GET",
            parameters=params.to_query_params(),
            headers=self._headers(),
            cache_ttl=TTL["stocks"],
        )


def _series(response: Any, key: str, params: AlpacaParams) -> dict[str, Any]:
    """Return the ``quotes``/``bars`` mapping from a response.

    An empty mapping is fine — that just means every symbol is missing — but a
    response without the key at all is a shape we do not understand.
    """
    if not isinstance(response, dict) or key not in response:
        raise ResponseError(query=params, api_response=response)
    entries = response[key]
    if entries is None:
        return {}
    if not isinstance(entries, dict):
        raise ResponseError(query=params, api_response=response)
    return entries


def _parse_quote(ticker: str, entry: Any) -> StockQuote | None:
    """Build a :class:`StockQuote`, or ``None`` when the entry is unusable."""
    if not isinstance(entry, dict):
        return None
    try:
        return StockQuote(
            ticker_name=ticker,
            ask_price=entry["ap"],
            bid_price=entry["bp"],
            time=entry["t"],
        )
    except (KeyError, TypeError, ValidationError):
        return None


def _parse_bar(ticker: str, entry: Any) -> StockBar | None:
    """Build a :class:`StockBar`, or ``None`` when the entry is unusable."""
    if not isinstance(entry, dict):
        return None
    try:
        return StockBar(
            ticker_name=ticker,
            open=entry["o"],
            close=entry["c"],
            time=entry["t"],
        )
    except (KeyError, TypeError, ValidationError):
        return None
