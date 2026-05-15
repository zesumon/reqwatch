"""Tests for reqwatch.cli_chain."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import pytest

from reqwatch.cli_chain import cmd_chain
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(body=None):
    return {"status": 200, "body": body or {"v": 1}, "headers": {}, "timestamp": "t", "error": None}


def _make_args(store, endpoint, summarize=False, fmt="json"):
    return SimpleNamespace(store=store, endpoint=endpoint, summarize=summarize, format=fmt)


def _seed(store, endpoint, snaps):
    for i, s in enumerate(snaps):
        save_snapshot(store, endpoint, f"s{i:03d}", s)


def test_cmd_chain_prints_json(store, capsys):
    _seed(store, "ep", [_snap({"a": 1}), _snap({"a": 2})])
    cmd_chain(_make_args(store, "ep"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["endpoint"] == "ep"
    assert data["total_snapshots"] == 2
    assert "links" in data


def test_cmd_chain_summarize_flag(store, capsys):
    _seed(store, "ep", [_snap(), _snap()])
    cmd_chain(_make_args(store, "ep", summarize=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "links" not in data
    assert "stability_pct" in data


def test_cmd_chain_text_format(store, capsys):
    _seed(store, "ep", [_snap({"x": 1}), _snap({"x": 2})])
    cmd_chain(_make_args(store, "ep", fmt="text"))
    out = capsys.readouterr().out
    assert "Chain for" in out
    assert "Stability" in out


def test_cmd_chain_no_snapshots_exits(store):
    with pytest.raises(SystemExit) as exc_info:
        cmd_chain(_make_args(store, "nonexistent"))
    assert exc_info.value.code == 1


def test_cmd_chain_change_count_in_output(store, capsys):
    _seed(store, "ep", [_snap({"v": 1}), _snap({"v": 2}), _snap({"v": 2})])
    cmd_chain(_make_args(store, "ep"))
    data = json.loads(capsys.readouterr().out)
    assert data["total_changes"] == 1
