"""Tests for mydash.client.stocks.alpaca.

Target: AlpacaClient, AlpacaParams
Usage pattern: set_current_stock_quotes() then get_current_stock_quotes()
Strategy: monkeypatch env vars; patch _make_request with bars JSON
Depends on: conftest.alpaca_env, conftest.sample_alpaca_bars
"""

# --- __init__ / credentials ---
#
# TODO(testing): missing env vars raises ValueError on AlpacaClient()
#
# TODO(testing): reads STOCK_ALPACA_API_KEY_ID and STOCK_ALPACA_API_SECRET_KEY
#   (not STOCK_APCA_*) — assert client.headers.api_key and api_secret
#
# TODO(testing): URL is base path without hardcoded ?symbols=SPY query string

# --- AlpacaParams ---
#
# TODO(testing): to_query_params() serializes symbols as comma-separated string —
#   AlpacaParams(symbols=["SPY","AAPL","MSFT"]) → {"symbols": "SPY,AAPL,MSFT"}

# --- set_current_stock_quotes ---
#
# TODO(testing): parses bars response with ap, bp, t per ticker —
#   patch _make_request; assert StockQuote ask_price, bid_price, time, ticker_name
#
# TODO(testing): handles response wrapped in {"bars": {...}} via response.get("bars", response)

# --- _make_request / HTTP errors ---
#
# TODO(testing): HTTP error propagates httpx.HTTPError — mock client.client.get failure