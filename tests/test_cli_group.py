"""Tests for reqwatch.cli_group."""

from __future__ import annotations

import json
import types

import pytest

from reqwatch.cli_group import cmd_group
from reqwatch.snapshot_group import add_to_group
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _make_args(store, action, group=None, endpoint=None):
    ns = types.SimpleNamespace(
        store=store,
        group_action=action,
        group=group,
        endpoint=endpoint,
    )
    return ns


def _snap(endpoint):
    return {"endpoint": endpoint, "status": 200, "body": {}, "timestamp": "2024-01-01T00:00:00"}


def test_cmd_group_add(store, capsys):
    args = _make_args(store, "add", group="prod", endpoint="https://api.example.com")
    cmd_group(args)
    captured = capsys.readouterr()
    assert "prod" in captured.out
    assert "https://api.example.com" in captured.out


def test_cmd_group_list(store, capsys):
    add_to_group(store, "prod", "https://api.example.com")
    args = _make_args(store, "list")
    cmd_group(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "prod" in data


def test_cmd_group_list_empty(store, capsys):
    args = _make_args(store, "list")
    cmd_group(args)
    captured = capsys.readouterr()
    assert "No groups defined" in captured.out


def test_cmd_group_members(store, capsys):
    add_to_group(store, "prod", "https://api.example.com")
    args = _make_args(store, "members", group="prod")
    cmd_group(args)
    captured = capsys.readouterr()
    members = json.loads(captured.out)
    assert "https://api.example.com" in members


def test_cmd_group_members_missing_group_exits(store):
    args = _make_args(store, "members", group="ghost")
    with pytest.raises(SystemExit):
        cmd_group(args)


def test_cmd_group_remove(store, capsys):
    add_to_group(store, "prod", "https://api.example.com")
    args = _make_args(store, "remove", group="prod", endpoint="https://api.example.com")
    cmd_group(args)
    captured = capsys.readouterr()
    assert "Removed" in captured.out


def test_cmd_group_latest(store, capsys):
    endpoint = "https://api.example.com"
    save_snapshot(store, endpoint, _snap(endpoint))
    add_to_group(store, "prod", endpoint)
    args = _make_args(store, "latest", group="prod")
    cmd_group(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["endpoint"] == endpoint
