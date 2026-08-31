"""Tests for UserConfigurationService.

Strategy: tmp_path SQLite files (never the real user-data dir); mock geocoding
for set_city. Cover seeding, reload, validation, watch list, and the one-time
import of the pre-SQLite JSON config.
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from mydash.models.geocoding import Coordinates
from mydash.services.user_config import (
    DEFAULT_CITY,
    DEFAULT_NEWS_CATEGORY,
    DEFAULT_SYMBOLS,
    DEFAULT_WEATHER_UNITS,
    LEGACY_CONFIG_FILENAME,
    UserConfig,
    UserConfigurationService,
    legacy_config_path,
    normalize_symbol,
)
from mydash.storage.database import Database


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "mydash" / "mydash.db"


@pytest.fixture
def service(db_path: Path):
    svc = UserConfigurationService(db_path=db_path)
    yield svc
    svc.close()


def _write_setting(db_path: Path, key: str, raw_value: str) -> None:
    """Write a raw settings row, bypassing the service's own encoding."""
    with Database(db_path) as db, db.transaction() as conn:
        conn.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, raw_value, "2026-08-30T00:00:00Z"),
        )


# --- seeding and reload ---------------------------------------------------


def test_creates_default_config_in_new_database(db_path: Path, service):
    assert db_path.is_file()

    cfg = service.get_configuration()
    assert cfg.city == DEFAULT_CITY
    assert cfg.news_category == DEFAULT_NEWS_CATEGORY
    assert cfg.stock_symbols == DEFAULT_SYMBOLS
    assert cfg.weather_units == DEFAULT_WEATHER_UNITS
    assert cfg.provider_weather == "open-meteo"
    assert cfg.provider_news == "noozra"
    assert cfg.provider_stocks == "alpaca"
    assert cfg.provider_geocoding == "open-meteo"


def test_reload_sees_persisted_values(db_path: Path):
    with UserConfigurationService(db_path=db_path) as svc:
        svc.set_news_category("politics")
        svc.set_weather_forecast_units("imperial")
        svc.add_stock_symbol("nvda")

    with UserConfigurationService(db_path=db_path) as reloaded:
        cfg = reloaded.get_configuration()

    assert cfg.news_category == "politics"
    assert cfg.weather_units == "imperial"
    assert cfg.stock_symbols == [*DEFAULT_SYMBOLS, "NVDA"]


def test_set_configuration_persists(db_path: Path):
    with UserConfigurationService(db_path=db_path) as svc:
        svc.set_configuration(
            UserConfig(city="Seattle", weather_units="imperial", stock_symbols=["TSLA"])
        )

    with UserConfigurationService(db_path=db_path) as reloaded:
        assert reloaded.get_city() == "Seattle"
        assert reloaded.get_weather_forecast_units() == "imperial"
        assert reloaded.get_stock_symbols() == ["TSLA"]


def test_reset_restores_defaults(db_path: Path):
    with UserConfigurationService(db_path=db_path) as svc:
        svc.set_news_category("politics")
        svc.set_stock_symbols(["TSLA"])

        restored = svc.reset()

    assert restored.news_category == DEFAULT_NEWS_CATEGORY
    assert restored.stock_symbols == DEFAULT_SYMBOLS

    with UserConfigurationService(db_path=db_path) as reloaded:
        assert reloaded.get_news_category() == DEFAULT_NEWS_CATEGORY


def test_service_accepts_an_injected_database(db_path: Path):
    with Database(db_path) as db:
        svc = UserConfigurationService(database=db)
        svc.set_news_category("science")

        # Closing the service must not close a database it does not own.
        svc.close()
        assert db.connect().execute("SELECT COUNT(*) FROM settings").fetchone()[0]


# --- watch list -----------------------------------------------------------


def test_add_and_remove_stock_symbols(service):
    service.add_stock_symbol("goog")
    assert "GOOG" in service.get_stock_symbols()

    service.add_stock_symbol("GOOG")  # idempotent
    assert service.get_stock_symbols().count("GOOG") == 1

    service.remove_stock_symbol("goog")
    assert "GOOG" not in service.get_stock_symbols()

    with pytest.raises(ValueError, match="not in list"):
        service.remove_stock_symbol("ZZZZ")


def test_watch_list_keeps_insertion_order(db_path: Path):
    with UserConfigurationService(db_path=db_path) as svc:
        svc.set_stock_symbols([])
        for symbol in ("nvda", "tsla", "amd"):
            svc.add_stock_symbol(symbol)

    with UserConfigurationService(db_path=db_path) as reloaded:
        assert reloaded.get_stock_symbols() == ["NVDA", "TSLA", "AMD"]


def test_set_stock_symbols_replaces_and_dedupes(service):
    service.set_stock_symbols(["spy", "SPY", "brk.b"])
    assert service.get_stock_symbols() == ["SPY", "BRK.B"]


@pytest.mark.parametrize("symbol", ["", "   ", "AA PL", "TOOLONGSYMBOL", "$SPY", "1SPY"])
def test_invalid_symbols_are_rejected(service, symbol):
    with pytest.raises(ValueError):
        service.add_stock_symbol(symbol)


@pytest.mark.parametrize(
    "raw, expected",
    [(" aapl ", "AAPL"), ("brk.b", "BRK.B"), ("rds-a", "RDS-A")],
)
def test_normalize_symbol(raw, expected):
    assert normalize_symbol(raw) == expected


