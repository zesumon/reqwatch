"""Tests for reqwatch.snapshot_watchdog."""
from __future__ import annotations

import time
import pytest

from reqwatch.snapshot_watchdog import (
    WatchdogError,
    WatchdogResult,
    check_endpoint,
    run_watchdog,
)
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(store, endpoint, ts, status=200):
    snap = {
        "endpoint": endpoint,
        "timestamp": ts,
        "status": status,
        "body": {"ok": True},
        "headers": {},
        "error": None,
    }
    save_snapshot(store, endpoint, snap)
    return snap


NOW = 1_700_000_000.0


def test_silent_when_no_snapshots(store):
    result = check_endpoint(store, "api/v1", threshold_seconds=60, now=NOW)
    assert result.is_silent is True
    assert result.is_stale is True
    assert result.last_seen is None
    assert result.age_seconds is None


def test_fresh_endpoint_not_stale(store):
    _snap(store, "api/v1", ts=NOW - 30)
    result = check_endpoint(store, "api/v1", threshold_seconds=60, now=NOW)
    assert result.is_silent is False
    assert result.is_stale is False
    assert pytest.approx(result.age_seconds, abs=1) == 30


def test_old_endpoint_is_stale(store):
    _snap(store, "api/v1", ts=NOW - 7200)
    result = check_endpoint(store, "api/v1", threshold_seconds=3600, now=NOW)
    assert result.is_stale is True
    assert result.is_silent is False


def test_exactly_at_threshold_is_not_stale(store):
    _snap(store, "api/v1", ts=NOW - 60)
    result = check_endpoint(store, "api/v1", threshold_seconds=60, now=NOW)
    # age == threshold is NOT stale (strictly greater)
    assert result.is_stale is False


def test_invalid_threshold_raises(store):
    with pytest.raises(WatchdogError):
        check_endpoint(store, "api/v1", threshold_seconds=0, now=NOW)


def test_run_watchdog_empty_endpoints_raises(store):
    with pytest.raises(WatchdogError):
        run_watchdog(store, [], threshold_seconds=60)


def test_run_watchdog_mixed_results(store):
    _snap(store, "fresh", ts=NOW - 10)
    _snap(store, "stale", ts=NOW - 9000)
    # "silent" has no snapshots
    report = run_watchdog(store, ["fresh", "stale", "silent"], threshold_seconds=3600, now=NOW)
    assert len(report.results) == 3
    assert len(report.stale) == 2   # stale + silent both count
    assert len(report.silent) == 1
    assert report.checked_at == NOW


def test_to_dict_structure(store):
    _snap(store, "api", ts=NOW - 5)
    report = run_watchdog(store, ["api"], threshold_seconds=60, now=NOW)
    d = report.to_dict()
    assert "checked_at" in d
    assert d["total"] == 1
    assert isinstance(d["results"], list)
    assert "is_stale" in d["results"][0]


def test_latest_snapshot_used_not_oldest(store):
    _snap(store, "api", ts=NOW - 9000)  # old
    _snap(store, "api", ts=NOW - 10)   # recent
    result = check_endpoint(store, "api", threshold_seconds=3600, now=NOW)
    assert result.is_stale is False
