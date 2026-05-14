"""Tests for reqwatch.snapshot_trend."""

from __future__ import annotations

import pytest

from reqwatch.snapshot_trend import build_trend, TrendError, TrendSummary


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(store, endpoint, ts, status=200, response_time=0.25, error=None):
    from reqwatch.storage import save_snapshot

    snap = {
        "endpoint": endpoint,
        "timestamp": ts,
        "status": status,
        "body": {"ok": True},
        "response_time": response_time,
    }
    if error:
        snap["error"] = error
    save_snapshot(store, endpoint, snap)
    return snap


def _seed(store, endpoint, n=5):
    for i in range(n):
        ts = f"2024-01-{i+1:02d}T12:00:00"
        _snap(store, endpoint, ts, status=200, response_time=round(0.1 * (i + 1), 2))


def test_no_snapshots_raises(store):
    with pytest.raises(TrendError, match="No snapshots"):
        build_trend(store, "api/missing")


def test_returns_trend_summary(store):
    _seed(store, "api/v1", n=5)
    result = build_trend(store, "api/v1")
    assert isinstance(result, TrendSummary)
    assert result.endpoint == "api/v1"


def test_points_count_matches_snapshots(store):
    _seed(store, "api/v1", n=7)
    result = build_trend(store, "api/v1")
    assert len(result.points) == 7


def test_limit_respected(store):
    _seed(store, "api/v1", n=10)
    result = build_trend(store, "api/v1", limit=4)
    assert len(result.points) == 4


def test_avg_response_time_correct(store):
    _seed(store, "api/v1", n=4)  # times: 0.1, 0.2, 0.3, 0.4 -> avg 0.25
    result = build_trend(store, "api/v1")
    assert result.avg_response_time == pytest.approx(0.25, abs=1e-4)


def test_p95_response_time_populated(store):
    _seed(store, "api/v1", n=5)
    result = build_trend(store, "api/v1")
    assert result.p95_response_time is not None
    assert result.p95_response_time >= result.avg_response_time


def test_error_rate_zero_when_no_errors(store):
    _seed(store, "api/v1", n=5)
    result = build_trend(store, "api/v1")
    assert result.error_rate == 0.0


def test_error_rate_with_errors(store):
    for i in range(4):
        _snap(store, "api/v1", f"2024-01-{i+1:02d}T00:00:00", status=200)
    _snap(store, "api/v1", "2024-01-05T00:00:00", status=0, error="timeout")
    result = build_trend(store, "api/v1")
    assert result.error_rate == pytest.approx(0.2, abs=1e-4)


def test_dominant_status_is_most_common(store):
    for i in range(3):
        _snap(store, "api/v1", f"2024-01-{i+1:02d}T00:00:00", status=200)
    _snap(store, "api/v1", "2024-01-04T00:00:00", status=404)
    result = build_trend(store, "api/v1")
    assert result.dominant_status == 200


def test_no_response_time_fields_handled(store):
    from reqwatch.storage import save_snapshot

    snap = {"endpoint": "api/v1", "timestamp": "2024-01-01T00:00:00", "status": 200, "body": {}}
    save_snapshot(store, "api/v1", snap)
    result = build_trend(store, "api/v1")
    assert result.avg_response_time is None
    assert result.p95_response_time is None
