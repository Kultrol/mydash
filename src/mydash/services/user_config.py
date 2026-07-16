"""User preferences: JSON-backed configuration for brief and domain services.

:class:`UserConfigurationService` owns the on-disk config file (path from
platformdirs) and an in-memory :class:`UserConfig`. The daily brief reads
preferences from this service; the ``mydash set`` CLI mutates them.

First use creates the file with Miami / tech / common ticker defaults so no
network is required until the user changes the city (which geocodes).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Literal

from platformdirs import user_config_path
from pydantic import BaseModel, Field, ValidationError

from mydash.client.geocoding.factory import get_geocoding_client
from mydash.models.geocoding import Coordinates

WeatherUnits = Literal["metric", "imperial"]

# Defaults for a new config file — coordinates are fixed so first create is offline.
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


def default_config_path() -> Path:
    """Return the platform-appropriate config file path for mydash.
    Application Support on macOS, XDG config on Linux, AppData on Windows.

    Typical File Paths on different Platforms:
        MacOS: ~/Library/Application Support/mydash/config.json
        Linux: ~/.config/mydash/config.json\"
        Windows: C:\ Users\ <user>\AppData\\mydash\config.json
    """
    return user_config_path("mydash", appauthor=False) / "config.json"


class UserConfigurationService:
    """Load, mutate, and persist :class:`UserConfig` as JSON.

    Holds an in-memory copy that is written after each successful mutation.
    Pass ``config_path`` in tests to avoid touching the real user config dir.
    """

    def __init__(self, config_path: Path | str | None = None) -> None:
        """Create the service and load or initialize the config file.

        :param config_path: Optional override path; defaults to
            :func:`default_config_path`.
        :raises ValueError: If an existing file is corrupt or invalid.
        """
        self.config_path = (
            Path(config_path) if config_path is not None else default_config_path()
        )
        self._config = self._load_or_create()

    def _load_or_create(self) -> UserConfig:
        """Load JSON from disk, or create and save defaults if missing.

        :raises ValueError: On invalid JSON or schema validation failure.
        """
        if self.config_path.is_file():
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                return UserConfig.model_validate(data)
            except json.JSONDecodeError as err:
                raise ValueError(
                    f"config file is not valid JSON: {self.config_path} ({err})"
                ) from err
            except ValidationError as err:
                raise ValueError(
                    f"config file has invalid structure: {self.config_path} ({err})"
                ) from err
        config = UserConfig()
        self._config = config
        self._save()
        return config

    def _save(self) -> None:
        """Atomically write the current config to disk (temp file + replace)."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._config.model_dump(mode="json")
        text = json.dumps(payload, indent=2) + "\n"
        # Write to a sibling temp file then replace to avoid partial configs.
        fd, tmp_name = tempfile.mkstemp(
            dir=self.config_path.parent,
            prefix=".config.",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                tmp_file.write(text)
            Path(tmp_name).replace(self.config_path)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def get_configuration(self) -> UserConfig:
        """Return a deep copy of the current configuration."""
        return self._config.model_copy(deep=True)

    def set_configuration(self, config: UserConfig) -> None:
        """Replace the entire configuration and persist it.

        :param config: New preferences to store.
        """
        self._config = config.model_copy(deep=True)
        self._save()

    def set_city(self, city: str) -> None:
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
        client.set_coordinates(city=city)
        coordinates = client.get_coordinates()
        self._config.city = city
        self._config.coordinates = coordinates
        self._save()

    def get_city(self) -> str:
        """Return the configured city name."""
        return self._config.city

    def get_coordinates(self) -> Coordinates:
        """Return a copy of the stored coordinates for the city."""
        return self._config.coordinates.model_copy()

    def _add_stock_symbol(self, symbol: str) -> None:
        """Append *symbol* (uppercase) if not already present; then persist."""
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("stock symbol must be a non-empty string")
        if normalized not in self._config.stock_symbols:
            self._config.stock_symbols.append(normalized)
            self._save()

    def _remove_stock_symbol(self, symbol: str) -> None:
        """Remove *symbol* from the list or raise if missing."""
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("stock symbol must be a non-empty string")
        if normalized not in self._config.stock_symbols:
            raise ValueError(f"stock symbol not in list: {normalized}")
        self._config.stock_symbols = [
            s for s in self._config.stock_symbols if s != normalized
        ]
        self._save()

    def add_stock_symbol(self, symbol: str) -> None:
        """Add a ticker to the watch list (case-insensitive; stored uppercase).

        :param symbol: Ticker symbol (e.g. ``aapl`` → ``AAPL``).
        :raises ValueError: If *symbol* is empty.
        """
        self._add_stock_symbol(symbol)

    def remove_stock_symbol(self, symbol: str) -> None:
        """Remove a ticker from the watch list.

        :param symbol: Ticker symbol to remove.
        :raises ValueError: If *symbol* is empty or not in the list.
        """
        self._remove_stock_symbol(symbol)

    def get_stock_symbols(self) -> list[str]:
        """Return a copy of the configured ticker symbols."""
        return list(self._config.stock_symbols)

    def set_news_category(self, category: str) -> None:
        """Set the news category used by the brief.

        :param category: Non-empty category string (provider-dependent).
        :raises ValueError: If *category* is empty after strip.
        """
        category = category.strip()
        if not category:
            raise ValueError("news category must be a non-empty string")
        self._config.news_category = category
        self._save()

    def get_news_category(self) -> str:
        """Return the configured news category."""
        return self._config.news_category

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
        self._save()

    def get_weather_forecast_units(self) -> WeatherUnits:
        """Return the configured weather unit preset."""
        return self._config.weather_units

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
        self._save()
