"""Tests for reqwatch.snapshot_stats."""

import json
import pytest

from reqwatch.snapshot_stats import compute_stats, StatsError, _status_counts, _error_rate, _avg_body_size
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _make_snap(status_code=200, body=None, error=None, timestamp="2024-01-01T00:00:00"):
    return {
        "endpoint": "https://api.example.com/data",
        "timestamp": timestamp,
        "status_code": status_code,
        "headers": {},
        "body": body or {"key": "value"},
        "error": error,
    }


def _seed(store, endpoint, count=3):
    for i in range(count):
        snap = _make_snap(timestamp=f"2024-01-0{i+1}T00:00:00")
        save_snapshot(store, endpoint, snap)


EP = "https://api.example.com/data"


def test_compute_stats_basic(store):
    _seed(store, EP, count=3)
    stats = compute_stats(store, EP)
    assert stats["endpoint"] == EP
    assert stats["total_snapshots"] == 3
    assert stats["status_counts"] == {200: 3}
    assert stats["error_rate"] == 0.0


def test_compute_stats_no_snapshots_raises(store):
    with pytest.raises(StatsError, match="No snapshots"):
        compute_stats(store, EP)


def test_compute_stats_respects_limit(store):
    _seed(store, EP, count=10)
    stats = compute_stats(store, EP, limit=4)
    assert stats["total_snapshots"] == 4


def test_compute_stats_error_rate(store):
    snaps = [
        _make_snap(error="timeout", timestamp="2024-01-01T00:00:00"),
        _make_snap(timestamp="2024-01-02T00:00:00"),
        _make_snap(error="connection refused", timestamp="2024-01-03T00:00:00"),
        _make_snap(timestamp="2024-01-04T00:00:00"),
    ]
    for s in snaps:
        save_snapshot(store, EP, s)
    stats = compute_stats(store, EP)
    assert stats["error_rate"] == 0.5


def test_compute_stats_timestamps_present(store):
    _seed(store, EP, count=2)
    stats = compute_stats(store, EP)
    assert stats["first_timestamp"] is not None
    assert stats["last_timestamp"] is not None


def test_status_counts_mixed():
    snaps = [{"status_code": 200}, {"status_code": 404}, {"status_code": 200}, {"status_code": 500}]
    counts = _status_counts(snaps)
    assert counts == {200: 2, 404: 1, 500: 1}


def test_avg_body_size_string_body():
    snaps = [{"body": "hello"}, {"body": "world!"}]
    avg = _avg_body_size(snaps)
    assert avg == (5 + 6) / 2


def test_avg_body_size_no_body():
    assert _avg_body_size([]) == 0.0


def test_error_rate_all_ok():
    snaps = [{"error": None}, {"error": None}]
    assert _error_rate(snaps) == 0.0


def test_error_rate_empty():
    assert _error_rate([]) == 0.0
