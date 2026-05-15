"""Integration tests for snapshot TTL with real storage."""

from __future__ import annotations

import time
import pytest

from reqwatch.snapshot_ttl import find_stale, set_ttl
from reqwatch.snapshot_prune import prune_snapshots
from reqwatch.storage import list_snapshots, save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _make_snap(store, endpoint, ts, body=None):
    snap = {
        "timestamp": ts,
        "status": 200,
        "body": body or {"value": ts},
        "headers": {},
        "error": None,
    }
    save_snapshot(store, endpoint, snap)


def test_stale_snapshots_can_be_pruned(store):
    """Snapshots identified as stale should be prunable via prune_snapshots."""
    now = time.time()
    set_ttl(store, "api", 100)
    for offset in [500, 400, 300, 50, 10]:
        _make_snap(store, "api", now - offset)

    stale = find_stale(store, "api", now=now)
    assert len(stale) == 3  # offsets 500, 400, 300 exceed TTL of 100s

    # prune to keep only 2 most recent
    result = prune_snapshots(store, "api", keep=2)
    assert result.deleted == 3
    remaining = list_snapshots(store, "api")
    assert len(remaining) == 2


def test_ttl_does_not_affect_other_endpoints(store):
    now = time.time()
    set_ttl(store, "api/v1", 60)
    _make_snap(store, "api/v1", now - 200)
    _make_snap(store, "api/v2", now - 200)

    stale_v1 = find_stale(store, "api/v1", now=now)
    stale_v2 = find_stale(store, "api/v2", now=now)

    assert len(stale_v1) == 1
    assert len(stale_v2) == 0  # no TTL set


def test_all_fresh_after_ttl_update(store):
    now = time.time()
    set_ttl(store, "api", 60)
    _make_snap(store, "api", now - 120)

    assert len(find_stale(store, "api", now=now)) == 1

    # extend TTL so snapshot is no longer stale
    set_ttl(store, "api", 300)
    assert len(find_stale(store, "api", now=now)) == 0
