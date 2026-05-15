"""Integration tests: watchdog works correctly with real on-disk storage."""
from __future__ import annotations

import time
import pytest

from reqwatch.snapshot_watchdog import run_watchdog
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


NOW = 1_700_100_000.0


def _make_snap(store, endpoint, age_seconds):
    snap = {
        "endpoint": endpoint,
        "timestamp": NOW - age_seconds,
        "status": 200,
        "body": {"value": age_seconds},
        "headers": {},
        "error": None,
    }
    save_snapshot(store, endpoint, snap)


def test_all_fresh_no_stale(store):
    for ep in ["a", "b", "c"]:
        _make_snap(store, ep, age_seconds=30)
    report = run_watchdog(store, ["a", "b", "c"], threshold_seconds=3600, now=NOW)
    assert len(report.stale) == 0
    assert len(report.silent) == 0


def test_mixed_fresh_and_stale(store):
    _make_snap(store, "fresh", age_seconds=60)
    _make_snap(store, "stale", age_seconds=7200)
    report = run_watchdog(store, ["fresh", "stale"], threshold_seconds=3600, now=NOW)
    stale_names = {r.endpoint for r in report.stale}
    assert "stale" in stale_names
    assert "fresh" not in stale_names


def test_multiple_snapshots_uses_latest(store):
    # save an old one first, then a fresh one
    _make_snap(store, "ep", age_seconds=9000)
    _make_snap(store, "ep", age_seconds=5)
    report = run_watchdog(store, ["ep"], threshold_seconds=3600, now=NOW)
    assert len(report.stale) == 0


def test_endpoints_are_isolated(store):
    _make_snap(store, "good", age_seconds=10)
    # "bad" has no snapshots
    report = run_watchdog(store, ["good", "bad"], threshold_seconds=60, now=NOW)
    silent_names = {r.endpoint for r in report.silent}
    assert "bad" in silent_names
    assert "good" not in silent_names
