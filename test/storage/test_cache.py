"""Tests for mydash.storage.cache.

Strategy: tmp_path databases; drive expiry by writing rows with explicit
timestamps rather than sleeping.
"""

import json
import time
from pathlib import Path

import pytest

from mydash.storage.cache import TTL, ResponseCache, build_key
from mydash.storage.database import Database


@pytest.fixture
def cache(tmp_path: Path):
    database = Database(tmp_path / "mydash.db")
    yield ResponseCache(database)
    database.close()


def _expire(cache: ResponseCache, key: str) -> None:
    """Backdate an entry so it reads as stale."""
    with cache.database.transaction() as connection:
        connection.execute(
            "UPDATE response_cache SET expires_at = ? WHERE key = ?",
            (time.time() - 1, key),
        )


# --- keys -----------------------------------------------------------------


def test_key_is_stable_across_parameter_order():
    first = build_key("GET", "https://example.com", {"a": 1, "b": 2})
    second = build_key("GET", "https://example.com", {"b": 2, "a": 1})

    assert first == second


def test_key_varies_with_method_url_and_parameters():
    base = build_key("GET", "https://example.com", {"a": 1})

    assert base != build_key("POST", "https://example.com", {"a": 1})
    assert base != build_key("GET", "https://example.org", {"a": 1})
    assert base != build_key("GET", "https://example.com", {"a": 2})


def test_key_ignores_method_case():
    assert build_key("get", "https://example.com") == build_key(
        "GET", "https://example.com"
    )


def test_key_treats_missing_and_empty_parameters_alike():
    assert build_key("GET", "https://example.com") == build_key(
        "GET", "https://example.com", {}
    )


# --- get / set ------------------------------------------------------------


def test_set_then_get_round_trips(cache: ResponseCache):
    cache.set("k", {"hello": "world"}, ttl=60)

    assert cache.get("k") == {"hello": "world"}


def test_get_returns_none_for_unknown_key(cache: ResponseCache):
    assert cache.get("nothing-here") is None


def test_expired_entries_are_not_served(cache: ResponseCache):
    cache.set("k", {"stale": True}, ttl=60)
    _expire(cache, "k")

    assert cache.get("k") is None


def test_zero_or_negative_ttl_is_not_stored(cache: ResponseCache):
    cache.set("zero", {"a": 1}, ttl=0)
    cache.set("negative", {"a": 1}, ttl=-5)

    assert cache.get("zero") is None
    assert cache.get("negative") is None


def test_set_overwrites_an_existing_key(cache: ResponseCache):
    cache.set("k", {"version": 1}, ttl=60)
    cache.set("k", {"version": 2}, ttl=60)

    assert cache.get("k") == {"version": 2}


def test_unserializable_payload_is_skipped(cache: ResponseCache):
    cache.set("k", {"when": object()}, ttl=60)

    assert cache.get("k") is None


def test_corrupt_payload_is_treated_as_a_miss_and_dropped(cache: ResponseCache):
    cache.set("k", {"a": 1}, ttl=60)
    with cache.database.transaction() as connection:
        connection.execute(
            "UPDATE response_cache SET payload = ? WHERE key = ?", ("{oops", "k")
        )

    assert cache.get("k") is None
    remaining = cache.database.connect().execute(
        "SELECT COUNT(*) FROM response_cache"
    ).fetchone()[0]
    assert remaining == 0


def test_delete_removes_an_entry(cache: ResponseCache):
    cache.set("k", {"a": 1}, ttl=60)
    cache.delete("k")

    assert cache.get("k") is None


# --- maintenance ----------------------------------------------------------


def test_purge_expired_only_drops_stale_rows(cache: ResponseCache):
    cache.set("fresh", {"a": 1}, ttl=60)
    cache.set("stale", {"a": 1}, ttl=60)
    _expire(cache, "stale")

    assert cache.purge_expired() == 1
    assert cache.get("fresh") == {"a": 1}


def test_clear_drops_everything(cache: ResponseCache):
    cache.set("a", {"a": 1}, ttl=60)
    cache.set("b", {"b": 2}, ttl=60)

    assert cache.clear() == 2
    assert cache.stats().entries == 0


def test_stats_counts_fresh_and_expired(cache: ResponseCache):
    cache.set("fresh", {"a": 1}, ttl=60)
    cache.set("stale", {"a": 1}, ttl=60)
    _expire(cache, "stale")

    stats = cache.stats()

    assert stats.entries == 2
    assert stats.expired == 1
    assert stats.fresh == 1
    assert stats.total_bytes == len(json.dumps({"a": 1})) * 2
    assert stats.oldest is not None and stats.newest is not None


def test_stats_on_an_empty_cache(cache: ResponseCache):
    stats = cache.stats()

    assert (stats.entries, stats.expired, stats.total_bytes) == (0, 0, 0)
    assert stats.oldest is None


# --- failing soft ---------------------------------------------------------


def test_storage_errors_degrade_to_a_miss(tmp_path: Path):
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("", encoding="utf-8")
    cache = ResponseCache(Database(blocker / "mydash.db"))

    # None of these may raise: caching is an optimization, not a dependency.
    cache.set("k", {"a": 1}, ttl=60)

    assert cache.get("k") is None
    assert cache.purge_expired() == 0
    assert cache.clear() == 0
    assert cache.stats().entries == 0


# --- TTL table ------------------------------------------------------------


def test_ttls_are_defined_for_every_domain():
    assert set(TTL) == {"geocoding", "weather", "news", "stocks"}
    assert TTL["stocks"] < TTL["news"] < TTL["weather"] < TTL["geocoding"]
