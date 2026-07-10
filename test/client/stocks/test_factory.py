"""Tests for mydash.client.stocks.factory.

Target: get_stock_client(provider, **config)
Strategy: direct instantiation checks; requires alpaca_env fixture for AlpacaClient.
Depends on: conftest.alpaca_env
"""

import pytest

from mydash.client.stocks.base import StockClient
from mydash.client.stocks.base_errors import StockFactoryError
from mydash.client.stocks.factory import get_stock_client


# --- Factory ---
@pytest.mark.parametrize(
    argnames="mock_provider, expected_provider",
    argvalues=[
        (None, "AlpacaClient"),
        ("alpaca", "AlpacaClient"),
        ("", "AlpacaClient"),
    ],
)
def test_get_stock_client_valid_provider_return_stock_client_instance(
    mock_provider, expected_provider
):
    stock_client: StockClient = get_stock_client(mock_provider)
    assert stock_client.__class__.__name__ == expected_provider


@pytest.mark.parametrize(
    argnames="mock_provider, expected_error",
    argvalues=[
        (2, StockFactoryError),
        ("hoopla", StockFactoryError),
        ({}, StockFactoryError),
    ],
)
def test_get_stock_client_invalid_provider_raise_stock_factory_error(
    mock_provider, expected_error
):
    with pytest.raises(expected_error) as err:
        get_stock_client(mock_provider)
    assert isinstance(err.value, expected_error)
