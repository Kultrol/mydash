"""User preferences, stored in SQLite.

:class:`UserConfigurationService` owns the ``settings`` and ``watchlist`` tables
and keeps an in-memory :class:`UserConfig` in sync with them. The daily brief
reads preferences from this service; the ``mydash set`` CLI mutates them.

Scalar preferences live one-per-row in ``settings`` so changing your city is a
single upsert rather than a rewrite of the whole file. Ticker symbols live in
``watchlist``, ordered, so the brief shows them in the order you added them.

First use seeds Miami / tech / common ticker defaults — the coordinates are
baked in, so nothing needs the network until you change the city.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Literal

from platformdirs import user_config_path
from pydantic import BaseModel, Field, ValidationError

from mydash.client.geocoding.factory import get_geocoding_client
from mydash.models.geocoding import Coordinates
from mydash.storage.database import APP_NAME, Database

WeatherUnits = Literal["metric", "imperial"]

# Defaults for a new database — coordinates are fixed so first create is offline.
DEFAULT_CITY = "Miami"
DEFAULT_COORDINATES = Coordinates(latitude=25.7617, longitude=-80.1918)
DEFAULT_NEWS_CATEGORY = "tech"
DEFAULT_SYMBOLS: list[str] = ["SPY", "AAPL", "MSFT"]
DEFAULT_WEATHER_UNITS: WeatherUnits = "metric"
DEFAULT_PROVIDER_WEATHER = "open-meteo"
DEFAULT_PROVIDER_STOCKS = "alpaca"
DEFAULT_PROVIDER_GEOCODING = "open-meteo"
DEFAULT_PROVIDER_NEWS = "noozra"


# Allowed values for provider / units setters (must match client factories).
KNOWN_WEATHER_PROVIDERS = frozenset({"open-meteo"})
KNOWN_STOCK_PROVIDERS = frozenset({"alpaca"})
KNOWN_GEOCODING_PROVIDERS = frozenset({"open-meteo"})
KNOWN_NEWS_PROVIDERS = frozenset({"noozra"})
KNOWN_WEATHER_UNITS = frozenset({"metric", "imperial"})

# Tickers are letters, digits, dots and dashes — enough for BRK.B and RDS-A.
SYMBOL_PATTERN: Final = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")

# Config file used before SQLite; imported once, then renamed out of the way.
LEGACY_CONFIG_FILENAME = "config.json"
LEGACY_MIGRATED_SUFFIX = ".migrated"

_UNSET: Final = object()


class UserConfig(BaseModel):
    """Persisted user preferences for mydash.

    Coordinates are stored with the city and refreshed when the city is set
    via :meth:`UserConfigurationService.set_city` (geocoding).
    """

    city: str = DEFAULT_CITY
    coordinates: Coordinates = Field(
        default_factory=lambda: DEFAULT_COORDINATES.model_copy()
    )
    news_category: str = DEFAULT_NEWS_CATEGORY
    stock_symbols: list[str] = Field(default_factory=lambda: list(DEFAULT_SYMBOLS))
    weather_units: WeatherUnits = DEFAULT_WEATHER_UNITS
    provider_weather: str = DEFAULT_PROVIDER_WEATHER
    provider_stocks: str = DEFAULT_PROVIDER_STOCKS
    provider_geocoding: str = DEFAULT_PROVIDER_GEOCODING
    provider_news: str = DEFAULT_PROVIDER_NEWS


#: Scalar fields persisted as individual ``settings`` rows.
_SETTING_FIELDS: Final[tuple[str, ...]] = (
    "city",
    "coordinates",
    "news_category",
    "weather_units",
    "provider_weather",
    "provider_stocks",
    "provider_geocoding",
    "provider_news",
)


def legacy_config_path() -> Path:
    """Return the pre-SQLite JSON config path (imported once on first run)."""
    return user_config_path(APP_NAME, appauthor=False) / LEGACY_CONFIG_FILENAME


def normalize_symbol(symbol: str) -> str:
    """Return *symbol* uppercased and stripped, after validating its shape.

    :param symbol: Raw ticker from the user (e.g. ``" aapl "``).
    :raises ValueError: If empty or not a plausible ticker.
    """
    normalized = symbol.strip().upper()
    if not normalized:
        raise ValueError("stock symbol must be a non-empty string")
    if not SYMBOL_PATTERN.match(normalized):
        raise ValueError(
            f"invalid stock symbol {symbol!r}; expected 1-10 characters of "
            "letters, digits, dots, or dashes (e.g. AAPL, BRK.B)"
        )
    return normalized


class UserConfigurationService:
    """Load, mutate, and persist :class:`UserConfig` in SQLite.

    Holds an in-memory copy that is written back after each mutation. Pass
    ``db_path`` (or an open ``database``) in tests to stay off the real
    user-data directory.
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        *,
        database: Database | None = None,
        legacy_json_path: Path | None | Any = _UNSET,
    ) -> None:
        """Open the database and load (or seed) the configuration.

        :param db_path: Optional database path; defaults to
            :func:`~mydash.storage.database.default_database_path`.
        :param database: Optional pre-built :class:`Database` to reuse.
        :param legacy_json_path: JSON config to import on a fresh database.
            Defaults to the real legacy path only when this service also uses
            the real database, so tests never sweep up a developer's own file.
        :raises ValueError: If stored preferences cannot be decoded.
        """
        self._owns_database = database is None
        self.database = database if database is not None else Database(db_path)

        if legacy_json_path is _UNSET:
            uses_default_database = db_path is None and database is None
            self._legacy_json_path = (
                legacy_config_path() if uses_default_database else None
            )
        else:
            self._legacy_json_path = legacy_json_path

        self._config = self._load_or_create()

    # -- lifecycle ------------------------------------------------------

    @property
    def database_path(self) -> Path | str:
        """Path of the database backing this configuration."""
        return self.database.path

    def close(self) -> None:
        """Close the database if this service opened it."""
        if self._owns_database:
            self.database.close()

    def __enter__(self) -> UserConfigurationService:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    # -- loading and persistence ----------------------------------------

    def _load_or_create(self) -> UserConfig:
        """Return stored preferences, seeding defaults on a fresh database."""
        connection = self.database.connect()
        stored = connection.execute("SELECT COUNT(*) FROM settings").fetchone()[0]
        if stored:
            return self._read()

        config = self._read_legacy_json() or UserConfig()
        self._write_all(config)
        return config

    def _read(self) -> UserConfig:
        """Build a :class:`UserConfig` from the settings and watchlist tables."""
        connection = self.database.connect()
        rows = connection.execute("SELECT key, value FROM settings").fetchall()

        data: dict[str, Any] = {}
        for row in rows:
            key = row["key"]
            # Ignore keys this version does not know about, so a database written
            # by a newer mydash still opens instead of hard-failing.
            if key not in _SETTING_FIELDS:
                continue
            try:
                data[key] = json.loads(row["value"])
            except json.JSONDecodeError as err:
                raise ValueError(
                    f"stored preference {key!r} is not valid JSON "
                    f"({self.database_path}): {err}"
                ) from err

        data["stock_symbols"] = self._read_symbols()

        try:
            return UserConfig.model_validate(data)
        except ValidationError as err:
            raise ValueError(
                f"stored preferences have an invalid structure "
                f"({self.database_path}): {err}"
            ) from err

    def _read_symbols(self) -> list[str]:
        """Return watch-list symbols in their stored order."""
        rows = self.database.connect().execute(
            "SELECT symbol FROM watchlist ORDER BY position"
        ).fetchall()
        return [row["symbol"] for row in rows]

    def _read_legacy_json(self) -> UserConfig | None:
        """Import the pre-SQLite JSON config, if one is present.

        A corrupt legacy file is skipped rather than blocking startup — the
        file stays put so it can be inspected by hand.
        """
        path = self._legacy_json_path
        if path is None or not Path(path).is_file():
            return None

        path = Path(path)
        try:
            config = UserConfig.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

        try:
            path.replace(path.with_suffix(path.suffix + LEGACY_MIGRATED_SUFFIX))
        except OSError:
            # Import still succeeded; leaving the original in place is harmless
            # because a populated database is never re-seeded from it.
            pass
        return config

    def _write_all(self, config: UserConfig) -> None:
        """Persist every field of *config* in one transaction."""
        payload = config.model_dump(mode="json")
        now = _timestamp()
        with self.database.transaction() as connection:
            connection.executemany(
                _UPSERT_SETTING,
                [(field, json.dumps(payload[field]), now) for field in _SETTING_FIELDS],
            )
            self._replace_symbols(connection, config.stock_symbols, now)

    def _write_setting(self, field: str, value: Any) -> None:
        """Upsert a single scalar preference."""
        with self.database.transaction() as connection:
            connection.execute(
                _UPSERT_SETTING, (field, json.dumps(value), _timestamp())
            )

    def _write_symbols(self, symbols: list[str]) -> None:
        """Replace the stored watch list with *symbols*, preserving order."""
        with self.database.transaction() as connection:
            self._replace_symbols(connection, symbols, _timestamp())

    @staticmethod
    def _replace_symbols(
        connection: sqlite3.Connection, symbols: list[str], now: str
    ) -> None:
        """Rewrite the watchlist rows inside an open transaction."""
        connection.execute("DELETE FROM watchlist")
        connection.executemany(
            "INSERT INTO watchlist (symbol, position, added_at) VALUES (?, ?, ?)",
            [(symbol, index, now) for index, symbol in enumerate(symbols)],
        )

    # -- whole-configuration access -------------------------------------

    def get_configuration(self) -> UserConfig:
        """Return a deep copy of the current configuration."""
        return self._config.model_copy(deep=True)

    def set_configuration(self, config: UserConfig) -> None:
        """Replace the entire configuration and persist it.

        :param config: New preferences to store.
        """
        self._config = config.model_copy(deep=True)
        self._write_all(self._config)

    def reset(self) -> UserConfig:
        """Restore the shipped defaults and return the fresh configuration."""
        self.set_configuration(UserConfig())
        return self.get_configuration()

    # -- city and coordinates -------------------------------------------

    async def set_city(self, city: str) -> None:
        """Geocode *city*, store name + coordinates, and persist.

        Uses the configured geocoding provider (network call).

        :param city: Non-empty place name.
        :raises ValueError: If *city* is empty after strip.
        :raises: Provider-specific errors from the geocoding client.
        """
        city = city.strip()
        if not city:
            raise ValueError("city must be a non-empty string")
        client = get_geocoding_client(provider=self._config.provider_geocoding)
        await client.set_coordinates(city=city)
        coordinates = client.get_coordinates()

        self._config.city = city
        self._config.coordinates = coordinates
        with self.database.transaction() as connection:
            now = _timestamp()
            connection.execute(_UPSERT_SETTING, ("city", json.dumps(city), now))
            connection.execute(
                _UPSERT_SETTING,
                ("coordinates", coordinates.model_dump_json(), now),
            )

    def get_city(self) -> str:
        """Return the configured city name."""
        return self._config.city

    def get_coordinates(self) -> Coordinates:
        """Return a copy of the stored coordinates for the city."""
        return self._config.coordinates.model_copy()

    # -- stock watch list -----------------------------------------------

    def add_stock_symbol(self, symbol: str) -> None:
        """Add a ticker to the watch list (case-insensitive; stored uppercase).

        Adding a symbol already on the list is a no-op.

        :param symbol: Ticker symbol (e.g. ``aapl`` → ``AAPL``).
        :raises ValueError: If *symbol* is empty or malformed.
        """
        normalized = normalize_symbol(symbol)
        if normalized in self._config.stock_symbols:
            return
        self._config.stock_symbols.append(normalized)
        self._write_symbols(self._config.stock_symbols)

    def remove_stock_symbol(self, symbol: str) -> None:
        """Remove a ticker from the watch list.

        :param symbol: Ticker symbol to remove.
        :raises ValueError: If *symbol* is empty, malformed, or not on the list.
        """
        normalized = normalize_symbol(symbol)
        if normalized not in self._config.stock_symbols:
            raise ValueError(f"stock symbol not in list: {normalized}")
        self._config.stock_symbols = [
            existing
            for existing in self._config.stock_symbols
            if existing != normalized
        ]
        self._write_symbols(self._config.stock_symbols)

    def set_stock_symbols(self, symbols: list[str]) -> None:
        """Replace the whole watch list, keeping the given order.

        :param symbols: Tickers to store; duplicates are collapsed.
        :raises ValueError: If any symbol is empty or malformed.
        """
        normalized: list[str] = []
        for symbol in symbols:
            candidate = normalize_symbol(symbol)
            if candidate not in normalized:
                normalized.append(candidate)
        self._config.stock_symbols = normalized
        self._write_symbols(normalized)

    def get_stock_symbols(self) -> list[str]:
        """Return a copy of the configured ticker symbols."""
        return list(self._config.stock_symbols)

    # -- news -----------------------------------------------------------

    def set_news_category(self, category: str) -> None:
        """Set the news category used by the brief.

        :param category: Non-empty category string (provider-dependent).
        :raises ValueError: If *category* is empty after strip.
        """
        category = category.strip()
        if not category:
            raise ValueError("news category must be a non-empty string")
        self._config.news_category = category
        self._write_setting("news_category", category)

    def get_news_category(self) -> str:
        """Return the configured news category."""
        return self._config.news_category

    # -- weather units --------------------------------------------------

    def set_weather_forecast_units(self, units: str) -> None:
        """Set the weather unit preset (``metric`` or ``imperial``).

        :param units: Unit preset name (case-insensitive).
        :raises ValueError: If *units* is not in :data:`KNOWN_WEATHER_UNITS`.
        """
        normalized = units.strip().lower()
        if normalized not in KNOWN_WEATHER_UNITS:
            raise ValueError(
                f"invalid weather units {units!r}; expected one of "
                f"{sorted(KNOWN_WEATHER_UNITS)}"
            )
        self._config.weather_units = normalized  # type: ignore[assignment]
        self._write_setting("weather_units", normalized)

    def get_weather_forecast_units(self) -> WeatherUnits:
        """Return the configured weather unit preset."""
        return self._config.weather_units

    # -- providers ------------------------------------------------------

    def set_news_provider(self, provider: str) -> None:
        """Set the news client provider id.

        :param provider: Must be in :data:`KNOWN_NEWS_PROVIDERS`.
        :raises ValueError: If *provider* is not allowed.
        """
        self._set_provider("provider_news", provider, KNOWN_NEWS_PROVIDERS)

    def get_news_provider(self) -> str:
        """Return the configured news provider id."""
        return self._config.provider_news

    def set_stock_provider(self, provider: str) -> None:
        """Set the stocks client provider id.

        :param provider: Must be in :data:`KNOWN_STOCK_PROVIDERS`.
        :raises ValueError: If *provider* is not allowed.
        """
        self._set_provider("provider_stocks", provider, KNOWN_STOCK_PROVIDERS)

    def get_stock_provider(self) -> str:
        """Return the configured stocks provider id."""
        return self._config.provider_stocks

    def set_weather_provider(self, provider: str) -> None:
        """Set the weather client provider id.

        :param provider: Must be in :data:`KNOWN_WEATHER_PROVIDERS`.
        :raises ValueError: If *provider* is not allowed.
        """
        self._set_provider("provider_weather", provider, KNOWN_WEATHER_PROVIDERS)

    def get_weather_provider(self) -> str:
        """Return the configured weather provider id."""
        return self._config.provider_weather

    def set_geocoding_provider(self, provider: str) -> None:
        """Set the geocoding client provider id.

        :param provider: Must be in :data:`KNOWN_GEOCODING_PROVIDERS`.
        :raises ValueError: If *provider* is not allowed.
        """
        self._set_provider("provider_geocoding", provider, KNOWN_GEOCODING_PROVIDERS)

    def get_geocoding_provider(self) -> str:
        """Return the configured geocoding provider id."""
        return self._config.provider_geocoding

    def _set_provider(self, field: str, provider: str, allowed: frozenset[str]) -> None:
        """Normalize, validate, assign a provider field, and persist.

        :param field: Attribute name on :class:`UserConfig`.
        :param provider: Raw provider string from the user.
        :param allowed: Set of accepted provider ids.
        :raises ValueError: If *provider* is not in *allowed*.
        """
        normalized = provider.strip().lower()
        if normalized not in allowed:
            raise ValueError(
                f"invalid provider {provider!r}; expected one of {sorted(allowed)}"
            )
        setattr(self._config, field, normalized)
        self._write_setting(field, normalized)


_UPSERT_SETTING: Final = """
    INSERT INTO settings (key, value, updated_at)
    VALUES (?, ?, ?)
    ON CONFLICT(key) DO UPDATE SET
        value = excluded.value,
        updated_at = excluded.updated_at
"""


def _timestamp() -> str:
    """Return an ISO-8601 UTC timestamp for ``updated_at`` columns."""
    return datetime.now(timezone.utc).isoformat()
