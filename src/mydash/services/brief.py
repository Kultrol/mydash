"""Brief orchestration: compose weather, news, and stocks into one DTO."""

from pydantic import BaseModel

from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.news.factory import get_news_client
from mydash.client.stocks.factory import get_stock_client
from mydash.client.weather.factory import get_weather_client
from mydash.models.news import NewsHeadlines
from mydash.models.stocks import StockBars, StockQuotes
from mydash.models.weather import MultiDayForecast

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

        weather = self._fetch_weather(city)
        headlines = self._fetch_headlines(news_category)
        stock_quotes, stock_bars = self._fetch_stocks(symbols)

        return DailyBrief(
            headlines=headlines,
            stock_quotes=stock_quotes,
            stock_bars=stock_bars,
            weather=weather,
            city=city,
            news_category=news_category,
            symbols=symbols,
        )

    def _fetch_weather(self, city: str) -> MultiDayForecast:
        geocoding_client = get_geocoding_client()
        geocoding_client.set_coordinates(city)
        coordinates = geocoding_client.get_coordinates()

        weather_client = get_weather_client()
        weather_client.set_coordinates(coordinates)
        weather_client.set_weather_forecast(
            forecast_length=1, backwardcast_length=1
        )
        return weather_client.get_weather_forecast()

    def _fetch_headlines(self, category: str) -> NewsHeadlines:
        news_client = get_news_client()
        news_client.set_news_headlines(category=category)
        return news_client.get_news_headlines()

    def _fetch_stocks(
        self, symbols: list[str]
    ) -> tuple[StockQuotes, StockBars]:
        stock_client = get_stock_client()
        stock_client.set_current_stock_quotes(symbols=symbols)
        stock_quotes = stock_client.get_current_stock_quotes()
        stock_client.set_current_stock_bars(symbols=symbols)
        stock_bars = stock_client.get_current_stock_bars()
        return stock_quotes, stock_bars
