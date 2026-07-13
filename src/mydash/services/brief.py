"""Brief orchestration: compose weather, news, and stocks into one DTO."""

from pydantic import BaseModel

from mydash.client.news.factory import get_news_client
from mydash.client.stocks.factory import get_stock_client
from mydash.models.news import NewsHeadlines
from mydash.models.stocks import StockBars, StockQuotes
from mydash.models.weather import MultiDayForecast
from mydash.services.stocks import StockService
from mydash.services.weather import WeatherService

DEFAULT_CITY = "Miami"
DEFAULT_NEWS_CATEGORY = "tech"
DEFAULT_SYMBOLS = ["SPY", "AAPL", "MSFT"]


class DailyBrief(BaseModel):
    """Aggregated snapshot for the daily brief command."""

    headlines: NewsHeadlines
    stock_quotes: StockQuotes
    stock_bars: StockBars
    weather: MultiDayForecast
    city: str
    news_category: str
    symbols: list[str]


class BriefService:
    """Fetch all brief domains and return a :class:`DailyBrief` (fail-fast)."""

    def build(self) -> DailyBrief:
        """Fetch weather, news, and stocks; return one composed brief."""
        city = DEFAULT_CITY
        news_category = DEFAULT_NEWS_CATEGORY
        symbols = list(DEFAULT_SYMBOLS)

        weather = WeatherService().fetch_today_weather_forecast(city=city)
        headlines = self._fetch_headlines(news_category)
        stock_quotes, stock_bars = StockService(
            stock_ticker_symbols=symbols
        ).fetch_stock_bars_and_quotes()

        return DailyBrief(
            headlines=headlines,
            stock_quotes=stock_quotes,
            stock_bars=stock_bars,
            weather=weather,
            city=city,
            news_category=news_category,
            symbols=symbols,
        )

    def _fetch_headlines(self, category: str) -> NewsHeadlines:
        news_client = get_news_client()
        news_client.set_news_headlines(category=category)
        return news_client.get_news_headlines()
