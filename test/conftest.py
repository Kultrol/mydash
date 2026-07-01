"""Shared pytest fixtures for mydash client tests."""

import pytest


@pytest.fixture
def mock_urls():
    """Canonical API base URLs used across client implementations."""
    return {
        "geocoding": "https://geocoding-api.open-meteo.com/v1/search",
        "weather": "https://api.open-meteo.com/v1/forecast",
        "news": "https://noozra.com/api/articles",
        "stocks": "https://data.alpaca.markets/v2/stocks/bars/latest",
    }
