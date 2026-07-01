"""Factory for stock quote client instances.

The Alpaca provider requires API credentials via environment variables:
    STOCK_ALPACA_API_KEY_ID
    STOCK_ALPACA_API_SECRET_KEY

TODO(docs): document required .env variables and Alpaca setup in README.md
"""

from mydash.client.stocks.base import StockClient
from .alpaca import AlpacaClient


def get_stock_client(provider: str = "alpaca", **config) -> StockClient:
    """Return a stock client for the given *provider*.

    :param provider: Provider identifier. Currently only ``"alpaca"`` is supported.
    :param config: Reserved for future provider-specific configuration.
    :raises ValueError: If *provider* is not recognized.
    """
    if provider == "alpaca":
        return AlpacaClient()
    else:
        raise ValueError("Unknown provider. Please choose a valid provider")