"""Tests for mydash.client.stocks.alpaca."""

from unittest.mock import MagicMock

import pytest

from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.stocks.base import StockClient
from mydash.client.stocks.factory import get_stock_client
from mydash.client.stocks.providers.alpaca.errors import (
    HeaderValidationError,
    MissingStockBarsError,
    MissingStockQuotesError,
    ParameterSettingError,
    ResponseError,
    StockBarsSettingError,
    StockQuotesSettingError,
)
from mydash.models.stocks import StockBars, StockQuotes

# ==============================================
# ***** Testing 'set_current_stock_bars' *****
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
def test_set_current_stock_bars_bad_params_raise_parameter_setting_error(
    monkeypatch: pytest.MonkeyPatch, mock_bad_symbols, expected_error
):
    stock_client = get_stock_client()
    with pytest.raises(expected_error) as err:
        stock_client.set_current_stock_bars(symbols=mock_bad_symbols)
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
def test_set_current_stock_bars_missing_env_vars_raise_header_validation_error(
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
        stock_client.set_current_stock_bars(symbols=mock_symbols)
    assert isinstance(err.value, expected_error)




# Testing Catching Response Errors — missing/empty "bars" key
@pytest.mark.parametrize(
    argnames="mock_symbols, mock_api_key, mock_api_key_value, mock_api_secret, mock_api_secret_value, mock_api_response, expected_error",
    argvalues=[
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {},
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {"hello": "world"},
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {"bars": {}},
            ResponseError,
        ),
    ],
)
def test_set_current_stock_bars_missing_bars_key_raise_response_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_symbols,
    mock_api_key,
    mock_api_key_value,
    mock_api_secret,
    mock_api_secret_value,
    mock_api_response,
    expected_error,
):
    monkeypatch.setenv(name=mock_api_key, value=mock_api_key_value)
    monkeypatch.setenv(name=mock_api_secret, value=mock_api_secret_value)

    stock_client = get_stock_client("alpaca")

    mock_response = MagicMock(return_value=mock_api_response)

    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    with pytest.raises(expected_error) as err:
        stock_client.set_current_stock_bars(symbols=mock_symbols)
    assert isinstance(err.value, expected_error)


# Testing Catching Response Errors — missing ticker in "bars"
@pytest.mark.parametrize(
    argnames="mock_symbols, mock_api_key, mock_api_key_value, mock_api_secret, mock_api_secret_value, mock_api_response, expected_error",
    argvalues=[
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {"bars": {"SPY": {}}},
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "AAPL": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "SPY": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "SPY": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
    ],
)
def test_set_current_stock_bars_missing_ticker_key_raise_response_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_symbols,
    mock_api_key,
    mock_api_key_value,
    mock_api_secret,
    mock_api_secret_value,
    mock_api_response,
    expected_error,
):
    monkeypatch.setenv(name=mock_api_key, value=mock_api_key_value)
    monkeypatch.setenv(name=mock_api_secret, value=mock_api_secret_value)

    stock_client = get_stock_client("alpaca")

    mock_response = MagicMock(return_value=mock_api_response)

    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    with pytest.raises(expected_error) as err:
        stock_client.set_current_stock_bars(symbols=mock_symbols)
    assert isinstance(err.value, expected_error)


# Testing Catching Response Errors — missing bar field keys (o, c, t)
@pytest.mark.parametrize(
    argnames="mock_symbols, mock_api_key, mock_api_key_value, mock_api_secret, mock_api_secret_value, mock_api_response, expected_error",
    argvalues=[
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "SPY": {
                        "o": 12.3,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "o": 12.3,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "o": 12.3,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "SPY": {
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "SPY": {
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "SPY": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "o": 12.3,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "SPY": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "o": 12.3,
                        "c": 12.5,
                    },
                }
            },
            ResponseError,
        ),
    ],
)
def test_set_current_stock_bars_missing_bar_keys_raise_response_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_symbols,
    mock_api_key,
    mock_api_key_value,
    mock_api_secret,
    mock_api_secret_value,
    mock_api_response,
    expected_error,
):
    monkeypatch.setenv(name=mock_api_key, value=mock_api_key_value)
    monkeypatch.setenv(name=mock_api_secret, value=mock_api_secret_value)

    stock_client = get_stock_client("alpaca")

    mock_response = MagicMock(return_value=mock_api_response)

    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    with pytest.raises(expected_error) as err:
        stock_client.set_current_stock_bars(symbols=mock_symbols)
    assert isinstance(err.value, expected_error)




