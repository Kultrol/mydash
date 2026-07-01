import typer
from rich.console import Console
from rich.pretty import pprint
from rich.traceback import install

from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.news.factory import get_news_client
from mydash.client.stocks.factory import get_stock_client

# TODO: wire up CLI commands that use these factories once real commands are added
from mydash.client.weather.factory import get_weather_client

# Custom Rich Traceback displays
install(show_locals=True)


console = Console()
app = typer.Typer()


@app.command("greeting")
def hello_world():
    """Smoke-test command to verify `uv run` works; not part of the app surface."""

    console.print("Hello World")


if __name__ == "__main__":
    app()
