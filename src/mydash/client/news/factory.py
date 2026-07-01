"""Factory for news client instances.

Selects a concrete provider by name. The ``**config`` kwargs are reserved for
future settings such as API keys, default categories, or article limits.
"""

from mydash.client.news.base import NewsClient
from .noozra import NoozraClient


def get_news_client(provider: str = "noozra", **config) -> NewsClient:
    """Return a news client for the given *provider*.

    :param provider: Provider identifier. Currently only ``"noozra"`` is supported.
    :param config: Reserved for future provider-specific configuration.
    :raises ValueError: If *provider* is not recognized.
    """
    if provider == "noozra":
        return NoozraClient()
    else:
        raise ValueError("Unknown provider. Please choose a valid provider.")