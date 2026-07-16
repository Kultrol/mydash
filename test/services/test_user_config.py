"""Tests for UserConfigurationService.

Strategy: use tmp_path config files (never real platformdirs paths); mock
geocoding for set_city. Cover create/load, validation, symbols, providers.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from mydash.models.geocoding import Coordinates
from mydash.services.user_config import (
    DEFAULT_CITY,
    DEFAULT_NEWS_CATEGORY,
    DEFAULT_SYMBOLS,
    DEFAULT_WEATHER_UNITS,
    UserConfig,
    UserConfigurationService,
)


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    return tmp_path / "mydash" / "config.json"


def test_creates_default_config_file(config_path: Path):
    svc = UserConfigurationService(config_path=config_path)

    assert config_path.is_file()
    cfg = svc.get_configuration()
    assert cfg.city == DEFAULT_CITY
    assert cfg.news_category == DEFAULT_NEWS_CATEGORY
    assert cfg.stock_symbols == DEFAULT_SYMBOLS
    assert cfg.weather_units == DEFAULT_WEATHER_UNITS
    assert cfg.provider_weather == "open-meteo"
    assert cfg.provider_news == "noozra"
    assert cfg.provider_stocks == "alpaca"
    assert cfg.provider_geocoding == "open-meteo"


def test_loads_existing_config(config_path: Path):
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        UserConfig(
            city="Boston",
            news_category="politics",
            stock_symbols=["SPY"],
            weather_units="imperial",
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )

    svc = UserConfigurationService(config_path=config_path)
    cfg = svc.get_configuration()
    assert cfg.city == "Boston"
    assert cfg.news_category == "politics"
    assert cfg.stock_symbols == ["SPY"]
    assert cfg.weather_units == "imperial"


def test_set_configuration_persists(config_path: Path):
    svc = UserConfigurationService(config_path=config_path)
    updated = UserConfig(city="Seattle", weather_units="imperial")
    svc.set_configuration(updated)

    reloaded = UserConfigurationService(config_path=config_path)
    assert reloaded.get_city() == "Seattle"
    assert reloaded.get_weather_forecast_units() == "imperial"


def test_weather_units_validation(config_path: Path):
    svc = UserConfigurationService(config_path=config_path)
    with pytest.raises(ValueError, match="invalid weather units"):
        svc.set_weather_forecast_units("kelvin")

    svc.set_weather_forecast_units("imperial")
    assert svc.get_weather_forecast_units() == "imperial"


def test_add_and_remove_stock_symbols(config_path: Path):
    svc = UserConfigurationService(config_path=config_path)
    svc.add_stock_symbol("goog")
    assert "GOOG" in svc.get_stock_symbols()

    svc.add_stock_symbol("GOOG")  # idempotent
    assert svc.get_stock_symbols().count("GOOG") == 1

    svc.remove_stock_symbol("goog")
    assert "GOOG" not in svc.get_stock_symbols()

    with pytest.raises(ValueError, match="not in list"):
        svc.remove_stock_symbol("ZZZZ")


def test_news_category(config_path: Path):
    svc = UserConfigurationService(config_path=config_path)
    svc.set_news_category("  politics ")
    assert svc.get_news_category() == "politics"

    with pytest.raises(ValueError):
        svc.set_news_category("   ")


def test_provider_validation(config_path: Path):
    svc = UserConfigurationService(config_path=config_path)

    with pytest.raises(ValueError, match="invalid provider"):
        svc.set_weather_provider("not-a-provider")
    with pytest.raises(ValueError, match="invalid provider"):
        svc.set_news_provider("not-a-provider")
    with pytest.raises(ValueError, match="invalid provider"):
        svc.set_stock_provider("not-a-provider")
    with pytest.raises(ValueError, match="invalid provider"):
        svc.set_geocoding_provider("not-a-provider")

    svc.set_weather_provider("open-meteo")
    svc.set_news_provider("noozra")
    svc.set_stock_provider("alpaca")
    svc.set_geocoding_provider("open-meteo")
    assert svc.get_weather_provider() == "open-meteo"
    assert svc.get_news_provider() == "noozra"
    assert svc.get_stock_provider() == "alpaca"
    assert svc.get_geocoding_provider() == "open-meteo"


def test_corrupt_json_raises_value_error(config_path: Path):
    config_path.parent.mkdir(parents=True)
    config_path.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(ValueError, match="not valid JSON"):
        UserConfigurationService(config_path=config_path)


def test_invalid_structure_raises_value_error(config_path: Path):
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        '{"city": "Miami", "coordinates": {"latitude": 999, "longitude": 0}}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid structure"):
        UserConfigurationService(config_path=config_path)


def test_set_city_geocodes(config_path: Path, mocker):
    coords = Coordinates(latitude=40.71, longitude=-74.01)
    geo = MagicMock()
    geo.set_coordinates = AsyncMock()
    geo.get_coordinates.return_value = coords
    mocker.patch(
        "mydash.services.user_config.get_geocoding_client", return_value=geo
    )

    svc = UserConfigurationService(config_path=config_path)
    asyncio.run(svc.set_city("New York"))

    geo.set_coordinates.assert_awaited_once_with(city="New York")
    assert svc.get_city() == "New York"
    assert svc.get_coordinates() == coords

    reloaded = UserConfigurationService(config_path=config_path)
    assert reloaded.get_city() == "New York"
    assert reloaded.get_coordinates() == coords
