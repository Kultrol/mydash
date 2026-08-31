"""Tests for mydash.client.http_api.

Strategy: drive the real httpx stack through ``httpx.MockTransport`` so retry,
caching, and error mapping are exercised end to end instead of against mocks.
"""

import asyncio
from typing import Any

import httpx
import pytest

from mydash.client.http_api.errors import (
    HttpApiError,
    HttpTimeoutError,
    RequestError,
    ResponseDecodeError,
    StatusCodeError,
)
from mydash.client.http_api.http_api import (
    RETRYABLE_STATUS_CODES,
    USER_AGENT,
    HttpApiClient,
)
from mydash.storage.cache import ResponseCache
from mydash.storage.database import Database

MOCK_URL = "https://api.example.com/v1/resource"


def _client(handler, **kwargs) -> HttpApiClient:
    """Build a client whose requests are answered by *handler*, without waiting."""
    kwargs.setdefault("retries", 0)
    kwargs.setdefault("backoff", 0)
    return HttpApiClient(transport=httpx.MockTransport(handler), **kwargs)


def _run(client: HttpApiClient, **kwargs) -> Any:
    kwargs.setdefault("url", httpx.URL(MOCK_URL))
    kwargs.setdefault("request_method", "GET")
    return asyncio.run(client.make_request(**kwargs))


def _json_handler(payload, status_code: int = 200):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=payload)

    return handler


# =============================================
# ******* Tests for custom exceptions *********
# =============================================


def test_request_error_is_http_api_error():
    err = RequestError(MOCK_URL)
    assert isinstance(err, HttpApiError)
    assert isinstance(err, RequestError)
    assert MOCK_URL in str(err)


def test_http_timeout_error_is_request_error():
    err = HttpTimeoutError(MOCK_URL, timeout=5)
    assert isinstance(err, RequestError)
    assert isinstance(err, HttpApiError)
    assert "timed out" in str(err).lower()
    assert err.timeout == 5


def test_response_decode_error_message():
    err = ResponseDecodeError(
        MOCK_URL,
        status_code=200,
        response_text="<html>not json</html>",
        error=ValueError("bad json"),
    )
    assert isinstance(err, HttpApiError)
    assert MOCK_URL in str(err)
    assert "JSON" in str(err)


@pytest.mark.parametrize(
    argnames="status_code, expected_text",
    argvalues=[
        (400, "Bad Request"),
        (401, "Unauthorized"),
        (403, "Forbidden"),
        (404, "Not Found"),
        (405, "Method Not Allowed"),
        (409, "Conflict"),
        (422, "Unprocessable Entity"),
        (429, "Too Many Requests"),
        (500, "Internal Server Error"),
        (502, "Bad Gateway"),
        (503, "Service Unavailable"),
        (504, "Gateway Timeout"),
        (418, "Client Error"),
        (511, "Server Error"),
    ],
)
def test_status_code_error_message_for_status_code(status_code, expected_text):
    err = StatusCodeError(MOCK_URL, status_code, method="GET")
    assert isinstance(err, StatusCodeError)
    assert isinstance(err, HttpApiError)
    assert expected_text in str(err)
    assert str(status_code) in str(err)
    assert err.status_code == status_code
    assert err.url == MOCK_URL


def test_status_code_error_includes_response_text_when_given():
    err = StatusCodeError(
        MOCK_URL, 401, method="GET", response_text='{"error": "invalid key"}'
    )
    assert "invalid key" in str(err)
    assert err.response_text == '{"error": "invalid key"}'


# =============================================
# ******* Successful requests *****************
# =============================================


def test_make_request_returns_json_on_success():
    result = _run(_client(_json_handler({"results": [1, 2, 3]})))

    assert result == {"results": [1, 2, 3]}


def test_make_request_sends_parameters_and_user_agent():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["user_agent"] = request.headers.get("User-Agent")
        seen["accept"] = request.headers.get("Accept-Language")
        return httpx.Response(200, json={"ok": True})

    _run(
        _client(handler),
        parameters={"q": "miami"},
        headers=httpx.Headers({"Accept-Language": "en"}),
    )

    assert "q=miami" in seen["url"]
    assert seen["user_agent"] == USER_AGENT
    assert seen["accept"] == "en"


def test_make_request_accepts_a_string_url():
    assert _run(_client(_json_handler({"ok": True})), url=MOCK_URL) == {"ok": True}


def test_shared_client_reuses_one_connection_pool():
    calls = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(200, json={"n": calls["count"]})

    async def scenario():
        async with _client(handler) as http:
            pool = http._shared
            first = await http.make_request(url=MOCK_URL, request_method="GET")
            second = await http.make_request(url=MOCK_URL, request_method="GET")
            assert http._shared is pool
            return first, second

    first, second = asyncio.run(scenario())

    assert (first, second) == ({"n": 1}, {"n": 2})
    assert calls["count"] == 2


# =============================================
# ******* Error mapping ***********************
# =============================================


