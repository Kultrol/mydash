"""Tests for mydash.core.client.news.noozra."""

import asyncio

from unittest.mock import AsyncMock, MagicMock

import pytest

from mydash.core.client.http_api.http_api import HttpApiClient
from mydash.core.client.news.base import NewsClient
from mydash.core.client.news.factory import get_news_client
from mydash.core.client.news.providers.noozra.errors import (
    HeadlineSettingError,
    MissingArticlesError,
    MissingNewsHeadlinesError,
    ParameterSettingError,
)
from mydash.core.models.news import NewsHeadlines

# ======================================
# ***** Testing set_news_headlines *****
# ======================================

# -----------------------------------
# Stage 1: Parameter Input Validation | TESTING COMPLETE : 07/09/26
# -----------------------------------


@pytest.mark.parametrize(
    argnames="mock_category, expected_error",
    argvalues=[
        (2, ParameterSettingError),
        (None, ParameterSettingError),
        ({}, ParameterSettingError),
    ],
)
def test_set_news_headlines_bad_input_raise_parameter_setting_error(
    mock_category, expected_error
):
    news_client: NewsClient = get_news_client()
    with pytest.raises(expected_exception=expected_error) as err:
        asyncio.run(news_client.set_news_headlines(category=mock_category))

    assert isinstance(err.value, expected_error)


# -----------------------------
# Stage 2:  Response Checking | TESTING COMPLETE : 07/09/26
# ----------------------------


@pytest.mark.parametrize(
    argnames="mock_response, expected_error",
    argvalues=[
        ({}, MissingArticlesError),
        ({"error": "something bad"}, MissingArticlesError),
        ({"results": []}, MissingArticlesError),
    ],
)
def test_set_news_headlines_bad_api_response_rasied_missing_articles_error(
    monkeypatch, mock_response, expected_error
):
    news_client = get_news_client()

    mock_make_request = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(HttpApiClient, "make_request", mock_make_request)

    with pytest.raises(expected_error) as err:
        asyncio.run(news_client.set_news_headlines(category="politics"))
    assert isinstance(err.value, expected_error)


# ---------------------------------------------------
# Stage 3:  Headline Creation and Headlines Setting | TESTING COMPLETE : 07/09/26
# ---------------------------------------------------


@pytest.mark.parametrize(
    argnames="mock_response, expected_error",
    argvalues=[
        ({"articles": [{"bob": "joe"}]}, HeadlineSettingError),
        (
            {"articles": [{"headline": "Hey Joe.(Check JimiHendrix's 'Hey Joe')"}]},
            HeadlineSettingError,
        ),
    ],
)
def test_set_news_headlines_failed_headline_validation(
    monkeypatch, mock_response, expected_error
):
    news_client = get_news_client()

    mock_make_request = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(HttpApiClient, "make_request", mock_make_request)

    with pytest.raises(expected_error) as err:
        asyncio.run(news_client.set_news_headlines(category="politics"))
    assert isinstance(err.value, expected_error)


# ======================================
# ***** Testing get_news_headlines ***** | TESTING COMPLETE : 07/09/26
# ======================================


# Test case "happy path" in which 'set_headlines' properly fetched and set headlines, which allowed 'get_headlines' to return a NewsHeadlines type.
@pytest.mark.parametrize(
    argnames="mock_params, mock_api_response",
    argvalues=[
        (
            "politics",
            {
                "articles": [
                    {
                        "headline": "Some scandle",
                        "source": "credible outlet",
                        "description": "famous people involved in a scandle you'll forget about tomorrow.",
                        "url": "https://whocares.com",
                        "category": "politics",
                        "published_at": "2026-07-09T17:06:03Z",
                    }
                ]
            },
        )
    ],
)
def test_get_news_headlines_valid_api_response_return_news_headlines(
    monkeypatch: pytest.MonkeyPatch, mock_params, mock_api_response
):
    news_client = get_news_client()

    mock_response = AsyncMock(return_value=mock_api_response)
    monkeypatch.setattr(HttpApiClient, "make_request", mock_response)

    asyncio.run(news_client.set_news_headlines(category=mock_params))

    client_headlines = news_client.get_news_headlines()

    assert isinstance(client_headlines, NewsHeadlines)


# Test case in which 'self.news_headlines' is of type None -> raises MissingNewsHeadlinesError
def test_get_news_headlines_missing_headlines_raises_missing_headlines_error():
    news_client = get_news_client()

    with pytest.raises(MissingNewsHeadlinesError) as err:
        _ = news_client.get_news_headlines()
    assert isinstance(err.value, MissingNewsHeadlinesError)
