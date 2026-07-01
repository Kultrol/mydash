"""Tests for mydash.client.weather.open_meteo.

Target: OpenMeteoClient
Usage pattern: set_coordinates(Coordinates) then set_weather_forecast() then get_weather_forecast()
Strategy: patch _make_request with sample hourly JSON; use Coordinates from geocoding.schemas
Depends on: conftest.sample_hourly_forecast
"""

# --- Coordinate guards ---
#
# TODO(testing): set_weather_forecast without prior set_coordinates raises ValueError
#   with message "Coordinates must be set"
#
# TODO(testing): get_weather_forecast without coordinates raises ValueError

# --- Forecast parsing ---
#
# TODO(testing): multi-day mock response appends all days including the final day —
#   use hourly times spanning 2+ calendar days; assert len(forecast.days) matches
#
# TODO(testing): HourForecast.hour is int (e.g. 14), not str —
#   assert isinstance(hour.hour, int)
#
# TODO(testing): all hourly fields mapped from API keys —
#   temperature_2m, apparent_temperature, precipitation_probability, precipitation,
#   weather_code, cloud_cover, wind_speed_10m, uv_index

# --- _make_request / HTTP errors ---
#
# TODO(testing): HTTP error from client.client.get propagates httpx.HTTPError —
#   mock raise_for_status failure or connection error