"""Integration tests for snapshot_chain — exercises the full build + summarize pipeline."""

from __future__ import annotations

import time
import pytest

from reqwatch.snapshot_chain import build_chain, summarize_chain
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _make_snap(body, status=200):
    return {
        "status": status,
        "body": body,
        "headers": {"content-type": "application/json"},
        "timestamp": str(time.time()),
        "error": None,
    }


def _seed(store, endpoint, snaps):
    for i, s in enumerate(snaps):
        save_snapshot(store, endpoint, f"{i:04d}", s)


def test_chain_reflects_all_transitions(store):
    bodies = [{"v": 1}, {"v": 1}, {"v": 2}, {"v": 2}, {"v": 3}]
    _seed(store, "ep", [_make_snap(b) for b in bodies])
    chain = build_chain(store, "ep")
    assert chain.length == 5
    # changes at index 2 and 4
    assert chain.change_count == 2
    changed_indices = [i for i, lk in enumerate(chain.links) if lk.has_change]
    assert changed_indices == [2, 4]


def test_multiple_endpoints_are_isolated(store):
    _seed(store, "ep_a", [_make_snap({"a": 1}), _make_snap({"a": 2})])
    _seed(store, "ep_b", [_make_snap({"b": 99}), _make_snap({"b": 99})])
    chain_a = build_chain(store, "ep_a")
    chain_b = build_chain(store, "ep_b")
    assert chain_a.change_count == 1
    assert chain_b.change_count == 0


def test_summarize_stability_pct_matches_manual_calc(store):
    bodies = [{"n": i % 2} for i in range(6)]  # alternating 0,1,0,1,0,1 => 5 changes
    _seed(store, "ep", [_make_snap(b) for b in bodies])
    chain = build_chain(store, "ep")
    summary = summarize_chain(chain)
    expected_stability = round(100.0 * (6 - 5) / 6, 2)
    assert summary["stability_pct"] == expected_stability
