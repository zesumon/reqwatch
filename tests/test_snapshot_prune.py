"""Tests for reqwatch.snapshot_prune and reqwatch.cli_prune."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import pytest

from reqwatch.snapshot_prune import prune_snapshots, prune_all_endpoints, PruneError
from reqwatch.storage import save_snapshot
from reqwatch.cli_prune import cmd_prune


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(store, endpoint, ts_suffix):
    snap = {
        "endpoint": endpoint,
        "timestamp": f"2024-01-01T00:00:{ts_suffix}Z",
        "status_code": 200,
        "body": {"v": ts_suffix},
        "headers": {},
        "error": None,
    }
    save_snapshot(store, endpoint, snap)
    return snap["timestamp"]


def test_prune_keeps_n_most_recent(store):
    for i in range(5):
        _snap(store, "ep1", f"{i:02d}")

    deleted = prune_snapshots(store, "ep1", keep=3)
    assert len(deleted) == 2

    from reqwatch.storage import list_snapshots
    remaining = list_snapshots(store, "ep1")
    assert len(remaining) == 3


def test_prune_nothing_to_delete(store):
    for i in range(3):
        _snap(store, "ep1", f"{i:02d}")

    deleted = prune_snapshots(store, "ep1", keep=10)
    assert deleted == []


def test_prune_keep_less_than_one_raises(store):
    with pytest.raises(PruneError, match="keep must be >= 1"):
        prune_snapshots(store, "ep1", keep=0)


def test_prune_missing_endpoint_returns_empty(store):
    deleted = prune_snapshots(store, "no-such-endpoint", keep=5)
    assert deleted == []


def test_prune_all_endpoints(store):
    for i in range(4):
        _snap(store, "ep1", f"{i:02d}")
    for i in range(4):
        _snap(store, "ep2", f"{i:02d}")

    result = prune_all_endpoints(store, keep=2)
    assert "ep1" in result
    assert "ep2" in result
    assert len(result["ep1"]) == 2
    assert len(result["ep2"]) == 2


def test_prune_all_empty_store(store):
    result = prune_all_endpoints(store, keep=5)
    assert result == {}


# --- CLI tests ---

def _make_args(**kwargs):
    defaults = {
        "store": None,
        "endpoint": None,
        "keep": 10,
        "json": False,
        "func": cmd_prune,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_prune_text_output(store, capsys):
    for i in range(5):
        _snap(store, "ep1", f"{i:02d}")

    args = _make_args(store=store, endpoint="ep1", keep=3)
    cmd_prune(args)
    out = capsys.readouterr().out
    assert "deleted" in out
    assert "2 snapshot(s) removed" in out


def test_cmd_prune_json_output(store, capsys):
    for i in range(4):
        _snap(store, "ep1", f"{i:02d}")

    args = _make_args(store=store, endpoint="ep1", keep=2, json=True)
    cmd_prune(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "ep1" in data
    assert len(data["ep1"]) == 2


def test_cmd_prune_nothing_to_prune_message(store, capsys):
    _snap(store, "ep1", "00")

    args = _make_args(store=store, endpoint="ep1", keep=10)
    cmd_prune(args)
    out = capsys.readouterr().out
    assert "Nothing to prune" in out
