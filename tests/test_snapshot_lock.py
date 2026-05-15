"""Tests for reqwatch.snapshot_lock."""

from __future__ import annotations

import pytest

from reqwatch.snapshot_lock import (
    LockError,
    clear_locks,
    is_locked,
    list_locked,
    lock_snapshot,
    unlock_snapshot,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


ENDPOINT = "https://api.example.com/v1/items"


def test_is_not_locked_by_default(store):
    assert is_locked(store, ENDPOINT, "snap-001") is False


def test_lock_and_is_locked(store):
    lock_snapshot(store, ENDPOINT, "snap-001")
    assert is_locked(store, ENDPOINT, "snap-001") is True


def test_lock_does_not_affect_other_ids(store):
    lock_snapshot(store, ENDPOINT, "snap-001")
    assert is_locked(store, ENDPOINT, "snap-002") is False


def test_lock_duplicate_is_noop(store):
    lock_snapshot(store, ENDPOINT, "snap-001")
    lock_snapshot(store, ENDPOINT, "snap-001")  # second call should not raise
    assert list_locked(store, ENDPOINT).count("snap-001") == 1


def test_unlock_existing_returns_true(store):
    lock_snapshot(store, ENDPOINT, "snap-001")
    result = unlock_snapshot(store, ENDPOINT, "snap-001")
    assert result is True
    assert is_locked(store, ENDPOINT, "snap-001") is False


def test_unlock_missing_returns_false(store):
    result = unlock_snapshot(store, ENDPOINT, "snap-999")
    assert result is False


def test_list_locked_returns_all(store):
    lock_snapshot(store, ENDPOINT, "snap-001")
    lock_snapshot(store, ENDPOINT, "snap-002")
    locked = list_locked(store, ENDPOINT)
    assert set(locked) == {"snap-001", "snap-002"}


def test_list_locked_empty_when_none(store):
    assert list_locked(store, ENDPOINT) == []


def test_clear_locks_returns_count(store):
    lock_snapshot(store, ENDPOINT, "snap-001")
    lock_snapshot(store, ENDPOINT, "snap-002")
    count = clear_locks(store, ENDPOINT)
    assert count == 2
    assert list_locked(store, ENDPOINT) == []


def test_clear_locks_empty_returns_zero(store):
    assert clear_locks(store, ENDPOINT) == 0


def test_lock_empty_id_raises(store):
    with pytest.raises(LockError):
        lock_snapshot(store, ENDPOINT, "")


def test_lock_whitespace_id_raises(store):
    with pytest.raises(LockError):
        lock_snapshot(store, ENDPOINT, "   ")


def test_locks_isolated_per_endpoint(store):
    other = "https://api.example.com/v2/other"
    lock_snapshot(store, ENDPOINT, "snap-001")
    assert is_locked(store, other, "snap-001") is False
