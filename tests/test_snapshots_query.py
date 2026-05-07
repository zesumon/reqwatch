"""Tests for reqwatch.snapshots_query."""

import pytest
from reqwatch.snapshots_query import query_snapshots, summarize_snapshots
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(ts, status=200, error=None):
    s = {"timestamp": ts, "status_code": status, "body": {"v": 1}}
    if error:
        s["error"] = error
    return s


def _seed(store, endpoint, snaps):
    for snap in snaps:
        save_snapshot(store, endpoint, snap["timestamp"], snap)


def test_returns_all_when_no_filters(store):
    snaps = [_snap("2024-01-01T00:00:00"), _snap("2024-01-02T00:00:00")]
    _seed(store, "api", snaps)
    result = query_snapshots(store, "api")
    assert len(result) == 2


def test_limit_respected(store):
    snaps = [_snap(f"2024-01-0{i}T00:00:00") for i in range(1, 5)]
    _seed(store, "api", snaps)
    result = query_snapshots(store, "api", limit=2)
    assert len(result) == 2


def test_since_filter(store):
    _seed(store, "api", [_snap("2024-01-01T00:00:00"), _snap("2024-03-01T00:00:00")])
    result = query_snapshots(store, "api", since="2024-02-01T00:00:00")
    assert len(result) == 1
    assert result[0]["timestamp"] == "2024-03-01T00:00:00"


def test_until_filter(store):
    _seed(store, "api", [_snap("2024-01-01T00:00:00"), _snap("2024-03-01T00:00:00")])
    result = query_snapshots(store, "api", until="2024-02-01T00:00:00")
    assert len(result) == 1
    assert result[0]["timestamp"] == "2024-01-01T00:00:00"


def test_status_code_filter(store):
    _seed(store, "api", [_snap("2024-01-01T00:00:00", status=200),
                         _snap("2024-01-02T00:00:00", status=404)])
    result = query_snapshots(store, "api", status_code=404)
    assert len(result) == 1
    assert result[0]["status_code"] == 404


def test_has_error_true_filter(store):
    _seed(store, "api", [_snap("2024-01-01T00:00:00"),
                         _snap("2024-01-02T00:00:00", error="timeout")])
    result = query_snapshots(store, "api", has_error=True)
    assert len(result) == 1
    assert result[0]["error"] == "timeout"


def test_has_error_false_filter(store):
    _seed(store, "api", [_snap("2024-01-01T00:00:00"),
                         _snap("2024-01-02T00:00:00", error="timeout")])
    result = query_snapshots(store, "api", has_error=False)
    assert len(result) == 1
    assert "error" not in result[0]


def test_empty_store_returns_empty(store):
    result = query_snapshots(store, "missing")
    assert result == []


def test_summarize_snapshots_basic():
    snaps = [
        _snap("2024-01-01T00:00:00", status=200),
        _snap("2024-01-03T00:00:00", status=200, error="oops"),
        _snap("2024-01-02T00:00:00", status=500),
    ]
    summary = summarize_snapshots(snaps)
    assert summary["count"] == 3
    assert summary["error_count"] == 1
    assert 200 in summary["status_codes"]
    assert 500 in summary["status_codes"]
    assert summary["earliest"] == "2024-01-01T00:00:00"
    assert summary["latest"] == "2024-01-03T00:00:00"


def test_summarize_empty_returns_zero_count():
    assert summarize_snapshots([]) == {"count": 0}
