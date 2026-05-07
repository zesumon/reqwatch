"""Integration tests combining query with real storage round-trips."""

import pytest
from reqwatch.storage import save_snapshot
from reqwatch.snapshots_query import query_snapshots, summarize_snapshots


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _make_snap(ts, status=200, error=None):
    s = {"timestamp": ts, "status_code": status, "body": {"key": "value"}}
    if error:
        s["error"] = error
    return s


def test_query_results_are_newest_first(store):
    timestamps = ["2024-01-01T00:00:00", "2024-01-03T00:00:00", "2024-01-02T00:00:00"]
    for ts in timestamps:
        save_snapshot(store, "svc", ts, _make_snap(ts))
    result = query_snapshots(store, "svc")
    returned_ts = [r["timestamp"] for r in result]
    assert returned_ts == sorted(timestamps, reverse=True)


def test_combined_filters_narrow_results(store):
    snaps = [
        _make_snap("2024-01-01T00:00:00", status=200),
        _make_snap("2024-01-02T00:00:00", status=500, error="crash"),
        _make_snap("2024-01-03T00:00:00", status=200),
    ]
    for s in snaps:
        save_snapshot(store, "svc", s["timestamp"], s)

    result = query_snapshots(
        store, "svc",
        since="2024-01-01T12:00:00",
        has_error=True,
    )
    assert len(result) == 1
    assert result[0]["status_code"] == 500


def test_summarize_after_query(store):
    snaps = [
        _make_snap("2024-01-01T00:00:00", status=200),
        _make_snap("2024-01-02T00:00:00", status=200, error="timeout"),
        _make_snap("2024-01-03T00:00:00", status=404),
    ]
    for s in snaps:
        save_snapshot(store, "svc", s["timestamp"], s)

    result = query_snapshots(store, "svc")
    summary = summarize_snapshots(result)

    assert summary["count"] == 3
    assert summary["error_count"] == 1
    assert set(summary["status_codes"]) == {200, 404}
    assert summary["earliest"] == "2024-01-01T00:00:00"
    assert summary["latest"] == "2024-01-03T00:00:00"
