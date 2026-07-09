"""Tests for mydash.client.news.factory."""

import pytest

from mydash.client.news.base import NewsClient
from mydash.client.news.base_errors import NewsFactoryError
from mydash.client.news.factory import get_news_client
from mydash.client.news.providers.noozra.noozra import NoozraClient


@pytest.mark.parametrize(
    argnames="mock_provider, expected_result",
    argvalues=[("noozra", NoozraClient)],
)
def test_get_noozra_client_valid_provider(mock_provider, expected_result) -> None:
    news_client: NewsClient = get_news_client(mock_provider)
    assert isinstance(news_client, expected_result)


@pytest.mark.parametrize(
    argnames="mock_provider, expected_error",
    argvalues=[
        ("", NewsFactoryError),
        (None, NewsFactoryError),
        (2102, NewsFactoryError),
        ("nooz", NewsFactoryError),
        ("bad", NewsFactoryError),
    ],
)
def test_get_news_client_invalid_provider(mock_provider, expected_error) -> None:
    with pytest.raises(expected_error):
        get_news_client(mock_provider)
