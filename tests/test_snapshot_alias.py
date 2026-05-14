"""Tests for reqwatch/snapshot_alias.py."""

import pytest

from reqwatch.snapshot_alias import (
    AliasError,
    delete_alias,
    get_alias,
    list_aliases,
    resolve,
    set_alias,
)
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def snap(store):
    """Save a single snapshot and return its ID."""
    snapshot = {
        "endpoint": "api/v1/health",
        "timestamp": "2024-06-01T12:00:00",
        "status_code": 200,
        "body": {"status": "ok"},
        "headers": {},
        "error": None,
        "elapsed": 0.1,
    }
    return save_snapshot(store, "api/v1/health", snapshot)


def test_set_and_get_alias(store, snap):
    set_alias(store, "prod-health", snap)
    assert get_alias(store, "prod-health") == snap


def test_get_missing_alias_returns_none(store):
    assert get_alias(store, "nonexistent") is None


def test_set_alias_nonexistent_snapshot_raises(store):
    with pytest.raises(AliasError, match="not found"):
        set_alias(store, "ghost", "fake-id-0000")


def test_set_alias_empty_name_raises(store, snap):
    with pytest.raises(AliasError, match="non-empty"):
        set_alias(store, "   ", snap)


def test_set_alias_overwrites_existing(store, snap):
    set_alias(store, "latest", snap)
    # Save a second snapshot so we have another valid ID.
    snapshot2 = {
        "endpoint": "api/v1/health",
        "timestamp": "2024-06-01T13:00:00",
        "status_code": 200,
        "body": {"status": "ok"},
        "headers": {},
        "error": None,
        "elapsed": 0.2,
    }
    snap2 = save_snapshot(store, "api/v1/health", snapshot2)
    set_alias(store, "latest", snap2)
    assert get_alias(store, "latest") == snap2


def test_delete_existing_alias_returns_true(store, snap):
    set_alias(store, "to-remove", snap)
    assert delete_alias(store, "to-remove") is True
    assert get_alias(store, "to-remove") is None


def test_delete_missing_alias_returns_false(store):
    assert delete_alias(store, "nope") is False


def test_list_aliases_empty(store):
    assert list_aliases(store) == {}


def test_list_aliases_returns_all(store, snap):
    set_alias(store, "a", snap)
    set_alias(store, "b", snap)
    result = list_aliases(store)
    assert set(result.keys()) == {"a", "b"}


def test_resolve_known_alias(store, snap):
    set_alias(store, "stable", snap)
    assert resolve(store, "stable") == snap


def test_resolve_unknown_falls_back_to_raw(store):
    raw_id = "some-raw-snapshot-id"
    assert resolve(store, raw_id) == raw_id
