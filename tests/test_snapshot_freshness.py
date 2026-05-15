"""Tests for reqwatch.snapshot_freshness."""

import pytest

from reqwatch.snapshot_freshness import (
    FreshnessError,
    FreshnessReport,
    check_all_freshness,
    check_freshness,
)
from reqwatch.storage import save_snapshot

ENDPOINT = "https://api.example.com/v1/data"
NOW = 1_700_000_000.0


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(store, endpoint, ts, status=200, body=None):
    snap = {
        "endpoint": endpoint,
        "timestamp": ts,
        "status": status,
        "body": body or {"ok": True},
        "headers": {},
        "error": None,
    }
    save_snapshot(store, endpoint, snap)
    return snap


# ---------------------------------------------------------------------------
# check_freshness
# ---------------------------------------------------------------------------

def test_no_snapshots_returns_not_fresh(store):
    report = check_freshness(store, ENDPOINT, max_age_seconds=60, _now=NOW)
    assert isinstance(report, FreshnessReport)
    assert report.snapshot_count == 0
    assert report.latest_ts is None
    assert report.age_seconds is None
    assert report.is_fresh is False


def test_fresh_snapshot_within_max_age(store):
    _snap(store, ENDPOINT, ts=NOW - 30)  # 30 s ago
    report = check_freshness(store, ENDPOINT, max_age_seconds=60, _now=NOW)
    assert report.is_fresh is True
    assert report.age_seconds == pytest.approx(30.0)
    assert report.snapshot_count == 1


def test_stale_snapshot_exceeds_max_age(store):
    _snap(store, ENDPOINT, ts=NOW - 7200)  # 2 h ago
    report = check_freshness(store, ENDPOINT, max_age_seconds=3600, _now=NOW)
    assert report.is_fresh is False
    assert report.age_seconds == pytest.approx(7200.0)


def test_exactly_at_max_age_is_fresh(store):
    _snap(store, ENDPOINT, ts=NOW - 3600)
    report = check_freshness(store, ENDPOINT, max_age_seconds=3600, _now=NOW)
    assert report.is_fresh is True


def test_multiple_snapshots_uses_latest(store):
    _snap(store, ENDPOINT, ts=NOW - 500)
    _snap(store, ENDPOINT, ts=NOW - 100)  # most recent
    report = check_freshness(store, ENDPOINT, max_age_seconds=200, _now=NOW)
    assert report.is_fresh is True
    assert report.age_seconds == pytest.approx(100.0)
    assert report.snapshot_count == 2


def test_invalid_max_age_raises(store):
    with pytest.raises(FreshnessError):
        check_freshness(store, ENDPOINT, max_age_seconds=0, _now=NOW)


def test_negative_max_age_raises(store):
    with pytest.raises(FreshnessError):
        check_freshness(store, ENDPOINT, max_age_seconds=-10, _now=NOW)


# ---------------------------------------------------------------------------
# check_all_freshness
# ---------------------------------------------------------------------------

def test_check_all_freshness_returns_dict(store):
    ep1 = "https://api.example.com/a"
    ep2 = "https://api.example.com/b"
    _snap(store, ep1, ts=NOW - 10)
    _snap(store, ep2, ts=NOW - 9000)

    reports = check_all_freshness(store, [ep1, ep2], max_age_seconds=3600, _now=NOW)
    assert set(reports.keys()) == {ep1, ep2}
    assert reports[ep1].is_fresh is True
    assert reports[ep2].is_fresh is False


def test_check_all_freshness_empty_list(store):
    reports = check_all_freshness(store, [], _now=NOW)
    assert reports == {}
