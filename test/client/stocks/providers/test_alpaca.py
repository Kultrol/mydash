"""Tests for mydash.client.stocks.alpaca."""

import pytest

from mydash.client.stocks.base import StockClient
from mydash.client.stocks.factory import get_stock_client
from mydash.client.stocks.providers.alpaca.errors import (
    HeaderValidationError,
    ParameterSettingError,
)

# ==============================================
# ***** Testing 'set_current_stock_quotes' *****
# ==============================================


# Testing Parameter Validation
@pytest.mark.parametrize(
    argnames="mock_bad_symbols, expected_error",
    argvalues=[
        ("SPY, AAPL, MSFT", ParameterSettingError),
        (1, ParameterSettingError),
        ([1, 2, 3], ParameterSettingError),
        ({"symbols": ["SPY", "AAPL", "MSFT"]}, ParameterSettingError),
    ],
)
def test_set_currnet_stock_quotes_bad_params_raise_parameter_setting_error(
    monkeypatch: pytest.MonkeyPatch, mock_bad_symbols, expected_error
):
    stock_client = get_stock_client()
    with pytest.raises(expected_error) as err:
        stock_client.set_current_stock_quotes(symbols=mock_bad_symbols)
    assert isinstance(err.value, expected_error)


# Testing Header Validation
@pytest.mark.parametrize(
    argnames="mock_symbols, mock_api_key, mock_api_secret, expected_error",
    argvalues=[
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_SECRET_KEY",
            HeaderValidationError,
        )
    ],
)
def test_set_current_stock_quotes_missing_env_vars_raise_header_validation_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_symbols,
    mock_api_key,
    mock_api_secret,
    expected_error,
):
    stock_client = get_stock_client()

    monkeypatch.delenv(name=mock_api_key, raising=False)
    monkeypatch.delenv(name=mock_api_secret, raising=False)

    with pytest.raises(expected_error) as err:
        stock_client.set_current_stock_quotes(symbols=mock_symbols)
    assert isinstance(err.value, expected_error)
