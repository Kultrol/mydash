"""Short-lived cache for provider responses, backed by SQLite.

Repeat runs of ``mydash brief`` within a few minutes should not re-ask
Open-Meteo what the weather is. Entries are keyed by request shape and expire
on a per-domain TTL (see :data:`TTL`).

Every operation fails soft: a cache that cannot be read or written degrades to
a cache miss rather than taking the command down with it.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final

from mydash.storage.database import Database, DatabaseError

# Anything that means "storage is unavailable right now". Caching is an
# optimization, so every one of these degrades to a miss instead of raising.
_STORAGE_ERRORS: Final = (sqlite3.Error, OSError, DatabaseError)

#: Per-domain freshness windows, in seconds.
TTL: Final[dict[str, float]] = {
    # Cities do not move.
    "geocoding": 30 * 24 * 60 * 60,
    # Hourly forecasts are published well under this cadence.
    "weather": 15 * 60,
    "news": 10 * 60,
    # Quotes go stale fast; this only collapses bursts of repeated runs.
    "stocks": 60,
}


@dataclass(frozen=True)
class CacheStats:
    """Summary of what the cache is currently holding."""

    entries: int
    expired: int
    total_bytes: int
    oldest: float | None
    newest: float | None

    @property
    def fresh(self) -> int:
        """Entries that would still be served."""
        return self.entries - self.expired


def build_key(
    method: str,
    url: str,
    parameters: Mapping[str, Any] | None = None,
) -> str:
    """Return a stable cache key for a request.

    Auth headers are deliberately excluded: two users with different Alpaca
    keys asking for the same symbols want the same answer, and secrets should
    not end up in a database column.

    :param method: HTTP method (case-insensitive).
    :param url: Full request URL without query parameters.
    :param parameters: Query parameters, order-independent.
    """
    canonical = json.dumps(
        {
            "method": method.upper(),
            "url": str(url),
            "params": _canonical_parameters(parameters),
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _canonical_parameters(parameters: Mapping[str, Any] | None) -> Any:
    """Normalize query parameters so equivalent requests share a key."""
    if not parameters:
        return {}
    return {key: parameters[key] for key in sorted(parameters)}


class ResponseCache:
    """Read and write cached provider responses in the ``response_cache`` table."""

    def __init__(self, database: Database | None = None) -> None:
        """Wrap *database*, or the default one when omitted.

        The database connection stays lazy, so building a cache costs nothing
        until something is actually read or written.
        """
        self.database = database if database is not None else Database()

    def get(self, key: str) -> dict[str, Any] | None:
        """Return the cached payload for *key*, or ``None`` when absent/stale."""
        try:
            row = self.database.connect().execute(
                "SELECT payload FROM response_cache "
                "WHERE key = ? AND expires_at > ?",
                (key, time.time()),
            ).fetchone()
        except _STORAGE_ERRORS:
            return None

        if row is None:
            return None
        try:
            return json.loads(row["payload"])
        except json.JSONDecodeError:
            # A payload we cannot read is no better than a miss; drop it.
            self.delete(key)
            return None

    def set(self, key: str, payload: dict[str, Any], ttl: float) -> None:
        """Store *payload* under *key* for *ttl* seconds. No-op if ttl <= 0."""
        if ttl <= 0:
            return
        try:
            encoded = json.dumps(payload)
        except (TypeError, ValueError):
            return

        now = time.time()
        try:
            with self.database.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO response_cache (key, payload, stored_at, expires_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        payload = excluded.payload,
                        stored_at = excluded.stored_at,
                        expires_at = excluded.expires_at
                    """,
                    (key, encoded, now, now + ttl),
                )
        except _STORAGE_ERRORS:
            # Caching is an optimization; never let it fail a command.
            return

    def delete(self, key: str) -> None:
        """Remove one entry, ignoring storage errors."""
        try:
            with self.database.transaction() as connection:
                connection.execute("DELETE FROM response_cache WHERE key = ?", (key,))
        except _STORAGE_ERRORS:
            return

    def purge_expired(self) -> int:
        """Delete entries past their expiry and return how many went."""
        try:
            with self.database.transaction() as connection:
                cursor = connection.execute(
                    "DELETE FROM response_cache WHERE expires_at <= ?", (time.time(),)
                )
                return cursor.rowcount or 0
        except _STORAGE_ERRORS:
            return 0

    def clear(self) -> int:
        """Delete every entry and return how many went."""
        try:
            with self.database.transaction() as connection:
                cursor = connection.execute("DELETE FROM response_cache")
                return cursor.rowcount or 0
        except _STORAGE_ERRORS:
            return 0

    def stats(self) -> CacheStats:
        """Return counts and sizes for ``mydash cache info``."""
        try:
            row = self.database.connect().execute(
                """
                SELECT
                    COUNT(*)                                  AS entries,
                    COALESCE(SUM(expires_at <= ?), 0)         AS expired,
                    COALESCE(SUM(LENGTH(payload)), 0)         AS total_bytes,
                    MIN(stored_at)                            AS oldest,
                    MAX(stored_at)                            AS newest
                FROM response_cache
                """,
                (time.time(),),
            ).fetchone()
        except _STORAGE_ERRORS:
            return CacheStats(entries=0, expired=0, total_bytes=0, oldest=None, newest=None)

        return CacheStats(
            entries=row["entries"],
            expired=row["expired"],
            total_bytes=row["total_bytes"],
            oldest=row["oldest"],
            newest=row["newest"],
        )
