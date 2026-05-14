"""Tests for reqwatch.cli_trend."""

from __future__ import annotations

import json
import argparse
import pytest

from reqwatch.cli_trend import cmd_trend, register_trend_subcommand


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(store, endpoint, ts, status=200, response_time=0.3):
    from reqwatch.storage import save_snapshot

    save_snapshot(
        store,
        endpoint,
        {
            "endpoint": endpoint,
            "timestamp": ts,
            "status": status,
            "body": {"ok": True},
            "response_time": response_time,
        },
    )


def _make_args(store, endpoint, limit=50, summarize=False):
    ns = argparse.Namespace()
    ns.store = store
    ns.endpoint = endpoint
    ns.limit = limit
    ns.summarize = summarize
    return ns


def test_cmd_trend_prints_json(store, capsys):
    _snap(store, "api/v1", "2024-01-01T00:00:00")
    cmd_trend(_make_args(store, "api/v1"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["endpoint"] == "api/v1"
    assert "points" in data
    assert "summary" in data


def test_cmd_trend_summarize_flag(store, capsys):
    _snap(store, "api/v1", "2024-01-01T00:00:00")
    cmd_trend(_make_args(store, "api/v1", summarize=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "points_analysed" in data
    assert "points" not in data


def test_cmd_trend_missing_endpoint_prints_error(store, capsys):
    cmd_trend(_make_args(store, "api/missing"))
    out = capsys.readouterr().out
    assert "error" in out


def test_cmd_trend_limit_applied(store, capsys):
    for i in range(10):
        _snap(store, "api/v1", f"2024-01-{i+1:02d}T00:00:00")
    cmd_trend(_make_args(store, "api/v1", limit=3))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data["points"]) == 3


def test_register_trend_subcommand():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    register_trend_subcommand(subs)
    args = parser.parse_args(["trend", "api/v1", "--limit", "10", "--summarize"])
    assert args.endpoint == "api/v1"
    assert args.limit == 10
    assert args.summarize is True
