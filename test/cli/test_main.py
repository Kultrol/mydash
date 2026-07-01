"""Tests for mydash.cli.main.

Target: Typer app and commands in cli/main.py
Strategy: use typer.testing.CliRunner; mock factory functions or patch client methods
Depends on: conftest fixtures for mocked geocoding/weather responses
"""

# --- greeting command (current smoke/integration test) ---
#
# TODO(testing): greeting runs without error via CliRunner —
#   patch get_geocoding_client and get_weather_client to return mocks
#
# TODO(testing): greeting orchestrates geocoding → weather pipeline —
#   verify set_coordinates("Miami") called on geocoding client,
#   get_coordinates() returns Coordinates passed to weather client.set_coordinates,
#   set_weather_forecast() and get_weather_forecast() called

# --- Future commands (not yet implemented in src) ---
#
# TODO(testing): weather command — resolve city, display forecast via Rich
#   (implement after TODO(connection) in cli/main.py)
#
# TODO(testing): news command — fetch headlines with configurable category
#   (implement after TODO(connection) in cli/main.py)
#
# TODO(testing): stocks command — fetch quotes when Alpaca env vars present
#   (implement after TODO(connection) in cli/main.py)
#
# TODO(testing): daily-brief command — aggregate weather, news, stocks output
#   (implement after TODO(connection) in cli/main.py)