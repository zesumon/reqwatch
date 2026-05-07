"""Tests for reqwatch.snapshot_compare."""

import pytest

from reqwatch.snapshot_compare import compare_snapshots, CompareError
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(status=200, body=None, error=None, ts="2024-01-01T00:00:00"):
    return {
        "timestamp": ts,
        "status": status,
        "body": body or {"value": 1},
        "error": error,
    }


def test_compare_no_change(store):
    snap = _snap(ts="2024-01-01T00:00:00")
    save_snapshot(store, "http://api/v1", snap)
    save_snapshot(store, "http://api/v1", _snap(ts="2024-01-01T00:01:00"))

    result = compare_snapshots(store, "http://api/v1")

    assert result["endpoint"] == "http://api/v1"
    assert result["changed"] is False
    assert result["diff_lines"] == []


def test_compare_detects_change(store):
    save_snapshot(store, "http://api/v1", _snap(body={"value": 1}, ts="2024-01-01T00:00:00"))
    save_snapshot(store, "http://api/v1", _snap(body={"value": 99}, ts="2024-01-01T00:01:00"))

    result = compare_snapshots(store, "http://api/v1")

    assert result["changed"] is True
    assert any("value" in line for line in result["diff_lines"])


def test_compare_explicit_refs(store):
    save_snapshot(store, "http://api/v1", _snap(body={"a": 1}, ts="2024-01-01T00:00:00"))
    save_snapshot(store, "http://api/v1", _snap(body={"a": 2}, ts="2024-01-01T00:01:00"))
    save_snapshot(store, "http://api/v1", _snap(body={"a": 3}, ts="2024-01-01T00:02:00"))

    result = compare_snapshots(store, "http://api/v1", ref_a="-3", ref_b="-1")
    assert result["changed"] is True


def test_compare_no_snapshots_raises(store):
    with pytest.raises(CompareError, match="No snapshots"):
        compare_snapshots(store, "http://missing/")


def test_compare_index_out_of_range_raises(store):
    save_snapshot(store, "http://api/v1", _snap())

    with pytest.raises(CompareError, match="out of range"):
        compare_snapshots(store, "http://api/v1", ref_a="-5", ref_b="-1")


def test_compare_result_contains_timestamps(store):
    save_snapshot(store, "http://api/v1", _snap(ts="2024-01-01T00:00:00"))
    save_snapshot(store, "http://api/v1", _snap(ts="2024-01-01T00:01:00"))

    result = compare_snapshots(store, "http://api/v1")

    assert "2024-01-01" in result["ref_a"]
    assert "2024-01-01" in result["ref_b"]
