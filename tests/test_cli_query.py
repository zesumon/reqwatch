"""Tests for reqwatch.cli_query."""

import argparse
import json
import pytest
from unittest.mock import patch

from reqwatch.cli_query import cmd_query, register_query_subcommand
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _make_args(store, endpoint, **kwargs):
    defaults = {
        "store": store,
        "endpoint": endpoint,
        "limit": None,
        "since": None,
        "until": None,
        "status_code": None,
        "has_error": None,
        "summarize": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _seed(store, endpoint, ts, status=200):
    snap = {"timestamp": ts, "status_code": status, "body": {}}
    save_snapshot(store, endpoint, ts, snap)
    return snap


def test_cmd_query_prints_json(store, capsys):
    _seed(store, "api", "2024-01-01T00:00:00")
    cmd_query(_make_args(store, "api"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 1


def test_cmd_query_summarize(store, capsys):
    _seed(store, "api", "2024-01-01T00:00:00")
    _seed(store, "api", "2024-01-02T00:00:00")
    cmd_query(_make_args(store, "api", summarize=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["count"] == 2


def test_cmd_query_no_results_prints_to_stderr(store, capsys):
    cmd_query(_make_args(store, "missing"))
    err = capsys.readouterr().err
    assert "No snapshots" in err


def test_cmd_query_limit(store, capsys):
    for i in range(1, 5):
        _seed(store, "api", f"2024-01-0{i}T00:00:00")
    cmd_query(_make_args(store, "api", limit=2))
    data = json.loads(capsys.readouterr().out)
    assert len(data) == 2


def test_register_query_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_query_subcommand(sub)
    args = parser.parse_args(["query", "myapi", "--limit", "5"])
    assert args.endpoint == "myapi"
    assert args.limit == 5
    assert args.func is cmd_query
