"""Factory for stock data client instances.

The Alpaca provider requires API credentials via environment variables:
    STOCK_ALPACA_API_KEY_ID
    STOCK_ALPACA_API_SECRET_KEY
"""

from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.stocks.base import StockClient
from mydash.client.stocks.base_errors import StockFactoryError
from mydash.client.stocks.providers.alpaca.alpaca import AlpacaClient


def get_stock_client(
    provider: str = "alpaca",
    *,
    http_client: HttpApiClient | None = None,
) -> StockClient:
    """Return a stock client for the given *provider*.

    :param provider: Provider identifier. Currently only ``"alpaca"`` is supported.
    :param http_client: Shared HTTP client to reuse connections and cache.
    :raises StockFactoryError: If *provider* is not recognized.
    """
    if provider == "alpaca":
        return AlpacaClient(http_client=http_client)
    raise StockFactoryError(provider=provider)
