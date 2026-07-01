"""CLI entry point for mydash.

Uses Typer for command routing and Rich for terminal output. Factory imports below
are the backends for future domain commands; only ``greeting`` exists today as a
packaging smoke-test.

Intended command flow (not yet implemented):
    weather      geocoding client → weather client → Rich display
    news         news client → Rich display
    stocks       stock client → Rich display (requires Alpaca API keys in .env)
    daily-brief  orchestrate all domains into a single briefing
"""

import typer
from rich.console import Console
from rich.pretty import pprint
from rich.traceback import install

from mydash.client.geocoding.factory import get_geocoding_client
from mydash.client.news.factory import get_news_client
from mydash.client.stocks.factory import get_stock_client

# TODO(connection): wire up CLI commands that use these factories:
#   - ``weather`` — resolve city via get_geocoding_client, pass Coordinates to get_weather_client
#   - ``news`` — fetch headlines via get_news_client
#   - ``stocks`` — fetch quotes via get_stock_client (STOCK_ALPACA_API_KEY_ID / SECRET in .env)
#   - ``daily-brief`` — aggregate all domains above into one Rich layout
from mydash.client.weather.factory import get_weather_client

# Rich traceback handler for clearer dev-time error output
install(show_locals=True)

console = Console()
app = typer.Typer()


@app.command("greeting")
def hello_world():
    """Smoke-test command to verify ``uv run`` works; not part of the app surface."""

    console.print("Hello World")


if __name__ == "__main__":
    app()