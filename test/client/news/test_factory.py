"""Tests for mydash.client.news.factory."""

import pytest

from mydash.client.news.base import NewsClient
from src.mydash.client.news.factory import get_news_client
from src.mydash.client.news.noozra import NoozraClient


@pytest.mark.parametrize(
    argnames="mock_provider, expected_result",
    argvalues=[("noozra", NoozraClient)],
)
def test_get_noozra_client_valid_provider(mock_provider, expected_result) -> None:
    news_client: NewsClient = get_news_client(mock_provider)
    assert isinstance(news_client, expected_result)


@pytest.mark.parametrize(
    argnames="mock_provider, expected_result",
    argvalues=[
        ("", ValueError),
        (None, ValueError),
        (2102, ValueError),
        ("nooz", ValueError),
        ("bad", ValueError),
    ],
)
def test_get_news_client_invalid_provider(mock_provider, expected_result) -> None:
    with pytest.raises(ValueError):
        get_news_client(mock_provider)
