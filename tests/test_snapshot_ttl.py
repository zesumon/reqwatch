"""Tests for reqwatch.snapshot_ttl."""

from __future__ import annotations

import time
import pytest

from reqwatch.snapshot_ttl import (
    TTLError,
    StaleSnapshot,
    clear_ttl,
    find_stale,
    get_ttl,
    set_ttl,
)
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(store, endpoint, ts, status=200):
    snap = {"timestamp": ts, "status": status, "body": {"v": 1}, "headers": {}, "error": None}
    save_snapshot(store, endpoint, snap)
    from reqwatch.storage import list_snapshots
    return list_snapshots(store, endpoint)[-1]


def test_set_and_get_ttl(store):
    set_ttl(store, "api/v1", 300)
    assert get_ttl(store, "api/v1") == 300.0


def test_get_missing_returns_none(store):
    assert get_ttl(store, "nonexistent") is None


def test_set_zero_raises(store):
    with pytest.raises(TTLError):
        set_ttl(store, "api/v1", 0)


def test_set_negative_raises(store):
    with pytest.raises(TTLError):
        set_ttl(store, "api/v1", -60)


def test_clear_existing_returns_true(store):
    set_ttl(store, "api/v1", 60)
    assert clear_ttl(store, "api/v1") is True
    assert get_ttl(store, "api/v1") is None


def test_clear_missing_returns_false(store):
    assert clear_ttl(store, "api/v1") is False


def test_find_stale_no_ttl_returns_empty(store):
    _snap(store, "api/v1", time.time() - 1000)
    assert find_stale(store, "api/v1") == []


def test_find_stale_fresh_snapshot_not_included(store):
    set_ttl(store, "api/v1", 3600)
    _snap(store, "api/v1", time.time() - 10)
    assert find_stale(store, "api/v1") == []


def test_find_stale_old_snapshot_included(store):
    set_ttl(store, "api/v1", 60)
    now = time.time()
    _snap(store, "api/v1", now - 120)
    stale = find_stale(store, "api/v1", now=now)
    assert len(stale) == 1
    assert isinstance(stale[0], StaleSnapshot)
    assert stale[0].age_seconds > 60
    assert stale[0].ttl_seconds == 60


def test_find_stale_mixed_snapshots(store):
    set_ttl(store, "api/v1", 100)
    now = time.time()
    _snap(store, "api/v1", now - 200)  # stale
    _snap(store, "api/v1", now - 50)   # fresh
    stale = find_stale(store, "api/v1", now=now)
    assert len(stale) == 1
    assert stale[0].age_seconds > 100


def test_overwrite_ttl(store):
    set_ttl(store, "api/v1", 300)
    set_ttl(store, "api/v1", 600)
    assert get_ttl(store, "api/v1") == 600.0


def test_multiple_endpoints_independent(store):
    set_ttl(store, "api/v1", 60)
    set_ttl(store, "api/v2", 120)
    assert get_ttl(store, "api/v1") == 60.0
    assert get_ttl(store, "api/v2") == 120.0
    clear_ttl(store, "api/v1")
    assert get_ttl(store, "api/v1") is None
    assert get_ttl(store, "api/v2") == 120.0
