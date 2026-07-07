"""Factory for stock quote client instances.

The Alpaca provider requires API credentials via environment variables:
    STOCK_ALPACA_API_KEY_ID
    STOCK_ALPACA_API_SECRET_KEY
"""

from mydash.client.stocks.base import StockClient
from mydash.client.stocks.base_errors import StockFactoryError
from mydash.client.stocks.providers.alpaca.alpaca import AlpacaClient


def get_stock_client(provider: str = "alpaca", **config) -> StockClient:
    """Return a stock client for the given *provider*.

    :param provider: Provider identifier. Currently only ``"alpaca"`` is supported.
    :param config: Reserved for future provider-specific configuration.
    :raises ValueError: If *provider* is not recognized.
    """
    if provider == "alpaca" or provider == "" or provider is None:
        return AlpacaClient()
    else:
        raise StockFactoryError(provider=provider)
