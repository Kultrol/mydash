"""Tests for mydash.client.stocks.factory.

Target: get_stock_client(provider, **config)
Strategy: direct instantiation checks; requires alpaca_env fixture for AlpacaClient.
Depends on: conftest.alpaca_env
"""

# --- Factory ---
#
# TODO(testing): default/no provider returns AlpacaClient instance when env vars set —
#   use alpaca_env fixture; assert isinstance(get_stock_client(), AlpacaClient)
#
# TODO(testing): unknown provider raises ValueError — parametrize invalid names