"""Tests for the Alpaca stock quote client."""

import os

import pytest

from mydash.client.stocks.alpaca import AlpacaClient, AlpacaParams
from mydash.client.stocks.schemas import StockQuote


@pytest.fixture
def alpaca_env(monkeypatch):
    monkeypatch.setenv("STOCK_ALPACA_API_KEY_ID", "test-key-id")
    monkeypatch.setenv("STOCK_ALPACA_API_SECRET_KEY", "test-secret-key")


def test_alpaca_client_uses_stock_alpaca_env_vars(alpaca_env):
    client = AlpacaClient()

    assert client.headers.api_key == "test-key-id"
    assert client.headers.api_secret == "test-secret-key"
    assert client.url == "https://data.alpaca.markets/v2/stocks/bars/latest"
    assert "symbols=SPY" not in client.url


def test_alpaca_params_serializes_symbols_as_comma_separated_string():
    params = AlpacaParams(symbols=["SPY", "AAPL", "MSFT"])

    assert params.to_query_params() == {"symbols": "SPY,AAPL,MSFT"}


def test_set_current_stock_quotes_parses_ap_bp_t_from_bars(alpaca_env, mocker):
    client = AlpacaClient()
    mock_response = {
        "bars": {
            "SPY": {"ap": 500.1, "bp": 500.0, "t": "2026-07-01T15:00:00Z"},
            "AAPL": {"ap": 210.5, "bp": 210.4, "t": "2026-07-01T15:00:00Z"},
            "MSFT": {"ap": 420.2, "bp": 420.1, "t": "2026-07-01T15:00:00Z"},
        }
    }
    mocker.patch.object(client, "_make_request", return_value=mock_response)

    client.set_current_stock_quotes()
    quotes = client.get_current_stock_quotes()

    assert len(quotes.quotes) == 3
    for quote in quotes.quotes:
        assert isinstance(quote, StockQuote)
        assert quote.ask_price > quote.bid_price

    spy = next(q for q in quotes.quotes if q.ticker_name == "SPY")
    assert spy.ask_price == 500.1
    assert spy.bid_price == 500.0
