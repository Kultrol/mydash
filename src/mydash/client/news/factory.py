"""Factory for news client instances.

Selects a concrete provider by name.
"""

from mydash.client.news.base import NewsClient
from mydash.client.news.base_errors import NewsFactoryError
from mydash.client.news.providers.noozra.noozra import NoozraClient


def get_news_client(provider: str = "noozra") -> NewsClient:
    """Return a news client for the given *provider*.

    :param provider: Provider identifier. Currently only ``"noozra"`` is supported.
    :raises ValueError: If *provider* is not recognized.
    """
    if provider == "noozra":
        return NoozraClient()
    else:
        raise NewsFactoryError(provider=provider)
