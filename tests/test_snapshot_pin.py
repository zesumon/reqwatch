"""Tests for snapshot_pin and cli_pin."""

from __future__ import annotations

import argparse
import pytest

from reqwatch.storage import save_snapshot
from reqwatch.snapshot_pin import (
    PinError,
    is_pinned,
    list_pinned,
    pin_snapshot,
    unpin_snapshot,
)
from reqwatch.cli_pin import cmd_pin


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(store, endpoint, ts):
    snap = {"timestamp": ts, "status": 200, "body": {"v": 1}, "error": None}
    save_snapshot(store, endpoint, snap)
    return snap


def test_pin_and_is_pinned(store):
    _snap(store, "api", "2024-01-01T00:00:00")
    pin_snapshot(store, "api", "2024-01-01T00:00:00")
    assert is_pinned(store, "api", "2024-01-01T00:00:00") is True


def test_is_not_pinned_by_default(store):
    _snap(store, "api", "2024-01-01T00:00:00")
    assert is_pinned(store, "api", "2024-01-01T00:00:00") is False


def test_pin_nonexistent_snapshot_raises(store):
    with pytest.raises(PinError, match="snapshot not found"):
        pin_snapshot(store, "api", "ghost-ts")


def test_pin_empty_timestamp_raises(store):
    with pytest.raises(PinError, match="timestamp must not be empty"):
        pin_snapshot(store, "api", "")


def test_list_pinned_returns_all(store):
    _snap(store, "api", "2024-01-01T00:00:00")
    _snap(store, "api", "2024-01-02T00:00:00")
    pin_snapshot(store, "api", "2024-01-01T00:00:00")
    pin_snapshot(store, "api", "2024-01-02T00:00:00")
    pins = list_pinned(store, "api")
    assert "2024-01-01T00:00:00" in pins
    assert "2024-01-02T00:00:00" in pins


def test_list_pinned_empty(store):
    assert list_pinned(store, "api") == []


def test_unpin_removes_pin(store):
    _snap(store, "api", "2024-01-01T00:00:00")
    pin_snapshot(store, "api", "2024-01-01T00:00:00")
    unpin_snapshot(store, "api", "2024-01-01T00:00:00")
    assert is_pinned(store, "api", "2024-01-01T00:00:00") is False


def test_unpin_not_pinned_raises(store):
    _snap(store, "api", "2024-01-01T00:00:00")
    with pytest.raises(PinError, match="not pinned"):
        unpin_snapshot(store, "api", "2024-01-01T00:00:00")


def _make_args(store, endpoint, action, timestamp=None):
    ns = argparse.Namespace(store=store, endpoint=endpoint, pin_action=action)
    if timestamp is not None:
        ns.timestamp = timestamp
    return ns


def test_cmd_pin_add(store, capsys):
    _snap(store, "svc", "2024-03-01T00:00:00")
    cmd_pin(_make_args(store, "svc", "add", "2024-03-01T00:00:00"))
    out = capsys.readouterr().out
    assert "Pinned" in out


def test_cmd_pin_list(store, capsys):
    _snap(store, "svc", "2024-03-01T00:00:00")
    pin_snapshot(store, "svc", "2024-03-01T00:00:00")
    cmd_pin(_make_args(store, "svc", "list"))
    out = capsys.readouterr().out
    assert "2024-03-01T00:00:00" in out


def test_cmd_pin_check_pinned(store, capsys):
    _snap(store, "svc", "2024-03-01T00:00:00")
    pin_snapshot(store, "svc", "2024-03-01T00:00:00")
    cmd_pin(_make_args(store, "svc", "check", "2024-03-01T00:00:00"))
    assert "pinned" in capsys.readouterr().out


def test_cmd_pin_remove(store, capsys):
    _snap(store, "svc", "2024-03-01T00:00:00")
    pin_snapshot(store, "svc", "2024-03-01T00:00:00")
    cmd_pin(_make_args(store, "svc", "remove", "2024-03-01T00:00:00"))
    assert "Unpinned" in capsys.readouterr().out
