"""Tests for the Noozra news provider.

Strategy: inject a FakeHttpClient (see test/conftest.py) and assert on ordering,
deduplication, and how gracefully malformed articles are handled.
"""

import asyncio
from datetime import datetime, timezone

import pytest

from mydash.client.news.base_errors import NewsClientError
from mydash.client.news.factory import get_news_client
from mydash.client.news.providers.noozra.errors import (
    MissingArticlesError,
    NoUsableArticlesError,
    ParameterSettingError,
)
from mydash.client.news.providers.noozra.noozra import NoozraClient
from mydash.models.news import NewsHeadlines
from mydash.storage.cache import TTL
from test.conftest import FakeHttpClient


def _article(
    headline="Something happened",
    url="https://example.com/1",
    published_at="2026-08-30T12:00:00Z",
    **extra,
):
    return {
        "headline": headline,
        "source": "Example Times",
        "description": "A description.",
        "url": url,
        "category": "tech",
        "published_at": published_at,
        **extra,
    }


def _fetch(http, category="tech", **kwargs) -> NewsHeadlines:
    return asyncio.run(NoozraClient(http_client=http).fetch_headlines(category, **kwargs))


# --- happy path -----------------------------------------------------------


def test_fetch_returns_parsed_headlines():
    http = FakeHttpClient({"articles": [_article()]})

    result = _fetch(http)

    assert len(result.headlines) == 1
    item = result.headlines[0]
    assert item.headline == "Something happened"
    assert item.publication == "Example Times"
    assert item.description == "A description."
    assert item.source_url == "https://example.com/1"
    assert item.category == "tech"


def test_request_sends_normalized_category_and_caches():
    http = FakeHttpClient({"articles": [_article()]})

    _fetch(http, "  TECH  ")

    assert http.parameters()["category"] == "tech"
    assert http.calls[0]["cache_ttl"] == TTL["news"]


def test_headlines_come_back_newest_first():
    http = FakeHttpClient(
        {
            "articles": [
                _article(headline="older", url="https://example.com/1",
                         published_at="2026-08-28T09:00:00Z"),
                _article(headline="newest", url="https://example.com/2",
                         published_at="2026-08-30T09:00:00Z"),
                _article(headline="middle", url="https://example.com/3",
                         published_at="2026-08-29T09:00:00Z"),
            ]
        }
    )

    assert [item.headline for item in _fetch(http).headlines] == [
        "newest",
        "middle",
        "older",
    ]


def test_mixed_aware_and_naive_timestamps_still_sort():
    http = FakeHttpClient(
        {
            "articles": [
                _article(headline="naive", url="https://example.com/1",
                         published_at="2026-08-28T09:00:00"),
                _article(headline="aware", url="https://example.com/2",
                         published_at="2026-08-30T09:00:00Z"),
            ]
        }
    )

    assert [item.headline for item in _fetch(http).headlines] == ["aware", "naive"]


def test_duplicate_urls_are_collapsed():
    http = FakeHttpClient(
        {
            "articles": [
                _article(headline="first copy", url="https://example.com/same"),
                _article(headline="second copy", url="https://example.com/same"),
            ]
        }
    )

    result = _fetch(http)

    assert [item.headline for item in result.headlines] == ["first copy"]


def test_limit_caps_the_result():
    http = FakeHttpClient(
        {
            "articles": [
                _article(url=f"https://example.com/{index}") for index in range(10)
            ]
        }
    )

    assert len(_fetch(http, limit=3).headlines) == 3


def test_limit_of_zero_returns_nothing():
    http = FakeHttpClient({"articles": [_article()]})

    assert _fetch(http, limit=0).headlines == []


def test_default_limit_is_twenty():
    http = FakeHttpClient(
        {
            "articles": [
                _article(url=f"https://example.com/{index}") for index in range(30)
            ]
        }
    )

    assert len(_fetch(http).headlines) == 20


def test_missing_category_falls_back_to_the_requested_one():
    http = FakeHttpClient({"articles": [_article(category=None)]})

    assert _fetch(http, "science").headlines[0].category == "science"


def test_missing_description_is_allowed():
    http = FakeHttpClient({"articles": [_article(description=None)]})

    assert _fetch(http).headlines[0].description is None


# --- resilient parsing ----------------------------------------------------


@pytest.mark.parametrize(
    "broken",
    [
        {"headline": "no url", "source": "X", "published_at": "2026-08-30T12:00:00Z"},
        {"url": "https://example.com/x", "source": "X"},
        {"headline": "bad date", "source": "X", "url": "https://example.com/y",
         "published_at": "sometime last week"},
        "not even a dict",
        None,
    ],
)
def test_one_malformed_article_does_not_sink_the_batch(broken):
    http = FakeHttpClient({"articles": [broken, _article(headline="good")]})

    result = _fetch(http)

    assert [item.headline for item in result.headlines] == ["good"]


def test_all_articles_malformed_raises_no_usable_articles():
    http = FakeHttpClient({"articles": [{"nope": True}, {"also": "nope"}]})

    with pytest.raises(NoUsableArticlesError) as err:
        _fetch(http)

    assert isinstance(err.value, NewsClientError)


def test_non_list_articles_raises_no_usable_articles():
    http = FakeHttpClient({"articles": {"headline": "not a list"}})

    with pytest.raises(NoUsableArticlesError):
        _fetch(http)


# --- error paths ----------------------------------------------------------


@pytest.mark.parametrize("payload", [{}, {"articles": []}, {"articles": None}])
def test_no_articles_raises_missing_articles(payload):
    with pytest.raises(MissingArticlesError) as err:
        _fetch(FakeHttpClient(payload), "politics")

    assert "politics" in str(err.value)
    assert isinstance(err.value, NewsClientError)


@pytest.mark.parametrize("category", ["", "   "])
def test_blank_category_raises_parameter_setting_error(category):
    with pytest.raises(ParameterSettingError):
        _fetch(FakeHttpClient(), category)


def test_http_errors_propagate():
    with pytest.raises(RuntimeError, match="network down"):
        _fetch(FakeHttpClient(RuntimeError("network down")))


# --- factory wiring -------------------------------------------------------


def test_factory_passes_the_shared_http_client_through():
    http = FakeHttpClient({"articles": [_article()]})
    client = get_news_client("noozra", http_client=http)

    assert client.http_client is http
    assert asyncio.run(client.fetch_headlines("tech")).headlines


def test_published_time_keeps_its_timezone():
    http = FakeHttpClient({"articles": [_article(published_at="2026-08-30T12:00:00Z")]})

    assert _fetch(http).headlines[0].published_time == datetime(
        2026, 8, 30, 12, 0, tzinfo=timezone.utc
    )
