"""Tests for reqwatch.snapshot_group."""

from __future__ import annotations

import pytest

from reqwatch.snapshot_group import (
    GroupError,
    add_to_group,
    get_group_members,
    latest_snapshots_for_group,
    list_groups,
    remove_from_group,
)
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(endpoint: str, status: int = 200) -> dict:
    return {"endpoint": endpoint, "status": status, "body": {"ok": True}, "timestamp": "2024-01-01T00:00:00"}


def test_add_and_list_group(store):
    add_to_group(store, "prod", "https://api.example.com/a")
    add_to_group(store, "prod", "https://api.example.com/b")
    groups = list_groups(store)
    assert "prod" in groups
    assert "https://api.example.com/a" in groups["prod"]
    assert "https://api.example.com/b" in groups["prod"]


def test_add_duplicate_is_noop(store):
    add_to_group(store, "prod", "https://api.example.com/a")
    add_to_group(store, "prod", "https://api.example.com/a")
    members = get_group_members(store, "prod")
    assert members.count("https://api.example.com/a") == 1


def test_add_empty_group_name_raises(store):
    with pytest.raises(GroupError):
        add_to_group(store, "  ", "https://api.example.com/a")


def test_remove_existing_member(store):
    add_to_group(store, "prod", "https://api.example.com/a")
    result = remove_from_group(store, "prod", "https://api.example.com/a")
    assert result is True
    groups = list_groups(store)
    assert "prod" not in groups  # group deleted when empty


def test_remove_nonexistent_member_returns_false(store):
    add_to_group(store, "prod", "https://api.example.com/a")
    result = remove_from_group(store, "prod", "https://api.example.com/missing")
    assert result is False


def test_get_group_members_missing_group_raises(store):
    with pytest.raises(GroupError, match="does not exist"):
        get_group_members(store, "nonexistent")


def test_list_groups_empty_store(store):
    assert list_groups(store) == {}


def test_latest_snapshots_for_group(store):
    endpoint = "https://api.example.com/a"
    snap = _snap(endpoint)
    save_snapshot(store, endpoint, snap)
    add_to_group(store, "prod", endpoint)
    results = latest_snapshots_for_group(store, "prod")
    assert len(results) == 1
    assert results[0]["endpoint"] == endpoint


def test_latest_snapshots_none_when_no_snapshots(store):
    endpoint = "https://api.example.com/no-snaps"
    add_to_group(store, "prod", endpoint)
    results = latest_snapshots_for_group(store, "prod")
    assert results == [None]


def test_multiple_groups_independent(store):
    add_to_group(store, "prod", "https://a.com")
    add_to_group(store, "staging", "https://b.com")
    assert get_group_members(store, "prod") == ["https://a.com"]
    assert get_group_members(store, "staging") == ["https://b.com"]
