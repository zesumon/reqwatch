"""Tests for reqwatch.cli_ttl."""

from __future__ import annotations

import argparse
import json
import time
import pytest

from reqwatch.cli_ttl import cmd_ttl
from reqwatch.snapshot_ttl import set_ttl
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _make_args(store, endpoint, ttl_action, **kwargs):
    ns = argparse.Namespace(store=store, endpoint=endpoint, ttl_action=ttl_action)
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


def _snap(store, endpoint, ts):
    snap = {"timestamp": ts, "status": 200, "body": {}, "headers": {}, "error": None}
    save_snapshot(store, endpoint, snap)


def test_cmd_ttl_set_prints_confirmation(store, capsys):
    args = _make_args(store, "api/v1", "set", seconds=300.0)
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "300" in out
    assert "api/v1" in out


def test_cmd_ttl_get_prints_value(store, capsys):
    set_ttl(store, "api/v1", 120)
    args = _make_args(store, "api/v1", "get")
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "120" in out


def test_cmd_ttl_get_missing_prints_message(store, capsys):
    args = _make_args(store, "api/v1", "get")
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "No TTL" in out


def test_cmd_ttl_clear_existing(store, capsys):
    set_ttl(store, "api/v1", 60)
    args = _make_args(store, "api/v1", "clear")
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "cleared" in out


def test_cmd_ttl_clear_missing(store, capsys):
    args = _make_args(store, "api/v1", "clear")
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "No TTL found" in out


def test_cmd_ttl_stale_no_results(store, capsys):
    set_ttl(store, "api/v1", 3600)
    _snap(store, "api/v1", time.time() - 10)
    args = _make_args(store, "api/v1", "stale")
    cmd_ttl(args)
    out = capsys.readouterr().out
    assert "No stale" in out


def test_cmd_ttl_stale_with_results(store, capsys):
    set_ttl(store, "api/v1", 60)
    _snap(store, "api/v1", time.time() - 300)
    args = _make_args(store, "api/v1", "stale")
    cmd_ttl(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 1
    assert "snapshot_id" in data[0]
    assert data[0]["ttl_seconds"] == 60


def test_cmd_ttl_set_invalid_exits(store, capsys):
    args = _make_args(store, "api/v1", "set", seconds=-1.0)
    with pytest.raises(SystemExit) as exc_info:
        cmd_ttl(args)
    assert exc_info.value.code == 1