# --- scalar preferences ---------------------------------------------------


def test_weather_units_validation(service):
    with pytest.raises(ValueError, match="invalid weather units"):
        service.set_weather_forecast_units("kelvin")

    service.set_weather_forecast_units("imperial")
    assert service.get_weather_forecast_units() == "imperial"


def test_news_category(service):
    service.set_news_category("  politics ")
    assert service.get_news_category() == "politics"

    with pytest.raises(ValueError):
        service.set_news_category("   ")


def test_provider_validation(service):
    with pytest.raises(ValueError, match="invalid provider"):
        service.set_weather_provider("not-a-provider")
    with pytest.raises(ValueError, match="invalid provider"):
        service.set_news_provider("not-a-provider")
    with pytest.raises(ValueError, match="invalid provider"):
        service.set_stock_provider("not-a-provider")
    with pytest.raises(ValueError, match="invalid provider"):
        service.set_geocoding_provider("not-a-provider")

    service.set_weather_provider("open-meteo")
    service.set_news_provider("noozra")
    service.set_stock_provider("alpaca")
    service.set_geocoding_provider("open-meteo")
    assert service.get_weather_provider() == "open-meteo"
    assert service.get_news_provider() == "noozra"
    assert service.get_stock_provider() == "alpaca"
    assert service.get_geocoding_provider() == "open-meteo"


# --- corrupt storage ------------------------------------------------------


def test_corrupt_setting_value_raises_value_error(db_path: Path):
    UserConfigurationService(db_path=db_path).close()
    _write_setting(db_path, "city", "{not valid json")

    with pytest.raises(ValueError, match="not valid JSON"):
        UserConfigurationService(db_path=db_path)


def test_invalid_structure_raises_value_error(db_path: Path):
    UserConfigurationService(db_path=db_path).close()
    _write_setting(db_path, "coordinates", json.dumps({"latitude": 999, "longitude": 0}))

    with pytest.raises(ValueError, match="invalid structure"):
        UserConfigurationService(db_path=db_path)


def test_unknown_setting_keys_are_ignored(db_path: Path):
    UserConfigurationService(db_path=db_path).close()
    _write_setting(db_path, "future_preference", json.dumps("surprise"))

    with UserConfigurationService(db_path=db_path) as svc:
        assert svc.get_city() == DEFAULT_CITY


# --- city / geocoding -----------------------------------------------------


def test_set_city_geocodes_and_persists(db_path: Path, mocker):
    coords = Coordinates(latitude=40.71, longitude=-74.01)
    geo = MagicMock()
    geo.set_coordinates = AsyncMock()
    geo.get_coordinates.return_value = coords
    mocker.patch("mydash.services.user_config.get_geocoding_client", return_value=geo)

    with UserConfigurationService(db_path=db_path) as svc:
        asyncio.run(svc.set_city("New York"))

        geo.set_coordinates.assert_awaited_once_with(city="New York")
        assert svc.get_city() == "New York"
        assert svc.get_coordinates() == coords

    with UserConfigurationService(db_path=db_path) as reloaded:
        assert reloaded.get_city() == "New York"
        assert reloaded.get_coordinates() == coords


def test_set_city_rejects_blank(service):
    with pytest.raises(ValueError, match="non-empty"):
        asyncio.run(service.set_city("   "))


# --- legacy JSON import ---------------------------------------------------


def _write_legacy(tmp_path: Path, config: UserConfig) -> Path:
    path = tmp_path / LEGACY_CONFIG_FILENAME
    path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    return path


def test_legacy_json_is_imported_and_renamed(tmp_path: Path, db_path: Path):
    legacy = _write_legacy(
        tmp_path,
        UserConfig(city="Boston", news_category="science", stock_symbols=["TSLA"]),
    )

    with UserConfigurationService(db_path=db_path, legacy_json_path=legacy) as svc:
        assert svc.get_city() == "Boston"
        assert svc.get_news_category() == "science"
        assert svc.get_stock_symbols() == ["TSLA"]

    assert not legacy.exists()
    assert legacy.with_suffix(".json.migrated").is_file()


def test_legacy_json_is_not_reimported_over_existing_settings(
    tmp_path: Path, db_path: Path
):
    with UserConfigurationService(db_path=db_path) as svc:
        svc.set_news_category("politics")

    legacy = _write_legacy(tmp_path, UserConfig(city="Boston"))

    with UserConfigurationService(db_path=db_path, legacy_json_path=legacy) as svc:
        assert svc.get_city() == DEFAULT_CITY
        assert svc.get_news_category() == "politics"

    assert legacy.is_file()


def test_corrupt_legacy_json_falls_back_to_defaults(tmp_path: Path, db_path: Path):
    legacy = tmp_path / LEGACY_CONFIG_FILENAME
    legacy.write_text("{not valid json", encoding="utf-8")

    with UserConfigurationService(db_path=db_path, legacy_json_path=legacy) as svc:
        assert svc.get_city() == DEFAULT_CITY

    # Left in place so a human can look at it.
    assert legacy.is_file()


def test_custom_db_path_never_touches_the_real_legacy_file(db_path: Path):
    svc = UserConfigurationService(db_path=db_path)
    assert svc._legacy_json_path is None
    svc.close()


def test_legacy_config_path_points_at_the_old_json_file():
    assert legacy_config_path().name == LEGACY_CONFIG_FILENAME
