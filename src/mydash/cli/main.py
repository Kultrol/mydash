import os

import typer
from rich.console import Console
from rich.pretty import pprint

from src.mydash.client.weather.factory import get_weather_client
from src.mydash.client.geocoding.factory import get_geocoding_client
from src.mydash.client.stocks.factory import get_stock_client
from src.mydash.client.news.factory import get_news_client

from rich.traceback import install

import os

#Custom Rich Traceback displays
install(show_locals=True)


console = Console()
app = typer.Typer()

@app.command("greeting")
def hello_world():

    console.print("Hello World")





if __name__ == "__main__":
    app()
