"""Tests for reqwatch.snapshot_retention."""

from __future__ import annotations

import time
import pytest

from reqwatch.storage import save_snapshot, list_snapshots
from reqwatch.snapshot_retention import (
    RetentionError,
    RetentionResult,
    _cutoff_ts,
    apply_retention,
    apply_retention_all,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(ts: float, status: int = 200) -> dict:
    return {
        "endpoint": "https://api.example.com/data",
        "timestamp": ts,
        "status": status,
        "headers": {},
        "body": {"ok": True},
    }


ENDPOINT = "https://api.example.com/data"
NOW = time.time()
OLD = NOW - 10 * 86_400  # 10 days ago
RECENT = NOW - 1 * 86_400  # 1 day ago


# ---------------------------------------------------------------------------
# _cutoff_ts
# ---------------------------------------------------------------------------

def test_cutoff_ts_returns_float():
    assert isinstance(_cutoff_ts(7), float)


def test_cutoff_ts_invalid_raises():
    with pytest.raises(RetentionError):
        _cutoff_ts(0)


# ---------------------------------------------------------------------------
# apply_retention
# ---------------------------------------------------------------------------

def test_no_snapshots_returns_zero_result(store):
    result = apply_retention(store, ENDPOINT, max_age_days=7)
    assert result.total == 0
    assert result.removed == 0
    assert result.kept == 0


def test_recent_snapshot_not_removed(store):
    save_snapshot(store, ENDPOINT, _snap(RECENT))
    result = apply_retention(store, ENDPOINT, max_age_days=7)
    assert result.removed == 0
    assert len(list_snapshots(store, ENDPOINT)) == 1


def test_old_snapshot_removed(store):
    save_snapshot(store, ENDPOINT, _snap(OLD))
    save_snapshot(store, ENDPOINT, _snap(RECENT))
    result = apply_retention(store, ENDPOINT, max_age_days=7)
    # one old snapshot should have been pruned
    assert result.removed >= 1
    remaining = list_snapshots(store, ENDPOINT)
    assert len(remaining) >= 1  # at least one kept


def test_always_keeps_at_least_one(store):
    """Even if all snapshots are expired, one must survive."""
    save_snapshot(store, ENDPOINT, _snap(OLD))
    result = apply_retention(store, ENDPOINT, max_age_days=1)
    assert result.kept >= 1
    assert len(list_snapshots(store, ENDPOINT)) >= 1


def test_result_is_retention_result_instance(store):
    save_snapshot(store, ENDPOINT, _snap(RECENT))
    result = apply_retention(store, ENDPOINT, max_age_days=7)
    assert isinstance(result, RetentionResult)
    assert result.endpoint == ENDPOINT


# ---------------------------------------------------------------------------
# apply_retention_all
# ---------------------------------------------------------------------------

def test_apply_retention_all_multiple_endpoints(store):
    ep2 = "https://api.example.com/other"
    save_snapshot(store, ENDPOINT, _snap(RECENT))
    save_snapshot(store, ep2, _snap(OLD))

    policy = {ENDPOINT: 7, ep2: 3}
    results = apply_retention_all(store, policy)
    assert len(results) == 2
    endpoints_seen = {r.endpoint for r in results}
    assert ENDPOINT in endpoints_seen
    assert ep2 in endpoints_seen


def test_apply_retention_all_empty_policy(store):
    results = apply_retention_all(store, {})
    assert results == []
