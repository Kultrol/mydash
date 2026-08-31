"""Tests for the Alpaca stocks provider.

Strategy: inject a FakeHttpClient (see test/conftest.py) and use the
alpaca_env / no_alpaca_env fixtures for credentials. Partial-result handling
is the main thing under test: one bad symbol must not sink the batch.
"""

import asyncio
from datetime import datetime, timezone

import pytest

from mydash.client.stocks.base_errors import StockClientError
from mydash.client.stocks.factory import get_stock_client
from mydash.client.stocks.providers.alpaca.alpaca import (
    API_KEY_ENV_VAR,
    API_SECRET_ENV_VAR,
    AlpacaClient,
)
from mydash.client.stocks.providers.alpaca.errors import (
    MissingCredentialsError,
    ParameterSettingError,
    ResponseError,
)
from mydash.storage.cache import TTL
from test.conftest import FakeHttpClient

SYMBOLS = ["SPY", "AAPL"]
TIMESTAMP = "2026-08-30T14:30:00Z"


def _quote(ask=1.5, bid=1.4, time=TIMESTAMP):
    return {"ap": ask, "bp": bid, "t": time}


def _bar(open_price=100.0, close=101.5, time=TIMESTAMP):
    return {"o": open_price, "c": close, "t": time}


def _quotes_payload(**overrides):
    quotes = {symbol: _quote() for symbol in SYMBOLS}
    quotes.update(overrides)
    return {"quotes": quotes}


def _bars_payload(**overrides):
    bars = {symbol: _bar() for symbol in SYMBOLS}
    bars.update(overrides)
    return {"bars": bars}


def _fetch_quotes(http, symbols=SYMBOLS):
    return asyncio.run(AlpacaClient(http_client=http).fetch_quotes(symbols))


def _fetch_bars(http, symbols=SYMBOLS):
    return asyncio.run(AlpacaClient(http_client=http).fetch_bars(symbols))


# --- credentials ----------------------------------------------------------


@pytest.mark.parametrize("fetch", [_fetch_quotes, _fetch_bars])
def test_missing_both_credentials_raises_with_an_actionable_message(
    no_alpaca_env, fetch
):
    with pytest.raises(MissingCredentialsError) as err:
        fetch(FakeHttpClient())

    assert err.value.missing == [API_KEY_ENV_VAR, API_SECRET_ENV_VAR]
    assert ".env" in str(err.value)
    assert "Weather and headlines work without them" in str(err.value)
    assert isinstance(err.value, StockClientError)


@pytest.mark.parametrize(
    "present, absent",
    [(API_KEY_ENV_VAR, API_SECRET_ENV_VAR), (API_SECRET_ENV_VAR, API_KEY_ENV_VAR)],
)
def test_one_missing_credential_names_only_that_one(
    monkeypatch: pytest.MonkeyPatch, present, absent
):
    monkeypatch.setenv(present, "value")
    monkeypatch.delenv(absent, raising=False)

    with pytest.raises(MissingCredentialsError) as err:
        _fetch_quotes(FakeHttpClient())

    assert err.value.missing == [absent]


def test_blank_credentials_count_as_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, "   ")
    monkeypatch.setenv(API_SECRET_ENV_VAR, "secret")

    with pytest.raises(MissingCredentialsError):
        _fetch_quotes(FakeHttpClient())


def test_credentials_are_sent_as_alpaca_headers(alpaca_env):
    http = FakeHttpClient(_quotes_payload())

    _fetch_quotes(http)

    headers = http.calls[0]["headers"]
    assert headers["APCA-API-KEY-ID"] == "test-key-id"
    assert headers["APCA-API-SECRET-KEY"] == "test-secret-key"
    assert headers["ACCEPT"] == "application/json"


# --- parameters -----------------------------------------------------------


@pytest.mark.parametrize(
    "bad_symbols",
    ["SPY,AAPL", 1, [1, 2, 3], {"symbols": ["SPY"]}, [], None],
)
@pytest.mark.parametrize("fetch", [_fetch_quotes, _fetch_bars])
def test_invalid_symbols_raise_parameter_setting_error(alpaca_env, fetch, bad_symbols):
    with pytest.raises(ParameterSettingError):
        fetch(FakeHttpClient(), bad_symbols)


def test_symbols_are_sent_comma_separated_and_cached(alpaca_env):
    http = FakeHttpClient(_quotes_payload())

    _fetch_quotes(http)

    assert http.parameters()["symbols"] == "SPY,AAPL"
    assert http.calls[0]["cache_ttl"] == TTL["stocks"]


# --- quotes ---------------------------------------------------------------


