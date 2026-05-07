"""Tests for reqwatch.cli_search."""

from __future__ import annotations

import argparse
import json
import time
from io import StringIO
from unittest.mock import patch

import pytest

from reqwatch.cli_search import cmd_search, register_search_subcommand
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(endpoint, body, status_code=200, error=None):
    return {
        "endpoint": endpoint,
        "timestamp": str(time.time()),
        "status_code": status_code,
        "headers": {},
        "body": body,
        "error": error,
    }


def _make_args(**kwargs):
    defaults = {
        "endpoint": "ep",
        "text": None,
        "status": None,
        "has_error": None,
        "limit": 50,
        "func": cmd_search,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_search_prints_json(store, capsys):
    save_snapshot(store, "ep", _snap("ep", {"hello": "world"}))
    with patch("reqwatch.cli_search.search_snapshots",
               wraps=lambda sd, ep, **kw: __import__(
                   "reqwatch.snapshot_search", fromlist=["search_snapshots"]
               ).search_snapshots(sd, ep, **kw)):
        cmd_search(_make_args(), store_dir=store)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["body"] == {"hello": "world"}


def test_cmd_search_no_results_prints_message(store, capsys):
    cmd_search(_make_args(), store_dir=store)
    captured = capsys.readouterr()
    assert "No matching snapshots" in captured.out


def test_cmd_search_invalid_limit_exits(store):
    with pytest.raises(SystemExit):
        cmd_search(_make_args(limit=0), store_dir=store)


def test_register_search_subcommand_adds_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_search_subcommand(sub)
    args = parser.parse_args(["search", "my_ep", "--text", "foo", "--limit", "5"])
    assert args.endpoint == "my_ep"
    assert args.text == "foo"
    assert args.limit == 5


def test_register_search_errors_only_flag():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_search_subcommand(sub)
    args = parser.parse_args(["search", "ep", "--errors-only"])
    assert args.has_error is True


def test_register_search_no_errors_flag():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_search_subcommand(sub)
    args = parser.parse_args(["search", "ep", "--no-errors"])
    assert args.has_error is False
