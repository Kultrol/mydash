"""Tests for mydash.storage.database.

Strategy: tmp_path database files (never the real user-data dir); assert schema,
pragmas, migration idempotence, and transaction rollback.
"""

from pathlib import Path

import pytest

from mydash.storage.database import (
    DB_PATH_ENV_VAR,
    SCHEMA_VERSION,
    Database,
    DatabaseError,
    default_database_path,
)

EXPECTED_TABLES = {"settings", "watchlist", "response_cache"}


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "nested" / "mydash.db"


def test_connect_creates_file_and_parent_directory(db_path: Path):
    with Database(db_path) as db:
        db.connect()

    assert db_path.is_file()


def test_schema_creates_expected_tables(db_path: Path):
    with Database(db_path) as db:
        rows = db.connect().execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    names = {row["name"] for row in rows}
    assert EXPECTED_TABLES <= names


def test_schema_version_is_recorded(db_path: Path):
    with Database(db_path) as db:
        version = db.connect().execute("PRAGMA user_version").fetchone()[0]

    assert version == SCHEMA_VERSION


def test_reopening_an_existing_database_keeps_data(db_path: Path):
    with Database(db_path) as db:
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                ("city", '"Miami"', "2026-08-30T00:00:00Z"),
            )

    with Database(db_path) as reopened:
        row = reopened.connect().execute(
            "SELECT value FROM settings WHERE key = 'city'"
        ).fetchone()
        version = reopened.connect().execute("PRAGMA user_version").fetchone()[0]

    assert row["value"] == '"Miami"'
    assert version == SCHEMA_VERSION


def test_row_factory_allows_name_access(db_path: Path):
    with Database(db_path) as db:
        row = db.connect().execute("SELECT 1 AS answer").fetchone()

    assert row["answer"] == 1


def test_foreign_keys_pragma_is_on(db_path: Path):
    with Database(db_path) as db:
        assert db.connect().execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_transaction_rolls_back_on_error(db_path: Path):
    db = Database(db_path)
    db.connect()

    with pytest.raises(RuntimeError, match="boom"):
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                ("city", '"Seattle"', "2026-08-30T00:00:00Z"),
            )
            raise RuntimeError("boom")

    remaining = db.connect().execute("SELECT COUNT(*) FROM settings").fetchone()[0]
    assert remaining == 0
    db.close()


def test_transaction_commits_on_success(db_path: Path):
    with Database(db_path) as db:
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                ("city", '"Seattle"', "2026-08-30T00:00:00Z"),
            )

        stored = db.connect().execute("SELECT COUNT(*) FROM settings").fetchone()[0]

    assert stored == 1


def test_close_is_idempotent(db_path: Path):
    db = Database(db_path)
    db.connect()
    db.close()
    db.close()

    # A closed database can be reopened.
    assert db.connect().execute("SELECT 1").fetchone()[0] == 1
    db.close()


def test_memory_database_never_touches_disk(tmp_path: Path):
    with Database(":memory:") as db:
        assert db.is_memory
        rows = db.connect().execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    assert EXPECTED_TABLES <= {row["name"] for row in rows}
    assert not list(tmp_path.iterdir())


def test_unwritable_location_raises_database_error(tmp_path: Path):
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("", encoding="utf-8")

    with pytest.raises(DatabaseError):
        Database(blocker / "mydash.db").connect()


def test_default_path_uses_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    override = tmp_path / "custom.db"
    monkeypatch.setenv(DB_PATH_ENV_VAR, str(override))

    assert default_database_path() == override


def test_default_path_ignores_blank_env_override(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(DB_PATH_ENV_VAR, "   ")

    assert default_database_path().name == "mydash.db"
