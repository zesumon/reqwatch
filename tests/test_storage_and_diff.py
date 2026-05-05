"""Tests for the storage and diff modules."""

import json
import os
import tempfile

import pytest

from reqwatch.diff import diff_snapshots, format_diff, has_changes
from reqwatch.storage import list_snapshots, load_snapshot, save_snapshot


@pytest.fixture()
def tmp_store(tmp_path):
    return str(tmp_path / "snapshots")


def make_snapshot(status=200, body=None):
    return {"status_code": status, "headers": {"content-type": "application/json"}, "body": body or {}}


# --- storage tests ---

def test_save_and_load_roundtrip(tmp_store):
    data = make_snapshot(body={"users": [{"id": 1, "name": "Alice"}]})
    path = save_snapshot("users-list", data, storage_dir=tmp_store)
    assert path.exists()
    loaded = load_snapshot("users-list", storage_dir=tmp_store)
    assert loaded["status_code"] == 200
    assert loaded["body"] == data["body"]


def test_load_missing_returns_none(tmp_store):
    assert load_snapshot("nonexistent", storage_dir=tmp_store) is None


def test_list_snapshots(tmp_store):
    save_snapshot("ep-one", make_snapshot(), storage_dir=tmp_store)
    save_snapshot("ep-two", make_snapshot(), storage_dir=tmp_store)
    ids = list_snapshots(storage_dir=tmp_store)
    assert set(ids) == {"ep-one", "ep-two"}


def test_list_snapshots_empty_dir(tmp_store):
    assert list_snapshots(storage_dir=tmp_store) == []


# --- diff tests ---

def test_no_changes():
    snap = make_snapshot(body={"key": "value"})
    diff = diff_snapshots(snap, snap)
    assert not has_changes(diff)


def test_status_change_detected():
    old = make_snapshot(status=200)
    new = make_snapshot(status=404)
    diff = diff_snapshots(old, new)
    assert diff["status_changed"] == {"from": 200, "to": 404}
    assert has_changes(diff)


def test_body_field_added():
    old = make_snapshot(body={"a": 1})
    new = make_snapshot(body={"a": 1, "b": 2})
    diff = diff_snapshots(old, new)
    assert "b" in diff["added"]


def test_body_field_removed():
    old = make_snapshot(body={"a": 1, "b": 2})
    new = make_snapshot(body={"a": 1})
    diff = diff_snapshots(old, new)
    assert "b" in diff["removed"]


def test_body_field_changed():
    old = make_snapshot(body={"version": "1.0"})
    new = make_snapshot(body={"version": "2.0"})
    diff = diff_snapshots(old, new)
    assert diff["changed"]["version"] == {"from": "1.0", "to": "2.0"}


def test_format_diff_no_changes():
    snap = make_snapshot(body={"x": 1})
    diff = diff_snapshots(snap, snap)
    assert "no changes" in format_diff(diff)


def test_format_diff_with_changes():
    old = make_snapshot(status=200, body={"name": "foo", "extra": True})
    new = make_snapshot(status=500, body={"name": "bar", "new_field": 42})
    diff = diff_snapshots(old, new)
    output = format_diff(diff)
    assert "STATUS" in output
    assert "name" in output
    assert "extra" in output
    assert "new_field" in output
