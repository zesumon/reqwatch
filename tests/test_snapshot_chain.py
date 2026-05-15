"""Tests for reqwatch.snapshot_chain."""

from __future__ import annotations

import time
import pytest

from reqwatch.snapshot_chain import (
    ChainError,
    ChainLink,
    SnapshotChain,
    build_chain,
    summarize_chain,
)
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(status=200, body=None, ts=None):
    return {
        "status": status,
        "body": body or {"value": 1},
        "headers": {},
        "timestamp": ts or str(time.time()),
        "error": None,
    }


def _seed(store, endpoint, snaps):
    ids = []
    for i, s in enumerate(snaps):
        sid = f"snap{i:03d}"
        save_snapshot(store, endpoint, sid, s)
        ids.append(sid)
    return ids


def test_no_snapshots_raises(store):
    with pytest.raises(ChainError, match="No snapshots"):
        build_chain(store, "https://api.example.com/v1")


def test_single_snapshot_no_change(store):
    _seed(store, "ep", [_snap()])
    chain = build_chain(store, "ep")
    assert chain.length == 1
    assert chain.change_count == 0
    assert chain.links[0].has_change is False
    assert chain.links[0].parent_id is None
    assert chain.links[0].child_id is None


def test_two_identical_snapshots_no_change(store):
    _seed(store, "ep", [_snap(body={"x": 1}), _snap(body={"x": 1})])
    chain = build_chain(store, "ep")
    assert chain.length == 2
    assert chain.change_count == 0


def test_two_different_snapshots_detects_change(store):
    _seed(store, "ep", [_snap(body={"x": 1}), _snap(body={"x": 2})])
    chain = build_chain(store, "ep")
    assert chain.length == 2
    assert chain.change_count == 1
    assert chain.links[0].has_change is False
    assert chain.links[1].has_change is True


def test_parent_child_linkage(store):
    ids = _seed(store, "ep", [_snap(), _snap(), _snap()])
    chain = build_chain(store, "ep")
    assert chain.links[0].parent_id is None
    assert chain.links[0].child_id == chain.links[1].snapshot_id
    assert chain.links[1].parent_id == chain.links[0].snapshot_id
    assert chain.links[1].child_id == chain.links[2].snapshot_id
    assert chain.links[2].child_id is None


def test_summarize_chain_structure(store):
    _seed(store, "ep", [_snap(body={"a": 1}), _snap(body={"a": 2}), _snap(body={"a": 2})])
    chain = build_chain(store, "ep")
    summary = summarize_chain(chain)
    assert summary["endpoint"] == "ep"
    assert summary["total_snapshots"] == 3
    assert summary["total_changes"] == 1
    assert 0.0 <= summary["stability_pct"] <= 100.0
    assert len(summary["links"]) == 3


def test_stability_pct_all_stable(store):
    _seed(store, "ep", [_snap(body={"v": 0})] * 4)
    chain = build_chain(store, "ep")
    assert summarize_chain(chain)["stability_pct"] == 100.0


def test_chain_link_summary_text(store):
    _seed(store, "ep", [_snap(status=200, body={"k": 1}), _snap(status=200, body={"k": 99})])
    chain = build_chain(store, "ep")
    assert "changed" in chain.links[1].summary
    assert "stable" in chain.links[0].summary
