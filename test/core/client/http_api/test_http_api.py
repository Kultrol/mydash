"""Tests for mydash.core.client.http_api."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from mydash.core.client.http_api.errors import (
    HttpApiError,
    HttpTimeoutError,
    RequestError,
    ResponseDecodeError,
    StatusCodeError,
)
from mydash.core.client.http_api.http_api import HttpApiClient

MOCK_URL = "https://api.example.com/v1/resource"


def _patch_async_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    send_return=None,
    send_side_effect=None,
):
    """Patch ``httpx.AsyncClient`` for ``async with`` + ``await send``."""
    mock_client = MagicMock()
    if send_side_effect is not None:
        mock_client.send = AsyncMock(side_effect=send_side_effect)
    else:
        mock_client.send = AsyncMock(return_value=send_return)

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    mock_client_cls = MagicMock(return_value=mock_cm)
    monkeypatch.setattr(httpx, "AsyncClient", mock_client_cls)
    return mock_client, mock_client_cls


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


# ---------------------------------------------
# Stage 1: StatusCodeError messages by code
# ---------------------------------------------


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
# ******* Tests for make_request **************
# =============================================


# ---------------------------------------------
# Stage 1: Successful request | returns JSON
# ---------------------------------------------


def test_make_request_returns_json_on_success(monkeypatch: pytest.MonkeyPatch):
    mock_request = httpx.Request("GET", MOCK_URL)
    mock_response = httpx.Response(
        200, request=mock_request, json={"results": [1, 2, 3]}
    )
    mock_client, _ = _patch_async_client(monkeypatch, send_return=mock_response)

    result = asyncio.run(
        HttpApiClient().make_request(
            url=httpx.URL(MOCK_URL),
            request_method="GET",
            parameters={"q": "miami"},
        )
    )

    assert result == {"results": [1, 2, 3]}
    mock_client.send.assert_awaited_once()


def test_make_request_uses_default_timeout(monkeypatch: pytest.MonkeyPatch):
    mock_request = httpx.Request("GET", MOCK_URL)
    mock_response = httpx.Response(200, request=mock_request, json={"ok": True})
    _, mock_client_cls = _patch_async_client(monkeypatch, send_return=mock_response)

    asyncio.run(
        HttpApiClient().make_request(
            url=httpx.URL(MOCK_URL),
            request_method="GET",
        )
    )

    mock_client_cls.assert_called_once_with(timeout=5)


def test_make_request_uses_custom_timeout(monkeypatch: pytest.MonkeyPatch):
    mock_request = httpx.Request("GET", MOCK_URL)
    mock_response = httpx.Response(200, request=mock_request, json={"ok": True})
    _, mock_client_cls = _patch_async_client(monkeypatch, send_return=mock_response)

    asyncio.run(
        HttpApiClient().make_request(
            url=httpx.URL(MOCK_URL),
            request_method="GET",
            timeout=15,
        )
    )

    mock_client_cls.assert_called_once_with(timeout=15)


# ---------------------------------------------
# Stage 2: Bad status codes raise StatusCodeError
# ---------------------------------------------


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
def test_make_request_bad_status_raises_status_code_error(
    monkeypatch: pytest.MonkeyPatch, status_code, expected_text
):
    mock_request = httpx.Request("GET", MOCK_URL)
    mock_response = httpx.Response(
        status_code, request=mock_request, text='{"error": "something went wrong"}'
    )
    _patch_async_client(monkeypatch, send_return=mock_response)

    with pytest.raises(StatusCodeError) as err:
        asyncio.run(
            HttpApiClient().make_request(
                url=httpx.URL(MOCK_URL),
                request_method="GET",
            )
        )

    assert isinstance(err.value, StatusCodeError)
    assert err.value.status_code == status_code
    assert expected_text in str(err.value)


# ---------------------------------------------
# Stage 3: Network / timeout errors
# ---------------------------------------------


def test_make_request_connect_error_raises_request_error(
    monkeypatch: pytest.MonkeyPatch,
):
    mock_request = httpx.Request("GET", MOCK_URL)
    connect_err = httpx.ConnectError("Connection refused", request=mock_request)
    _patch_async_client(monkeypatch, send_side_effect=connect_err)

    with pytest.raises(RequestError) as err:
        asyncio.run(
            HttpApiClient().make_request(
                url=httpx.URL(MOCK_URL),
                request_method="GET",
            )
        )

    assert isinstance(err.value, RequestError)
    assert not isinstance(err.value, HttpTimeoutError)


def test_make_request_timeout_raises_http_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
):
    mock_request = httpx.Request("GET", MOCK_URL)
    timeout_err = httpx.ReadTimeout("Read timed out", request=mock_request)
    _patch_async_client(monkeypatch, send_side_effect=timeout_err)

    with pytest.raises(HttpTimeoutError) as err:
        asyncio.run(
            HttpApiClient().make_request(
                url=httpx.URL(MOCK_URL),
                request_method="GET",
                timeout=5,
            )
        )

    assert isinstance(err.value, HttpTimeoutError)
    assert isinstance(err.value, RequestError)
    assert err.value.timeout == 5
    assert "timed out" in str(err.value).lower()


# ---------------------------------------------
# Stage 4: Invalid JSON response
# ---------------------------------------------


def test_make_request_invalid_json_raises_response_decode_error(
    monkeypatch: pytest.MonkeyPatch,
):
    mock_request = httpx.Request("GET", MOCK_URL)
    mock_response = httpx.Response(
        200, request=mock_request, text="<html>not json</html>"
    )
    _patch_async_client(monkeypatch, send_return=mock_response)

    with pytest.raises(ResponseDecodeError) as err:
        asyncio.run(
            HttpApiClient().make_request(
                url=httpx.URL(MOCK_URL),
                request_method="GET",
            )
        )

    assert isinstance(err.value, ResponseDecodeError)
    assert err.value.status_code == 200
    assert "JSON" in str(err.value)