# Testing Validation Errors -> Raise StockBarsSettingError
@pytest.mark.parametrize(
    argnames="mock_symbols, mock_api_key, mock_api_key_value, mock_api_secret, mock_api_secret_value, mock_api_response, expected_error",
    argvalues=[
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "SPY": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "string",
                    },
                }
            },
            StockBarsSettingError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "SPY": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "o": 12.3,
                        "c": "string",
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            StockBarsSettingError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "SPY": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "o": "string",
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            StockBarsSettingError,
        ),
    ],
)
def test_set_current_stock_bars_validation_failure_raise_stock_bars_setting_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_symbols,
    mock_api_key,
    mock_api_key_value,
    mock_api_secret,
    mock_api_secret_value,
    mock_api_response,
    expected_error,
):
    monkeypatch.setenv(name=mock_api_key, value=mock_api_key_value)
    monkeypatch.setenv(name=mock_api_secret, value=mock_api_secret_value)

    stock_client = get_stock_client("alpaca")

    mock_response = MagicMock(return_value=mock_api_response)

    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    with pytest.raises(expected_error) as err:
        stock_client.set_current_stock_bars(symbols=mock_symbols)
    assert isinstance(err.value, expected_error)




# ==============================================
# ***** Testing 'get_current_stock_bars' *****
# ==============================================


# Test case: self.stock_bars is None -> raises MissingStockBarsError
def test_get_current_stock_bars_missing_stock_bars_raise_missing_stock_bars_error():
    stock_client = get_stock_client()

    with pytest.raises(MissingStockBarsError) as err:
        stock_client.get_current_stock_bars()
    assert isinstance(err.value, MissingStockBarsError)


# Test case: bars properly set -> returns StockBars
@pytest.mark.parametrize(
    argnames="mock_symbols, mock_api_key, mock_api_key_values, mock_api_secret, mock_api_secret_value, mock_api_response",
    argvalues=[
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "bars": {
                    "SPY": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "o": 12.3,
                        "c": 12.5,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
        )
    ],
)
def test_get_current_stock_bars_found_stock_bars_return_stock_bars(
    monkeypatch: pytest.MonkeyPatch,
    mock_symbols,
    mock_api_key,
    mock_api_key_values,
    mock_api_secret,
    mock_api_secret_value,
    mock_api_response,
):
    monkeypatch.setenv(name=mock_api_key, value=mock_api_key_values)
    monkeypatch.setenv(name=mock_api_secret, value=mock_api_secret_value)

    stock_client = get_stock_client("alpaca")

    mock_response = MagicMock(return_value=mock_api_response)
    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    stock_client.set_current_stock_bars(symbols=mock_symbols)

    result_current_bars = stock_client.get_current_stock_bars()

    assert isinstance(result_current_bars, StockBars)


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
def test_set_current_stock_quotes_bad_params_raise_parameter_setting_error(
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


# Testing Catching Response Errors
@pytest.mark.parametrize(
    argnames="mock_symbols, mock_api_key, mock_api_key_value, mock_api_secret, mock_api_secret_value, mock_api_response, expected_error",
    argvalues=[
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {},
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {"hello": "world"},
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {"quotes": {}},
            ResponseError,
        ),
    ],
)
def test_set_current_stock_quotes_missing_quotes_key_raise_response_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_symbols,
    mock_api_key,
    mock_api_key_value,
    mock_api_secret,
    mock_api_secret_value,
    mock_api_response,
    expected_error,
):
    monkeypatch.setenv(name=mock_api_key, value=mock_api_key_value)
    monkeypatch.setenv(name=mock_api_secret, value=mock_api_secret_value)

    stock_client = get_stock_client("alpaca")

    mock_response = MagicMock(return_value=mock_api_response)

    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    with pytest.raises(expected_error) as err:
        stock_client.set_current_stock_quotes(symbols=mock_symbols)
    assert isinstance(err.value, expected_error)


# Testing Catching Response Errors
@pytest.mark.parametrize(
    argnames="mock_symbols, mock_api_key, mock_api_key_value, mock_api_secret, mock_api_secret_value, mock_api_response, expected_error",
    argvalues=[
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {"quotes": {"SPY": {}}},
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "AAPL": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "SPY": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "SPY": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
    ],
)
def test_set_current_stock_quotes_missing_ticker_key_raise_response_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_symbols,
    mock_api_key,
    mock_api_key_value,
    mock_api_secret,
    mock_api_secret_value,
    mock_api_response,
    expected_error,
):
    monkeypatch.setenv(name=mock_api_key, value=mock_api_key_value)
    monkeypatch.setenv(name=mock_api_secret, value=mock_api_secret_value)

    stock_client = get_stock_client("alpaca")

    mock_response = MagicMock(return_value=mock_api_response)

    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    with pytest.raises(expected_error) as err:
        stock_client.set_current_stock_quotes(symbols=mock_symbols)
    assert isinstance(err.value, expected_error)


