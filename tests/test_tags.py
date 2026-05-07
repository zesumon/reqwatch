"""Tests for reqwatch/tags.py and reqwatch/cli_tags.py."""

from __future__ import annotations

import argparse
import pytest

from reqwatch.tags import (
    TagError,
    add_tag,
    clear_tags,
    find_by_tag,
    get_tags,
    remove_tag,
)
from reqwatch.cli_tags import cmd_tags


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


SNAP = "endpoint_abc_20240101T120000"


def test_add_and_get_tag(store):
    add_tag(store, SNAP, "stable")
    assert "stable" in get_tags(store, SNAP)


def test_add_duplicate_tag_is_noop(store):
    add_tag(store, SNAP, "stable")
    add_tag(store, SNAP, "stable")
    assert get_tags(store, SNAP).count("stable") == 1


def test_add_empty_tag_raises(store):
    with pytest.raises(TagError, match="non-empty"):
        add_tag(store, SNAP, "   ")


def test_remove_tag(store):
    add_tag(store, SNAP, "v1")
    remove_tag(store, SNAP, "v1")
    assert "v1" not in get_tags(store, SNAP)


def test_remove_missing_tag_is_noop(store):
    remove_tag(store, SNAP, "nonexistent")  # should not raise


def test_get_tags_empty_for_unknown_snapshot(store):
    assert get_tags(store, "unknown_snap") == []


def test_find_by_tag_returns_correct_ids(store):
    add_tag(store, "snap_a", "prod")
    add_tag(store, "snap_b", "prod")
    add_tag(store, "snap_c", "staging")
    result = find_by_tag(store, "prod")
    assert "snap_a" in result
    assert "snap_b" in result
    assert "snap_c" not in result


def test_find_by_tag_no_matches(store):
    assert find_by_tag(store, "missing") == []


def test_clear_tags(store):
    add_tag(store, SNAP, "a")
    add_tag(store, SNAP, "b")
    clear_tags(store, SNAP)
    assert get_tags(store, SNAP) == []


def test_clear_tags_unknown_snapshot_is_noop(store):
    clear_tags(store, "ghost")  # should not raise


def _args(store, action, snapshot_id=None, tag=None):
    ns = argparse.Namespace(store=store, tag_action=action)
    if snapshot_id is not None:
        ns.snapshot_id = snapshot_id
    if tag is not None:
        ns.tag = tag
    return ns


def test_cmd_add_prints_confirmation(store, capsys):
    cmd_tags(_args(store, "add", SNAP, "release"))
    out = capsys.readouterr().out
    assert "release" in out


def test_cmd_list_prints_tags(store, capsys):
    add_tag(store, SNAP, "mytag")
    cmd_tags(_args(store, "list", SNAP))
    out = capsys.readouterr().out
    assert "mytag" in out


def test_cmd_find_prints_snapshot_id(store, capsys):
    add_tag(store, SNAP, "search_me")
    cmd_tags(_args(store, "find", tag="search_me"))
    out = capsys.readouterr().out
    assert SNAP in out


def test_cmd_add_empty_tag_exits(store):
    with pytest.raises(SystemExit):
        cmd_tags(_args(store, "add", SNAP, ""))
