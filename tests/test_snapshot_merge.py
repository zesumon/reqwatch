"""Tests for reqwatch.snapshot_merge."""

from __future__ import annotations

import pytest

from reqwatch.snapshot_merge import MergeError, _deep_merge, merge_snapshots, merge_and_save
from reqwatch.storage import save_snapshot, list_snapshots


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(body, timestamp="2024-01-01T00:00:00", url="https://api.example.com/v1"):
    return {
        "url": url,
        "status": 200,
        "headers": {"content-type": "application/json"},
        "body": body,
        "timestamp": timestamp,
        "error": None,
    }


# ---------------------------------------------------------------------------
# _deep_merge unit tests
# ---------------------------------------------------------------------------


def test_deep_merge_simple_override():
    result = _deep_merge({"a": 1, "b": 2}, {"b": 99, "c": 3})
    assert result == {"a": 1, "b": 99, "c": 3}


def test_deep_merge_nested_dicts():
    base = {"meta": {"version": 1, "stable": True}}
    override = {"meta": {"version": 2}}
    result = _deep_merge(base, override)
    assert result == {"meta": {"version": 2, "stable": True}}


def test_deep_merge_does_not_mutate_inputs():
    base = {"x": {"y": 1}}
    override = {"x": {"z": 2}}
    _deep_merge(base, override)
    assert base == {"x": {"y": 1}}
    assert override == {"x": {"z": 2}}


# ---------------------------------------------------------------------------
# merge_snapshots tests
# ---------------------------------------------------------------------------


def test_merge_prefer_b_overwrites_scalar():
    a = _snap({"count": 5, "name": "alpha"}, timestamp="2024-01-01T00:00:00")
    b = _snap({"count": 10, "extra": True}, timestamp="2024-01-02T00:00:00")
    merged = merge_snapshots(a, b, prefer="b")
    assert merged["body"] == {"count": 10, "name": "alpha", "extra": True}
    assert merged["timestamp"] == "2024-01-02T00:00:00"


def test_merge_prefer_a_overwrites_scalar():
    a = _snap({"count": 5}, timestamp="2024-01-01T00:00:00")
    b = _snap({"count": 10, "extra": True}, timestamp="2024-01-02T00:00:00")
    merged = merge_snapshots(a, b, prefer="a")
    assert merged["body"]["count"] == 5
    assert merged["timestamp"] == "2024-01-01T00:00:00"


def test_merge_non_dict_body_raises():
    a = _snap(["list", "body"])
    b = _snap({"key": "value"})
    with pytest.raises(MergeError, match="must be dicts"):
        merge_snapshots(a, b)


def test_merge_invalid_prefer_raises():
    a = _snap({"x": 1})
    b = _snap({"y": 2})
    with pytest.raises(MergeError, match="prefer must be"):
        merge_snapshots(a, b, prefer="c")


def test_merge_nested_bodies_recursively():
    a = _snap({"data": {"items": [1, 2], "total": 2}})
    b = _snap({"data": {"total": 5, "page": 2}})
    merged = merge_snapshots(a, b)
    assert merged["body"] == {"data": {"items": [1, 2], "total": 5, "page": 2}}


# ---------------------------------------------------------------------------
# merge_and_save integration tests
# ---------------------------------------------------------------------------


def test_merge_and_save_persists_snapshot(store):
    endpoint = "api_v1"
    snap_a = _snap({"a": 1}, timestamp="2024-01-01T10:00:00")
    snap_b = _snap({"b": 2}, timestamp="2024-01-01T11:00:00")
    save_snapshot(store, endpoint, snap_a)
    save_snapshot(store, endpoint, snap_b)

    merged = merge_and_save(store, endpoint, "2024-01-01T10:00:00", "2024-01-01T11:00:00")
    assert merged["body"] == {"a": 1, "b": 2}
    # A third snapshot should now exist
    assert len(list_snapshots(store, endpoint)) == 3


def test_merge_and_save_missing_ref_raises(store):
    endpoint = "api_v1"
    snap_a = _snap({"a": 1}, timestamp="2024-01-01T10:00:00")
    save_snapshot(store, endpoint, snap_a)

    with pytest.raises(MergeError, match="Snapshot not found"):
        merge_and_save(store, endpoint, "2024-01-01T10:00:00", "9999-99-99T00:00:00")