# Testing Catching Response Errors
@pytest.mark.parametrize(
    argnames="mock_symbols, mock_api_key, mock_api_key_value, mock_api_secret, mock_api_secret_value, mock_api_response, expected_error",
    argvalues=[
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "SPY": {
                        "ap": 12.3,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "ap": 12.3,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "ap": 12.3,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "SPY": {
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "SPY": {
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "SPY": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "ap": 12.3,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            ResponseError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "SPY": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "ap": 12.3,
                        "bp": 12.2,
                    },
                }
            },
            ResponseError,
        ),
    ],
)
def test_set_current_stock_quotes_missing_quote_keys_raise_response_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_symbols,
    mock_api_key,
    mock_api_key_value,
    mock_api_secret,
    mock_api_secret_value,
    mock_api_response,
    expected_error,
):
    monkeypatch.setenv(name=mock_api_key, value=mock_api_key_value)
    monkeypatch.setenv(name=mock_api_secret, value=mock_api_secret_value)

    stock_client = get_stock_client("alpaca")

    mock_response = MagicMock(return_value=mock_api_response)

    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    with pytest.raises(expected_error) as err:
        stock_client.set_current_stock_quotes(symbols=mock_symbols)
    assert isinstance(err.value, expected_error)


# Testing Vaildation Errors -> Raise StockQuoteSettingErrors
@pytest.mark.parametrize(
    argnames="mock_symbols, mock_api_key, mock_api_key_value, mock_api_secret, mock_api_secret_value, mock_api_response, expected_error",
    argvalues=[
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "SPY": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "string",
                    },
                }
            },
            StockQuotesSettingError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "SPY": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "ap": 12.3,
                        "bp": "string",
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            StockQuotesSettingError,
        ),
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "SPY": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "ap": "string",
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
            StockQuotesSettingError,
        ),
    ],
)
def test_set_current_quotes_validation_failure_raise_stock_quotes_setting_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_symbols,
    mock_api_key,
    mock_api_key_value,
    mock_api_secret,
    mock_api_secret_value,
    mock_api_response,
    expected_error,
):
    monkeypatch.setenv(name=mock_api_key, value=mock_api_key_value)
    monkeypatch.setenv(name=mock_api_secret, value=mock_api_secret_value)

    stock_client = get_stock_client("alpaca")

    mock_response = MagicMock(return_value=mock_api_response)

    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    with pytest.raises(expected_error) as err:
        stock_client.set_current_stock_quotes(symbols=mock_symbols)
    assert isinstance(err.value, expected_error)


# ==============================================
# ***** Testing 'get_current_stock_quotes' *****
# ==============================================


def test_get_current_stock_quotes_missing_stock_quotes_raise_missing_stock_quotes_error():
    stock_client = get_stock_client()

    with pytest.raises(MissingStockQuotesError) as err:
        stock_client.get_current_stock_quotes()
    assert isinstance(err.value, MissingStockQuotesError)


@pytest.mark.parametrize(
    argnames="mock_symbols, mock_api_key, mock_api_key_values, mock_api_secret, mock_api_secret_value, mock_api_response",
    argvalues=[
        (
            ["SPY", "AAPL", "MSFT"],
            "STOCK_ALPACA_API_KEY_ID",
            "STOCK_ALPACA_API_KEY_VALUE",
            "STOCK_ALPACA_API_SECRET_KEY",
            "STOCK_ALPACA_API_SECRET_VALUE",
            {
                "quotes": {
                    "SPY": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "AAPL": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                    "MSFT": {
                        "ap": 12.3,
                        "bp": 12.2,
                        "t": "2022-08-17T10:07:40.286587431Z",
                    },
                }
            },
        )
    ],
)
def test_get_current_stock_quotes_found_stock_quotes_return_stock_quotes(
    monkeypatch: pytest.MonkeyPatch,
    mock_symbols,
    mock_api_key,
    mock_api_key_values,
    mock_api_secret,
    mock_api_secret_value,
    mock_api_response,
):

    monkeypatch.setenv(name=mock_api_key, value=mock_api_key_values)
    monkeypatch.setenv(name=mock_api_secret, value=mock_api_secret_value)

    stock_client = get_stock_client("alpaca")

    mock_response = MagicMock(return_value=mock_api_response)
    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    stock_client.set_current_stock_quotes(symbols=mock_symbols)

    result_current_quotes = stock_client.get_current_stock_quotes()

    assert isinstance(result_current_quotes, StockQuotes)
