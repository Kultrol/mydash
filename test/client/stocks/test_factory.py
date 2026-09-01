"""Tests for mydash.client.stocks.factory.

Target: get_stock_client(provider)
Strategy: direct instantiation checks; requires alpaca_env fixture for AlpacaClient.
Depends on: conftest.alpaca_env
"""

import pytest

from mydash.client.stocks.base import StockClient
from mydash.client.stocks.base_errors import StockFactoryError
from mydash.client.stocks.factory import get_stock_client


# --- Factory ---
def test_get_stock_client_valid_provider_return_stock_client_instance():
    stock_client: StockClient = get_stock_client("alpaca")
    assert stock_client.__class__.__name__ == "AlpacaClient"


def test_get_stock_client_defaults_to_alpaca():
    assert get_stock_client().__class__.__name__ == "AlpacaClient"


@pytest.mark.parametrize(
    argnames="mock_provider, expected_error",
    argvalues=[
        (2, StockFactoryError),
        ("hoopla", StockFactoryError),
        ({}, StockFactoryError),
        (None, StockFactoryError),
        ("", StockFactoryError),
    ],
)
def test_get_stock_client_invalid_provider_raise_stock_factory_error(
    mock_provider, expected_error
):
    with pytest.raises(expected_error) as err:
        get_stock_client(mock_provider)
    assert isinstance(err.value, expected_error)
