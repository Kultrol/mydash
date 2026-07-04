"""Tests for mydash.client.stocks.alpaca."""

from unittest.mock import patch

import pytest

from mydash.client.stocks.base import StockClient
from src.mydash.client.stocks.factory import get_stock_client


# --- __init__ / credentials ---
@pytest.mark.parametrize(
    argnames="mock_env_api_key, mock_env_api_secret, expected_error",
    argvalues=[("STOCK_ALPACA_API_KEY_ID", "STOCK_ALPACA_API_SECRET_KEY", ValueError)],
)
def test__init__missing_env_items_raise_value_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_env_api_key,
    mock_env_api_secret,
    expected_error,
) -> None:
    monkeypatch.delenv(mock_env_api_key, raising=False)
    monkeypatch.delenv(mock_env_api_secret, raising=False)
    with patch("src.mydash.client.stocks.alpaca.load_dotenv"):
        with pytest.raises(expected_error) as err:
            _ = get_stock_client()
        assert isinstance(err.value, expected_error)


@pytest.mark.parametrize(
    argnames="mock_missing_env, expected_error",
    argvalues=[
        ("STOCK_ALPACA_API_KEY_ID", ValueError),
        ("STOCK_ALPACA_API_SECRET_KEY", ValueError),
    ],
)
def test__init__missing_env_item_raise_value_error(
    monkeypatch: pytest.MonkeyPatch,
    mock_missing_env,
    expected_error,
) -> None:
    monkeypatch.delenv(mock_missing_env, raising=False)
    with patch("src.mydash.client.stocks.alpaca.load_dotenv"):
        with pytest.raises(expected_error) as err:
            _ = get_stock_client()
        assert isinstance(err.value, expected_error)


@pytest.mark.parametrize(
    argnames="mock_env_api_key, mock_env_api_key_value, mock_env_api_secret, mock_env_api_secret_value",
    argvalues=[
        (
            "STOCK_ALPACA_API_KEY_ID",
            "test_key",
            "STOCK_ALPACA_API_SECRET_KEY",
            "test_secret",
        )
    ],
)
def test__init__sets_env_items(
    monkeypatch: pytest.MonkeyPatch,
    mock_env_api_key,
    mock_env_api_secret,
    mock_env_api_key_value,
    mock_env_api_secret_value,
) -> None:
    monkeypatch.setenv(mock_env_api_key, mock_env_api_key_value)
    monkeypatch.setenv(mock_env_api_secret, mock_env_api_secret_value)
    stock_client: StockClient = get_stock_client("alpaca")
    # headers are a valid attribute, error detected due to basedpyright not detecting AlpacaClient Class in this case.
    assert stock_client.headers.api_key == mock_env_api_key_value
    assert stock_client.headers.api_secret == mock_env_api_secret_value
