"""Tests for reqwatch.snapshot_search."""

from __future__ import annotations

import time
import pytest

from reqwatch.snapshot_search import SearchError, search_snapshots
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(endpoint, body, status_code=200, error=None, ts=None):
    return {
        "endpoint": endpoint,
        "timestamp": ts or str(time.time()),
        "status_code": status_code,
        "headers": {},
        "body": body,
        "error": error,
    }


def _seed(store, endpoint, snaps):
    for snap in snaps:
        save_snapshot(store, endpoint, snap)
        time.sleep(0.01)


# ---------------------------------------------------------------------------

def test_returns_all_when_no_filters(store):
    _seed(store, "ep", [_snap("ep", {"k": i}) for i in range(3)])
    results = search_snapshots(store, "ep")
    assert len(results) == 3


def test_results_are_newest_first(store):
    _seed(store, "ep", [_snap("ep", {"n": i}) for i in range(3)])
    results = search_snapshots(store, "ep")
    ns = [r["body"]["n"] for r in results]
    assert ns == sorted(ns, reverse=True)


def test_text_filter_matches_body(store):
    _seed(store, "ep", [
        _snap("ep", {"msg": "hello world"}),
        _snap("ep", {"msg": "goodbye"}),
    ])
    results = search_snapshots(store, "ep", text="hello")
    assert len(results) == 1
    assert results[0]["body"]["msg"] == "hello world"


def test_text_filter_is_case_insensitive(store):
    _seed(store, "ep", [_snap("ep", {"msg": "Hello World"})])
    assert len(search_snapshots(store, "ep", text="HELLO")) == 1


def test_status_code_filter(store):
    _seed(store, "ep", [
        _snap("ep", {}, status_code=200),
        _snap("ep", {}, status_code=404),
    ])
    results = search_snapshots(store, "ep", status_code=404)
    assert all(r["status_code"] == 404 for r in results)
    assert len(results) == 1


def test_has_error_true_filter(store):
    _seed(store, "ep", [
        _snap("ep", {}, error="timeout"),
        _snap("ep", {}),
    ])
    results = search_snapshots(store, "ep", has_error=True)
    assert len(results) == 1
    assert results[0]["error"] == "timeout"


def test_has_error_false_filter(store):
    _seed(store, "ep", [
        _snap("ep", {}, error="oops"),
        _snap("ep", {}),
    ])
    results = search_snapshots(store, "ep", has_error=False)
    assert all(r["error"] is None for r in results)


def test_limit_respected(store):
    _seed(store, "ep", [_snap("ep", {"i": i}) for i in range(10)])
    results = search_snapshots(store, "ep", limit=3)
    assert len(results) == 3


def test_limit_less_than_one_raises(store):
    with pytest.raises(SearchError):
        search_snapshots(store, "ep", limit=0)


def test_no_snapshots_returns_empty(store):
    assert search_snapshots(store, "nonexistent") == []


def test_combined_filters(store):
    _seed(store, "ep", [
        _snap("ep", {"user": "alice"}, status_code=200),
        _snap("ep", {"user": "bob"}, status_code=200),
        _snap("ep", {"user": "alice"}, status_code=500),
    ])
    results = search_snapshots(store, "ep", text="alice", status_code=200)
    assert len(results) == 1
    assert results[0]["body"]["user"] == "alice"
    assert results[0]["status_code"] == 200
