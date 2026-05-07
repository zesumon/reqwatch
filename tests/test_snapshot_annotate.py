"""Tests for reqwatch.snapshot_annotate."""

import pytest

from reqwatch.snapshot_annotate import (
    AnnotateError,
    delete_annotation,
    list_annotations,
    load_annotation,
    save_annotation,
)
from reqwatch.storage import save_snapshot

ENDPOINT = "https://api.example.com/data"


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def snap(store):
    """Save a minimal snapshot and return its ref."""
    snapshot = {
        "endpoint": ENDPOINT,
        "timestamp": "2024-01-01T00:00:00",
        "status": 200,
        "body": {"ok": True},
        "headers": {},
        "error": None,
    }
    save_snapshot(store, ENDPOINT, snapshot)
    from reqwatch.storage import list_snapshots
    refs = list_snapshots(store, ENDPOINT)
    return refs[0]


def test_save_and_load_roundtrip(store, snap):
    save_annotation(store, ENDPOINT, snap, "initial baseline captured")
    note = load_annotation(store, ENDPOINT, snap)
    assert note == "initial baseline captured"


def test_load_missing_returns_none(store, snap):
    result = load_annotation(store, ENDPOINT, snap)
    assert result is None


def test_save_empty_note_raises(store, snap):
    with pytest.raises(AnnotateError, match="empty"):
        save_annotation(store, ENDPOINT, snap, "   ")


def test_save_on_missing_snapshot_raises(store):
    with pytest.raises(AnnotateError, match="Snapshot not found"):
        save_annotation(store, ENDPOINT, "nonexistent-ref", "some note")


def test_delete_existing_annotation(store, snap):
    save_annotation(store, ENDPOINT, snap, "to be removed")
    removed = delete_annotation(store, ENDPOINT, snap)
    assert removed is True
    assert load_annotation(store, ENDPOINT, snap) is None


def test_delete_nonexistent_annotation_returns_false(store, snap):
    result = delete_annotation(store, ENDPOINT, snap)
    assert result is False


def test_list_annotations_empty(store):
    results = list_annotations(store, ENDPOINT)
    assert results == []


def test_list_annotations_returns_all(store, snap):
    # create a second snapshot
    from reqwatch.storage import save_snapshot, list_snapshots
    import time
    time.sleep(0.01)
    snapshot2 = {
        "endpoint": ENDPOINT,
        "timestamp": "2024-01-02T00:00:00",
        "status": 200,
        "body": {"ok": False},
        "headers": {},
        "error": None,
    }
    save_snapshot(store, ENDPOINT, snapshot2)
    refs = list_snapshots(store, ENDPOINT)
    assert len(refs) == 2

    save_annotation(store, ENDPOINT, refs[0], "note one")
    save_annotation(store, ENDPOINT, refs[1], "note two")

    annotations = list_annotations(store, ENDPOINT)
    assert len(annotations) == 2
    notes = {a["note"] for a in annotations}
    assert notes == {"note one", "note two"}
