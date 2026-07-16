from mydash.client.news.factory import get_news_client
from mydash.models.news import NewsHeadlines


class NewsService:
    def __init__(self, news_provider: str = "noozra") -> None:
        self.news_client = get_news_client(provider=news_provider)

    async def fetch_news(self, category: str) -> NewsHeadlines:
        await self.news_client.set_news_headlines(category=category)
        return self.news_client.get_news_headlines()
