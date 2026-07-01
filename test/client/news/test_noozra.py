"""Tests for the Noozra news client."""

import pytest

import httpx

from mydash.client.news.factory import get_news_client
from mydash.client.news.noozra import NoozraParams


def test_set_news_headlines_accepts_category_param(mocker):
    client = get_news_client("noozra")
    mock_response = {
        "articles": [
            {
                "headline": "Tech headline",
                "source": "Example News",
                "description": "A tech story",
                "url": "https://example.com/tech",
                "category": "technology",
                "published_at": "2026-07-01T12:00:00Z",
            }
        ]
    }
    make_request = mocker.patch.object(client, "_make_request", return_value=mock_response)

    client.set_news_headlines(category="technology")

    make_request.assert_called_once()
    params = make_request.call_args.kwargs["params"]
    assert isinstance(params, NoozraParams)
    assert params.category == "technology"

    headlines = client.get_news_headlines()
    assert len(headlines.headlines) == 1
    assert headlines.headlines[0].headline == "Tech headline"
    assert headlines.headlines[0].category == "technology"


def test_make_request_propagates_http_error(mocker, mock_urls):
    client = get_news_client("noozra")
    request = httpx.Request("GET", mock_urls["news"])
    http_error = httpx.HTTPStatusError(
        "Server error", request=request, response=httpx.Response(500, request=request)
    )
    mocker.patch.object(client.client, "get", side_effect=http_error)

    with pytest.raises(httpx.HTTPError):
        client._make_request(params=NoozraParams(category="politics"))
