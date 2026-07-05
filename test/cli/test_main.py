"""Tests for mydash.cli.main.

Target: Typer app and commands in cli/main.py
Strategy: use typer.testing.CliRunner; mock factory functions or patch client methods
Depends on: conftest fixtures for mocked geocoding/weather/news/stock responses
"""

# --- weather command ---
#
# TODO(testing): weather runs without error via CliRunner —
#   patch get_geocoding_client and get_weather_client to return mocks
#
# TODO(testing): weather orchestrates geocoding → weather pipeline —
#   verify set_coordinates called on geocoding client,
#   Coordinates passed to weather client.set_coordinates,
#   set_weather_forecast() and get_weather_forecast() called

# --- news command ---
#
# TODO(testing): news command — fetch headlines with configurable category;
#   patch get_news_client, assert set_news_headlines(category=...) called

# --- stocks command ---
#
# TODO(testing): stocks command — fetch quotes/bars when Alpaca env vars present;
#   patch get_stock_client and alpaca_env fixture

# --- brief command ---
#
# TODO(testing): brief command — aggregates weather, news, stocks output;
#   mock all three factories and assert each pipeline invoked once