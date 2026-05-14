"""Integration tests: snapshot_trend works end-to-end with real storage."""

from __future__ import annotations

import pytest

from reqwatch.storage import save_snapshot
from reqwatch.snapshot_trend import build_trend


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _make_snap(store, endpoint, ts, status=200, rt=0.2, error=None):
    snap = {
        "endpoint": endpoint,
        "timestamp": ts,
        "status": status,
        "body": {"data": ts},
        "response_time": rt,
    }
    if error:
        snap["error"] = error
    save_snapshot(store, endpoint, snap)
    return snap


def test_trend_newest_first_ordering(store):
    """Trend should use the N most-recent snapshots regardless of insertion order."""
    for i in range(8):
        _make_snap(store, "api/v1", f"2024-0{i+1}-01T00:00:00", rt=float(i + 1))

    result = build_trend(store, "api/v1", limit=4)
    # most recent 4 have rt 5,6,7,8 -> avg 6.5
    assert result.avg_response_time == pytest.approx(6.5, abs=0.01)


def test_mixed_errors_and_successes(store):
    _make_snap(store, "api/v2", "2024-01-01T00:00:00", status=200, rt=0.1)
    _make_snap(store, "api/v2", "2024-01-02T00:00:00", status=200, rt=0.2)
    _make_snap(store, "api/v2", "2024-01-03T00:00:00", status=0, rt=None, error="conn refused")

    result = build_trend(store, "api/v2")
    assert result.error_rate == pytest.approx(1 / 3, abs=0.01)
    # only two non-error points have response times
    assert result.avg_response_time == pytest.approx(0.15, abs=0.01)


def test_multiple_endpoints_isolated(store):
    _make_snap(store, "api/a", "2024-01-01T00:00:00", status=200, rt=1.0)
    _make_snap(store, "api/b", "2024-01-01T00:00:00", status=500, rt=9.0)

    trend_a = build_trend(store, "api/a")
    trend_b = build_trend(store, "api/b")

    assert trend_a.dominant_status == 200
    assert trend_b.dominant_status == 500
    assert trend_a.avg_response_time != trend_b.avg_response_time
