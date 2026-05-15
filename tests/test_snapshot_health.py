"""Tests for reqwatch.snapshot_health."""
import time
import pytest

from reqwatch.storage import save_snapshot
from reqwatch.snapshot_health import HealthError, check_health, check_all_endpoints


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(store, endpoint, status=200, error=None, ts_offset=0):
    snap = {
        "endpoint": endpoint,
        "status": status,
        "body": {"ok": True},
        "headers": {},
        "timestamp": time.time() + ts_offset,
    }
    if error:
        snap["error"] = error
    save_snapshot(store, endpoint, snap)
    return snap


def test_no_snapshots_raises(store):
    with pytest.raises(HealthError, match="No snapshots"):
        check_health(store, "missing")


def test_all_ok_is_healthy(store):
    for i in range(5):
        _snap(store, "api", ts_offset=i)
    report = check_health(store, "api")
    assert report.healthy is True
    assert report.reason == "ok"
    assert report.error_count == 0


def test_consecutive_errors_marks_unhealthy(store):
    _snap(store, "api", ts_offset=0)
    for i in range(3):
        _snap(store, "api", status=500, error="timeout", ts_offset=i + 1)
    report = check_health(store, "api", consecutive_limit=3)
    assert report.healthy is False
    assert "consecutive" in report.reason
    assert report.consecutive_errors == 3


def test_high_error_rate_marks_unhealthy(store):
    # 6 errors out of 8 = 75% > default 50%
    for i in range(2):
        _snap(store, "api", ts_offset=i)
    for i in range(6):
        _snap(store, "api", status=503, error="server error", ts_offset=i + 2)
    report = check_health(store, "api", consecutive_limit=99)
    assert report.healthy is False
    assert "error rate" in report.reason


def test_low_error_rate_still_healthy(store):
    for i in range(9):
        _snap(store, "api", ts_offset=i)
    _snap(store, "api", status=500, error="blip", ts_offset=9)
    report = check_health(store, "api", error_threshold=0.5, consecutive_limit=99)
    assert report.healthy is True
    assert report.error_count == 1


def test_last_status_reflects_most_recent(store):
    _snap(store, "api", status=200, ts_offset=0)
    _snap(store, "api", status=404, ts_offset=1)
    report = check_health(store, "api")
    assert report.last_status == 404


def test_window_limits_snapshots_considered(store):
    # 10 old successes + 6 recent errors; window=6 => 100% error rate
    for i in range(10):
        _snap(store, "api", ts_offset=i)
    for i in range(6):
        _snap(store, "api", status=500, error="err", ts_offset=i + 10)
    report = check_health(store, "api", window=6, error_threshold=0.5, consecutive_limit=99)
    assert report.healthy is False
    assert report.total == 6


def test_check_all_endpoints_returns_reports(store):
    _snap(store, "alpha", ts_offset=0)
    _snap(store, "beta", ts_offset=0)
    reports = check_all_endpoints(store)
    names = {r.endpoint for r in reports}
    assert "alpha" in names
    assert "beta" in names


def test_check_all_endpoints_empty_store(store):
    reports = check_all_endpoints(store)
    assert reports == []
