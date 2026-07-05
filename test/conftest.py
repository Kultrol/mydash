"""Shared pytest fixtures for mydash tests.

Implement fixtures here before writing client/CLI tests. Prefer mocking at the
httpx layer (``client.client.get``) or patching ``_make_request`` on clients.
"""

# --- Fixtures to implement ---
#
# TODO(testing): mock_urls — return dict of canonical API base URLs:
#   geocoding: https://geocoding-api.open-meteo.com/v1/search
#   weather:   https://api.open-meteo.com/v1/forecast
#   news:      https://noozra.com/api/articles
#   stocks:    https://data.alpaca.markets/v2/stocks/bars/latest
#
# TODO(testing): alpaca_env — monkeypatch STOCK_ALPACA_API_KEY_ID and
#   STOCK_ALPACA_API_SECRET_KEY for AlpacaClient construction in stock tests.
#
# TODO(testing): sample_geocoding_response — reusable JSON with results array
#   (latitude/longitude) for geocoding client tests.
#
# TODO(testing): sample_hourly_forecast — reusable hourly time-series JSON
#   spanning multiple calendar days for weather parser tests.
#
# TODO(testing): sample_noozra_articles — reusable articles array for news tests.
#
# TODO(testing): sample_alpaca_quotes — reusable quotes dict keyed by ticker
#   (ap, bp, t fields) for stock quote parsing tests.
#
# TODO(testing): sample_alpaca_bars — reusable bars dict keyed by ticker
#   (o, c, t fields) for stock bar parsing tests.