@pytest.mark.parametrize(
    argnames="status_code, expected_text",
    argvalues=[
        (400, "Bad Request"),
        (401, "Unauthorized"),
        (403, "Forbidden"),
        (404, "Not Found"),
        (429, "Too Many Requests"),
        (500, "Internal Server Error"),
        (502, "Bad Gateway"),
        (503, "Service Unavailable"),
    ],
)
def test_make_request_bad_status_raises_status_code_error(status_code, expected_text):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, text='{"error": "something went wrong"}')

    with pytest.raises(StatusCodeError) as err:
        _run(_client(handler))

    assert err.value.status_code == status_code
    assert expected_text in str(err.value)


def test_make_request_connect_error_raises_request_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused", request=request)

    with pytest.raises(RequestError) as err:
        _run(_client(handler))

    assert not isinstance(err.value, HttpTimeoutError)


def test_make_request_timeout_raises_http_timeout_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Read timed out", request=request)

    with pytest.raises(HttpTimeoutError) as err:
        _run(_client(handler), timeout=5)

    assert isinstance(err.value, RequestError)
    assert err.value.timeout == 5
    assert "timed out" in str(err.value).lower()


def test_timeout_error_reports_the_instance_timeout_when_not_overridden():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Read timed out", request=request)

    with pytest.raises(HttpTimeoutError) as err:
        _run(_client(handler, timeout=3.5))

    assert err.value.timeout == 3.5


def test_make_request_invalid_json_raises_response_decode_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>not json</html>")

    with pytest.raises(ResponseDecodeError) as err:
        _run(_client(handler))

    assert err.value.status_code == 200
    assert "JSON" in str(err.value)


# =============================================
# ******* Retries *****************************
# =============================================


@pytest.mark.parametrize("status_code", sorted(RETRYABLE_STATUS_CODES))
def test_retryable_status_is_retried_then_succeeds(status_code):
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(status_code)
        return httpx.Response(200, json={"ok": True})

    assert _run(_client(handler, retries=2)) == {"ok": True}
    assert attempts["count"] == 2


def test_retries_are_exhausted_then_the_status_error_surfaces():
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(503)

    with pytest.raises(StatusCodeError):
        _run(_client(handler, retries=2))

    assert attempts["count"] == 3  # first attempt plus two retries


def test_client_errors_are_not_retried():
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(404)

    with pytest.raises(StatusCodeError):
        _run(_client(handler, retries=2))

    assert attempts["count"] == 1


def test_timeouts_are_retried_before_giving_up():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(HttpTimeoutError):
        _run(_client(handler, retries=1))

    assert attempts["count"] == 2


def test_a_transient_connection_error_recovers_on_retry():
    attempts = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise httpx.ConnectError("nope", request=request)
        return httpx.Response(200, json={"recovered": True})

    assert _run(_client(handler, retries=1)) == {"recovered": True}


def test_retry_after_header_is_honoured(monkeypatch: pytest.MonkeyPatch):
    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr("mydash.client.http_api.http_api.asyncio.sleep", fake_sleep)
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200, json={"ok": True})

    assert _run(_client(handler, retries=1, backoff=0.5)) == {"ok": True}
    assert slept == [2.0]


def test_unparsable_retry_after_falls_back_to_backoff(monkeypatch: pytest.MonkeyPatch):
    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr("mydash.client.http_api.http_api.asyncio.sleep", fake_sleep)
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(
                503, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}
            )
        return httpx.Response(200, json={"ok": True})

    _run(_client(handler, retries=1, backoff=0.5))

    assert len(slept) == 1
    assert 0.5 <= slept[0] <= 1.0  # base delay plus jitter


# =============================================
# ******* Caching *****************************
# =============================================


@pytest.fixture
def cache(tmp_path):
    database = Database(tmp_path / "mydash.db")
    yield ResponseCache(database)
    database.close()


def test_cached_get_is_served_without_a_second_request(cache):
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(200, json={"n": attempts["count"]})

    client = _client(handler, cache=cache)
    first = _run(client, cache_ttl=60)
    second = _run(client, cache_ttl=60)

    assert first == second == {"n": 1}
    assert attempts["count"] == 1


def test_different_parameters_are_cached_separately(cache):
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(200, json={"n": attempts["count"]})

    client = _client(handler, cache=cache)
    _run(client, parameters={"city": "Miami"}, cache_ttl=60)
    _run(client, parameters={"city": "Boston"}, cache_ttl=60)

    assert attempts["count"] == 2


def test_no_cache_ttl_means_no_caching(cache):
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(200, json={"n": attempts["count"]})

    client = _client(handler, cache=cache)
    _run(client)
    _run(client)

    assert attempts["count"] == 2


def test_failed_responses_are_not_cached(cache):
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(500)
        return httpx.Response(200, json={"ok": True})

    client = _client(handler, cache=cache)
    with pytest.raises(StatusCodeError):
        _run(client, cache_ttl=60)

    assert _run(client, cache_ttl=60) == {"ok": True}


def test_non_get_requests_are_never_cached(cache):
    attempts = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        return httpx.Response(200, json={"n": attempts["count"]})

    client = _client(handler, cache=cache)
    _run(client, request_method="POST", cache_ttl=60)
    _run(client, request_method="POST", cache_ttl=60)

    assert attempts["count"] == 2
