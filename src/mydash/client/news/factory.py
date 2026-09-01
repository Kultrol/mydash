"""Factory for news client instances.

Selects a concrete provider by name.
"""

from mydash.client.http_api.http_api import HttpApiClient
from mydash.client.news.base import NewsClient
from mydash.client.news.base_errors import NewsFactoryError
from mydash.client.news.providers.noozra.noozra import NoozraClient


def get_news_client(
    provider: str = "noozra",
    *,
    http_client: HttpApiClient | None = None,
) -> NewsClient:
    """Return a news client for the given *provider*.

    :param provider: Provider identifier. Currently only ``"noozra"`` is supported.
    :param http_client: Shared HTTP client to reuse connections and cache.
    :raises NewsFactoryError: If *provider* is not recognized.
    """
    if provider == "noozra":
        return NoozraClient(http_client=http_client)
    raise NewsFactoryError(provider=provider)
