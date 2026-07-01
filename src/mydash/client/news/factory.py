from mydash.client.news.base import NewsClient
from .noozra import NoozraClient


def get_news_client(provider : str = "noozra", **config) -> NewsClient:
    if provider == "noozra":
        return NoozraClient()
    else:
        raise ValueError("Unknown provider. Please choose a valid provider.")