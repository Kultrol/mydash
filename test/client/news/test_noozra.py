"""Tests for mydash.client.news.noozra.

Target: NoozraClient
Usage pattern: set_news_headlines(category=...) then get_news_headlines()
Strategy: patch _make_request or mock client.client.get; use mock_urls fixture
Depends on: conftest.mock_urls, conftest.sample_noozra_articles
"""

from unittest.mock import MagicMock

import httpx
import pytest
from pydantic import ValidationError

from mydash.client.news.base import NewsClient
from src.mydash.client.news.factory import get_news_client
from src.mydash.client.news.noozra import NoozraParams

# --- set_news_headlines ---


#'set_news_headlines' bad input, raised Validation Error
@pytest.mark.parametrize(
    argnames="mock_category, expected_error",
    argvalues=[(2, ValidationError), (None, ValidationError), ({}, ValidationError)],
)
def test_set_news_headlines_bad_input_raise_validation_error(
    mock_category, expected_error
):
    news_client: NewsClient = get_news_client()
    with pytest.raises(expected_exception=expected_error) as err:
        news_client.set_news_headlines(category=mock_category)

    assert isinstance(err.value, expected_error)


#'set_news_headlines' bad '_make_request' response, raised ValueError
@pytest.mark.parametrize(
    argnames="mock_response, expected_error",
    argvalues=[
        ({}, ValueError),
        ({"error": "something bad"}, ValueError),
        ({"results": []}, ValueError),
    ],
)
def test_set_news_headlines_bad__make_reuqest_response_rasied_value_error(
    monkeypatch, mock_response, expected_error
):
    news_client = get_news_client()

    mock_make_request = MagicMock(return_value=mock_response)
    monkeypatch.setattr(news_client, "_make_request", mock_make_request)

    with pytest.raises(expected_error) as err:
        news_client.set_news_headlines(category="politics")
    assert isinstance(err.value, expected_error)


# --- _make_request / HTTP errors ---
def make_bad_response(status_code: int) -> httpx.Response:
    request = httpx.Request("GET", "https://example.com/some/endpoint")
    return httpx.Response(status_code=status_code, request=request)


@pytest.mark.parametrize(
    argnames="status_code", argvalues=[400, 401, 403, 404, 429, 500, 502, 503]
)
def test__make_request_raises_http_status_error(monkeypatch, status_code):
    news_client = get_news_client()

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.get.return_value = make_bad_response(status_code)

    monkeypatch.setattr(news_client, "client", mock_client)

    with pytest.raises(httpx.HTTPStatusError) as err:
        news_client._make_request(NoozraParams(category="politics"))
    assert err.value.response.status_code == status_code, (
        f"Raised:{err.value.response.status_code} and expected: {status_code}"
    )


# --- Error handling ---


@pytest.mark.parametrize(
    argnames="mock_response, expected_error",
    argvalues=[
        ({"articles": [{"bob": "joe"}]}, ValidationError),
        (
            {"articles": [{"headline": "Hey Joe.(Check JimiHendrix's 'Hey Joe')"}]},
            ValidationError,
        ),
    ],
)
def test_set_news_headlines_failed_headline_validation(
    monkeypatch, mock_response, expected_error
):
    news_client = get_news_client()

    mock_make_request = MagicMock(return_value=mock_response)
    monkeypatch.setattr(news_client, "_make_request", mock_make_request)

    with pytest.raises(expected_error) as err:
        news_client.set_news_headlines(category="politics")
    assert isinstance(err.value, expected_error)
