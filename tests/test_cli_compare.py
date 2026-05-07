"""Tests for reqwatch.cli_compare."""

import argparse
import json
import pytest

from reqwatch.cli_compare import cmd_compare, register_compare_subcommand
from reqwatch.storage import save_snapshot


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _make_args(store, endpoint, a="-2", b="-1", as_json=False):
    ns = argparse.Namespace(
        store=store,
        endpoint=endpoint,
        a=a,
        b=b,
        json=as_json,
    )
    return ns


def _snap(body, ts):
    return {"timestamp": ts, "status": 200, "body": body, "error": None}


def test_cmd_compare_text_no_change(store, capsys):
    save_snapshot(store, "http://api/x", _snap({"k": 1}, "2024-01-01T00:00:00"))
    save_snapshot(store, "http://api/x", _snap({"k": 1}, "2024-01-01T00:01:00"))

    cmd_compare(_make_args(store, "http://api/x"))

    out = capsys.readouterr().out
    assert "no changes" in out
    assert "identical" in out


def test_cmd_compare_text_with_change(store, capsys):
    save_snapshot(store, "http://api/x", _snap({"k": 1}, "2024-01-01T00:00:00"))
    save_snapshot(store, "http://api/x", _snap({"k": 2}, "2024-01-01T00:01:00"))

    cmd_compare(_make_args(store, "http://api/x"))

    out = capsys.readouterr().out
    assert "CHANGED" in out


def test_cmd_compare_json_output(store, capsys):
    save_snapshot(store, "http://api/x", _snap({"k": 1}, "2024-01-01T00:00:00"))
    save_snapshot(store, "http://api/x", _snap({"k": 2}, "2024-01-01T00:01:00"))

    cmd_compare(_make_args(store, "http://api/x", as_json=True))

    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["changed"] is True
    assert "diff" in data


def test_cmd_compare_missing_endpoint_exits(store):
    with pytest.raises(SystemExit) as exc_info:
        cmd_compare(_make_args(store, "http://missing/"))
    assert exc_info.value.code == 1


def test_register_compare_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_compare_subcommand(sub)
    args = parser.parse_args(["compare", "http://api/x", "--json"])
    assert args.endpoint == "http://api/x"
    assert args.json is True
    assert args.a == "-2"
    assert args.b == "-1"
