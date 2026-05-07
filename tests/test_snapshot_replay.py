"""Tests for snapshot_replay and cli_replay."""

from __future__ import annotations

import json
import argparse
from io import StringIO
from unittest.mock import patch

import pytest

from reqwatch.snapshot_replay import replay_endpoint, summarize_replay, ReplayError


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(ts: str, body: dict):
    return {"timestamp": ts, "status": 200, "body": body, "error": None}


def _seed(store_dir, endpoint, snaps):
    from reqwatch.storage import save_snapshot
    for ts, body in snaps:
        save_snapshot(store_dir, endpoint, _snap(ts, body))


def test_replay_no_snapshots_raises(store):
    with pytest.raises(ReplayError, match="No snapshots found"):
        replay_endpoint(store, "api/missing")


def test_replay_single_snapshot_no_change(store):
    _seed(store, "api/v1", [("2024-01-01T00:00:00", {"x": 1})])
    events = replay_endpoint(store, "api/v1")
    assert len(events) == 1
    assert events[0].changed is False
    assert events[0].diff == {}


def test_replay_detects_change(store):
    _seed(store, "api/v1", [
        ("2024-01-01T00:00:00", {"x": 1}),
        ("2024-01-02T00:00:00", {"x": 2}),
    ])
    events = replay_endpoint(store, "api/v1")
    assert len(events) == 2
    assert events[0].changed is False
    assert events[1].changed is True


def test_replay_stable_sequence(store):
    _seed(store, "api/v1", [
        ("2024-01-01T00:00:00", {"x": 1}),
        ("2024-01-02T00:00:00", {"x": 1}),
        ("2024-01-03T00:00:00", {"x": 1}),
    ])
    events = replay_endpoint(store, "api/v1")
    assert all(not e.changed for e in events)


def test_replay_limit(store):
    _seed(store, "api/v1", [
        ("2024-01-01T00:00:00", {"x": 1}),
        ("2024-01-02T00:00:00", {"x": 2}),
        ("2024-01-03T00:00:00", {"x": 3}),
    ])
    events = replay_endpoint(store, "api/v1", limit=2)
    assert len(events) == 2


def test_replay_limit_less_than_one_raises(store):
    _seed(store, "api/v1", [("2024-01-01T00:00:00", {"x": 1})])
    with pytest.raises(ReplayError, match="limit must be"):
        replay_endpoint(store, "api/v1", limit=0)


def test_summarize_replay_counts(store):
    _seed(store, "api/v1", [
        ("2024-01-01T00:00:00", {"x": 1}),
        ("2024-01-02T00:00:00", {"x": 2}),
        ("2024-01-03T00:00:00", {"x": 2}),
    ])
    events = replay_endpoint(store, "api/v1")
    summary = summarize_replay(events)
    assert summary["total"] == 3
    assert summary["changes"] == 1
    assert summary["stable"] == 2


def test_summarize_empty():
    summary = summarize_replay([])
    assert summary == {"total": 0, "changes": 0, "stable": 0}


def test_cmd_replay_json_output(store, capsys):
    from reqwatch.cli_replay import cmd_replay
    _seed(store, "api/v1", [
        ("2024-01-01T00:00:00", {"x": 1}),
        ("2024-01-02T00:00:00", {"x": 2}),
    ])
    args = argparse.Namespace(
        store=store, endpoint="api/v1", limit=None, json=True, summarize=False
    )
    cmd_replay(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 2


def test_cmd_replay_summarize(store, capsys):
    from reqwatch.cli_replay import cmd_replay
    _seed(store, "api/v1", [("2024-01-01T00:00:00", {"x": 1})])
    args = argparse.Namespace(
        store=store, endpoint="api/v1", limit=None, json=False, summarize=True
    )
    cmd_replay(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "total" in data
