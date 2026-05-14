"""Tests for reqwatch.cli_label cmd_label."""

from __future__ import annotations

import argparse
import json

import pytest

from reqwatch.cli_label import cmd_label
from reqwatch.snapshot_label import add_label


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _make_args(store, action, snapshot_id=None, label=None):
    ns = argparse.Namespace(
        store=store,
        label_action=action,
        snapshot_id=snapshot_id,
        label=label,
    )
    return ns


def test_cmd_label_add(store, capsys):
    cmd_label(_make_args(store, "add", "snap-1", "prod"))
    out = capsys.readouterr().out
    assert "prod" in out
    assert "snap-1" in out


def test_cmd_label_list_prints_json(store, capsys):
    add_label(store, "snap-1", "alpha")
    add_label(store, "snap-1", "beta")
    cmd_label(_make_args(store, "list", "snap-1"))
    out = capsys.readouterr().out
    labels = json.loads(out)
    assert "alpha" in labels
    assert "beta" in labels


def test_cmd_label_list_empty(store, capsys):
    cmd_label(_make_args(store, "list", "snap-nobody"))
    out = capsys.readouterr().out
    assert "No labels" in out


def test_cmd_label_remove_existing(store, capsys):
    add_label(store, "snap-1", "old")
    cmd_label(_make_args(store, "remove", "snap-1", "old"))
    out = capsys.readouterr().out
    assert "removed" in out


def test_cmd_label_remove_missing(store, capsys):
    cmd_label(_make_args(store, "remove", "snap-1", "ghost"))
    out = capsys.readouterr().out
    assert "not found" in out


def test_cmd_label_find_prints_ids(store, capsys):
    add_label(store, "snap-a", "release")
    add_label(store, "snap-b", "release")
    cmd_label(_make_args(store, "find", label="release"))
    out = capsys.readouterr().out
    ids = json.loads(out)
    assert set(ids) == {"snap-a", "snap-b"}


def test_cmd_label_find_no_match(store, capsys):
    cmd_label(_make_args(store, "find", label="nowhere"))
    out = capsys.readouterr().out
    assert "No snapshots" in out


def test_cmd_label_clear(store, capsys):
    add_label(store, "snap-1", "temp")
    cmd_label(_make_args(store, "clear", "snap-1"))
    out = capsys.readouterr().out
    assert "cleared" in out


def test_cmd_label_add_empty_label_exits(store):
    with pytest.raises(SystemExit):
        cmd_label(_make_args(store, "add", "snap-1", ""))
