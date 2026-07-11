"""CLI entry point for mydash.

Uses Typer for command routing and Rich for terminal output. Commands currently call
client factories directly (two-layer); the target is cli → services → client, but
how to migrate without a big-bang rewrite is still being explored.

Existing commands: ``weather``, ``news``, ``stocks``, ``brief`` (chains the others).
"""

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.traceback import install

from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.news.factory import get_news_client
from mydash.client.stocks.factory import get_stock_client
from mydash.client.weather.factory import get_weather_client

# Rich traceback handler for clearer dev-time error output
install(show_locals=True)

console = Console()
app = typer.Typer()

load_dotenv()

# TODO(cli): city/category/symbols are hardcoded — explore Typer options or a shared
# config module once services exist; unclear yet whether config lives in cli or services.
# TODO(cli): brief() calls command functions directly — may want a shared orchestration
# path (service layer?) so brief and individual commands don't duplicate pipeline logic.
# TODO(cli): console.print(models) is a dev placeholder — explore moving Rich layout to
# cli/renderers/ once presentation needs are clearer.


@app.command("weather")
def weather_watch():
    """Fetch and display a weather forecast for a city."""
    geocoding_client = get_geocoding_client()
    geocoding_client.set_coordinates("Miami")
    coordinates = geocoding_client.get_coordinates()

    weather_client = get_weather_client()
    weather_client.set_coordinates(coordinates)
    weather_client.set_weather_forecast(forecast_length=1, backwardcast_length=1)
    console.print(weather_client.get_weather_forecast())


@app.command("stocks")
def stock_watch():
    stock_client = get_stock_client()
    stock_client.set_current_stock_quotes(symbols=["SPY", "AAPL", "MSFT"])
    stock_quotes = stock_client.get_current_stock_quotes()
    stock_client.set_current_stock_bars(symbols=["SPY", "AAPL", "MSFT"])
    stock_bars = stock_client.get_current_stock_bars()
    console.print(stock_quotes)
    console.print(stock_bars)


@app.command("news")
def news_watch():
    news_client = get_news_client()
    news_client.set_news_headlines(category="politics")
    news_headlines = news_client.get_news_headlines()
    console.print(news_headlines)


@app.command("brief")
def brief():
    weather_watch()
    news_watch()
    stock_watch()


if __name__ == "__main__":
    app()
