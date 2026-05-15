"""Tests for reqwatch.cli_watchdog."""
from __future__ import annotations

import argparse
import json
import sys
import pytest

from reqwatch.cli_watchdog import cmd_watchdog, register_watchdog_subcommand
from reqwatch.storage import save_snapshot

NOW = 1_700_000_000.0


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(store, endpoint, ts):
    save_snapshot(store, endpoint, {
        "endpoint": endpoint,
        "timestamp": ts,
        "status": 200,
        "body": {},
        "headers": {},
        "error": None,
    })


def _make_args(store, endpoints, threshold=3600.0, summarize=False):
    ns = argparse.Namespace(
        store=store,
        endpoints=endpoints,
        threshold=threshold,
        summarize=summarize,
    )
    return ns


def test_cmd_watchdog_prints_json(store, capsys):
    _snap(store, "api", NOW - 10)
    args = _make_args(store, ["api"], threshold=3600.0)
    cmd_watchdog(args)  # exit code 0 — no stale
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["total"] == 1
    assert data["stale_count"] == 0


def test_cmd_watchdog_exits_2_when_stale(store):
    _snap(store, "api", NOW - 9999)
    args = _make_args(store, ["api"], threshold=60.0)
    with pytest.raises(SystemExit) as exc:
        cmd_watchdog(args)
    assert exc.value.code == 2


def test_cmd_watchdog_summarize(store, capsys):
    _snap(store, "api", NOW - 10)
    args = _make_args(store, ["api"], threshold=3600.0, summarize=True)
    cmd_watchdog(args)
    out = capsys.readouterr().out
    assert "Checked" in out
    assert "ok" in out


def test_cmd_watchdog_no_endpoints_exits(store):
    args = _make_args(store, [])
    with pytest.raises(SystemExit) as exc:
        cmd_watchdog(args)
    assert exc.value.code == 1


def test_register_adds_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_watchdog_subcommand(sub)
    parsed = parser.parse_args(["watchdog", "my-endpoint", "--threshold", "120"])
    assert parsed.endpoints == ["my-endpoint"]
    assert parsed.threshold == 120.0
    assert parsed.summarize is False


def test_silent_endpoint_exits_2(store):
    # no snapshots saved — endpoint is silent
    args = _make_args(store, ["ghost"], threshold=60.0)
    with pytest.raises(SystemExit) as exc:
        cmd_watchdog(args)
    assert exc.value.code == 2
