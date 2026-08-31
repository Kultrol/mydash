"""SQLite connection handling and schema management.

One file holds every piece of state mydash keeps between runs. Opening a
:class:`Database` creates the file, applies pragmas, and brings the schema up to
:data:`SCHEMA_VERSION` — callers never deal with migrations directly.

Set ``MYDASH_DB_PATH`` to point the CLI at a throwaway database; useful for
trying things out without touching your real preferences.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from platformdirs import user_data_path

APP_NAME = "mydash"
DATABASE_FILENAME = "mydash.db"
DB_PATH_ENV_VAR = "MYDASH_DB_PATH"
MEMORY_PATH = ":memory:"

#: Bump together with a new entry in :data:`_MIGRATIONS`.
SCHEMA_VERSION = 1

# Pragmas applied to every connection. WAL keeps reads from blocking on the
# writer, which matters because a brief reads config while it writes cache rows.
_PRAGMAS = (
    "PRAGMA journal_mode = WAL",
    "PRAGMA synchronous = NORMAL",
    "PRAGMA foreign_keys = ON",
    "PRAGMA busy_timeout = 5000",
)

# Schema version 1: user preferences plus the provider response cache.
_MIGRATION_1 = (
    """
    CREATE TABLE IF NOT EXISTS settings (
        key        TEXT PRIMARY KEY,
        value      TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS watchlist (
        symbol   TEXT PRIMARY KEY,
        position INTEGER NOT NULL,
        added_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_watchlist_position ON watchlist(position)",
    """
    CREATE TABLE IF NOT EXISTS response_cache (
        key        TEXT PRIMARY KEY,
        payload    TEXT NOT NULL,
        stored_at  REAL NOT NULL,
        expires_at REAL NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_response_cache_expires_at "
    "ON response_cache(expires_at)",
)

#: Ordered migrations; index + 1 is the schema version each one produces.
_MIGRATIONS: tuple[tuple[str, ...], ...] = (_MIGRATION_1,)


def default_database_path() -> Path:
    """Return the database path, honouring the ``MYDASH_DB_PATH`` override.

    Without an override this is the platform user-data directory:

        macOS:   ~/Library/Application Support/mydash/mydash.db
        Linux:   ~/.local/share/mydash/mydash.db
        Windows: C:\\Users\\<user>\\AppData\\Local\\mydash\\mydash.db
    """
    override = os.getenv(DB_PATH_ENV_VAR)
    if override and override.strip():
        return Path(override.strip()).expanduser()
    return user_data_path(APP_NAME, appauthor=False) / DATABASE_FILENAME


class DatabaseError(RuntimeError):
    """Raised when the database cannot be opened or migrated."""


class Database:
    """A lazily opened SQLite database with the mydash schema applied.

    The connection is created on first use, so constructing a ``Database`` is
    cheap enough to do in a CLI callback that may never touch storage.
    """

    def __init__(self, path: Path | str | None = None) -> None:
        """Open (lazily) the database at *path*.

        :param path: File path, ``":memory:"``, or ``None`` for
            :func:`default_database_path`.
        """
        if path is None:
            self.path: Path | str = default_database_path()
        elif str(path) == MEMORY_PATH:
            self.path = MEMORY_PATH
        else:
            self.path = Path(path).expanduser()
        self._connection: sqlite3.Connection | None = None

    @property
    def is_memory(self) -> bool:
        """True when this database lives in memory and is never written out."""
        return self.path == MEMORY_PATH

    def connect(self) -> sqlite3.Connection:
        """Return the open connection, creating and migrating it if needed.

        :raises DatabaseError: If the file cannot be created or opened.
        """
        if self._connection is not None:
            return self._connection

        if not self.is_memory:
            parent = Path(self.path).parent
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except OSError as err:
                raise DatabaseError(
                    f"could not create the mydash data directory {parent}: {err}"
                ) from err

        try:
            # isolation_level=None puts sqlite3 in autocommit mode so that
            # `transaction()` controls transaction boundaries explicitly.
            connection = sqlite3.connect(
                self.path,
                isolation_level=None,
                check_same_thread=False,
            )
        except sqlite3.Error as err:
            raise DatabaseError(
                f"could not open the mydash database {self.path}: {err}"
            ) from err

        connection.row_factory = sqlite3.Row
        for pragma in _PRAGMAS:
            connection.execute(pragma)

        self._connection = connection
        try:
            self._migrate(connection)
        except sqlite3.Error as err:
            self.close()
            raise DatabaseError(
                f"could not prepare the mydash database {self.path}: {err}"
            ) from err
        return connection

    def _migrate(self, connection: sqlite3.Connection) -> None:
        """Apply any migrations the file has not seen yet."""
        current: int = connection.execute("PRAGMA user_version").fetchone()[0]
        if current >= SCHEMA_VERSION:
            return

        for version, statements in enumerate(_MIGRATIONS[current:], start=current + 1):
            connection.execute("BEGIN IMMEDIATE")
            try:
                for statement in statements:
                    connection.execute(statement)
                # PRAGMA does not accept bound parameters; version is an int
                # produced by enumerate over a module constant.
                connection.execute(f"PRAGMA user_version = {version}")
            except sqlite3.Error:
                connection.execute("ROLLBACK")
                raise
            connection.execute("COMMIT")

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Run a block inside one immediate transaction, rolling back on error."""
        connection = self.connect()
        connection.execute("BEGIN IMMEDIATE")
        try:
            yield connection
        except BaseException:
            connection.execute("ROLLBACK")
            raise
        connection.execute("COMMIT")

    def close(self) -> None:
        """Close the connection if one is open. Safe to call repeatedly."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> Database:
        self.connect()
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()
