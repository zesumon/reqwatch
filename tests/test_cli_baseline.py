"""Tests for reqwatch.cli_baseline (pin / show / clear sub-commands)."""

from __future__ import annotations

import json
from argparse import ArgumentParser
from unittest.mock import patch

import pytest

from reqwatch.baseline import save_baseline
from reqwatch.cli_baseline import cmd_baseline, register_baseline_subcommand
from reqwatch.storage import save_snapshot

ENDPOINT = "https://api.example.com/v1/data"
SNAP = {"url": ENDPOINT, "status": 200, "body": {"x": 1}, "timestamp": "2024-06-01T12:00:00"}


def _make_args(store_dir, action, key=ENDPOINT):
    p = ArgumentParser()
    sub = p.add_subparsers()
    register_baseline_subcommand(sub)
    return p.parse_args(["baseline", key, action, "--store-dir", store_dir])


def test_pin_stores_latest_snapshot(tmp_path, capsys):
    store = str(tmp_path)
    save_snapshot(store, ENDPOINT, SNAP)
    args = _make_args(store, "pin")
    rc = cmd_baseline(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Pinned" in out


def test_pin_fails_when_no_snapshots(tmp_path, capsys):
    args = _make_args(str(tmp_path), "pin")
    rc = cmd_baseline(args)
    assert rc == 1
    assert "No snapshots" in capsys.readouterr().err


def test_show_prints_json(tmp_path, capsys):
    store = str(tmp_path)
    save_baseline(store, ENDPOINT, SNAP)
    args = _make_args(store, "show")
    rc = cmd_baseline(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == 200


def test_show_no_baseline_prints_message(tmp_path, capsys):
    args = _make_args(str(tmp_path), "show")
    rc = cmd_baseline(args)
    assert rc == 0
    assert "No baseline" in capsys.readouterr().out


def test_clear_removes_and_confirms(tmp_path, capsys):
    store = str(tmp_path)
    save_baseline(store, ENDPOINT, SNAP)
    args = _make_args(store, "clear")
    rc = cmd_baseline(args)
    assert rc == 0
    assert "cleared" in capsys.readouterr().out


def test_clear_missing_reports_not_found(tmp_path, capsys):
    args = _make_args(str(tmp_path), "clear")
    cmd_baseline(args)
    assert "No baseline" in capsys.readouterr().out


def test_register_adds_baseline_subcommand():
    p = ArgumentParser()
    sub = p.add_subparsers()
    register_baseline_subcommand(sub)
    args = p.parse_args(["baseline", ENDPOINT, "show", "--store-dir", ".reqwatch"])
    assert args.baseline_action == "show"
    assert args.endpoint_key == ENDPOINT