def test_fetch_quotes_returns_one_quote_per_symbol(alpaca_env):
    result = _fetch_quotes(FakeHttpClient(_quotes_payload()))

    assert [quote.ticker_name for quote in result.quotes] == SYMBOLS
    assert result.missing == []
    first = result.quotes[0]
    assert first.ask_price == 1.5
    assert first.bid_price == 1.4
    assert first.time == datetime(2026, 8, 30, 14, 30, tzinfo=timezone.utc)


def test_quotes_keep_the_requested_symbol_order(alpaca_env):
    http = FakeHttpClient({"quotes": {"AAPL": _quote(), "SPY": _quote()}})

    result = _fetch_quotes(http, ["SPY", "AAPL"])

    assert [quote.ticker_name for quote in result.quotes] == ["SPY", "AAPL"]


def test_symbol_absent_from_the_response_is_reported_missing(alpaca_env):
    http = FakeHttpClient({"quotes": {"SPY": _quote()}})

    result = _fetch_quotes(http)

    assert [quote.ticker_name for quote in result.quotes] == ["SPY"]
    assert result.missing == ["AAPL"]


@pytest.mark.parametrize(
    "broken",
    [
        {"bp": 1.4, "t": TIMESTAMP},  # no ask
        {"ap": 1.5, "t": TIMESTAMP},  # no bid
        {"ap": 1.5, "bp": 1.4},  # no time
        {"ap": "cheap", "bp": 1.4, "t": TIMESTAMP},  # unusable price
        {"ap": 1.5, "bp": 1.4, "t": "whenever"},  # unusable time
        "not a dict",
        None,
    ],
)
def test_one_unusable_quote_does_not_sink_the_batch(alpaca_env, broken):
    http = FakeHttpClient(_quotes_payload(AAPL=broken))

    result = _fetch_quotes(http)

    assert [quote.ticker_name for quote in result.quotes] == ["SPY"]
    assert result.missing == ["AAPL"]


def test_every_symbol_missing_is_still_a_result_not_an_error(alpaca_env):
    result = _fetch_quotes(FakeHttpClient({"quotes": {}}))

    assert result.quotes == []
    assert result.missing == SYMBOLS


# --- bars -----------------------------------------------------------------


def test_fetch_bars_returns_one_bar_per_symbol(alpaca_env):
    result = _fetch_bars(FakeHttpClient(_bars_payload()))

    assert [bar.ticker_name for bar in result.bars] == SYMBOLS
    assert result.missing == []
    first = result.bars[0]
    assert first.open == 100.0
    assert first.close == 101.5
    assert first.time == datetime(2026, 8, 30, 14, 30, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "broken",
    [
        {"c": 101.5, "t": TIMESTAMP},  # no open
        {"o": 100.0, "t": TIMESTAMP},  # no close
        {"o": 100.0, "c": 101.5},  # no time
        {"o": "high", "c": 101.5, "t": TIMESTAMP},
        "not a dict",
        None,
    ],
)
def test_one_unusable_bar_does_not_sink_the_batch(alpaca_env, broken):
    http = FakeHttpClient(_bars_payload(AAPL=broken))

    result = _fetch_bars(http)

    assert [bar.ticker_name for bar in result.bars] == ["SPY"]
    assert result.missing == ["AAPL"]


def test_bars_request_goes_to_the_bars_endpoint(alpaca_env):
    http = FakeHttpClient(_bars_payload())

    _fetch_bars(http)

    assert "bars/latest" in str(http.calls[0]["url"])


# --- response shape -------------------------------------------------------


@pytest.mark.parametrize("payload", [{}, {"something_else": {}}, {"quotes": []}, []])
def test_unrecognizable_quotes_response_raises_response_error(alpaca_env, payload):
    with pytest.raises(ResponseError):
        _fetch_quotes(FakeHttpClient(payload))


@pytest.mark.parametrize("payload", [{}, {"something_else": {}}, {"bars": "nope"}])
def test_unrecognizable_bars_response_raises_response_error(alpaca_env, payload):
    with pytest.raises(ResponseError):
        _fetch_bars(FakeHttpClient(payload))


def test_null_series_is_treated_as_every_symbol_missing(alpaca_env):
    result = _fetch_quotes(FakeHttpClient({"quotes": None}))

    assert result.missing == SYMBOLS


def test_http_errors_propagate(alpaca_env):
    with pytest.raises(RuntimeError, match="network down"):
        _fetch_quotes(FakeHttpClient(RuntimeError("network down")))


# --- factory wiring -------------------------------------------------------


def test_factory_passes_the_shared_http_client_through(alpaca_env):
    http = FakeHttpClient(_quotes_payload())
    client = get_stock_client("alpaca", http_client=http)

    assert client.http_client is http
    assert asyncio.run(client.fetch_quotes(SYMBOLS)).quotes
