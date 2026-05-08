"""Tests for reqwatch.snapshot_diff_history."""

import pytest

from reqwatch.storage import save_snapshot
from reqwatch.snapshot_diff_history import (
    build_diff_history,
    summarize_diff_history,
    DiffHistoryError,
)


ENDPOINT = "https://api.example.com/v1/data"


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(store, endpoint, ts, body):
    snapshot = {
        "endpoint": endpoint,
        "timestamp": ts,
        "status": 200,
        "body": body,
        "headers": {},
        "error": None,
    }
    save_snapshot(store, endpoint, snapshot)
    return snapshot


def test_no_snapshots_raises(store):
    with pytest.raises(DiffHistoryError, match="No snapshots found"):
        build_diff_history(store, ENDPOINT)


def test_single_snapshot_produces_one_entry(store):
    _snap(store, ENDPOINT, "2024-01-01T00:00:00", {"v": 1})
    entries = build_diff_history(store, ENDPOINT)
    assert len(entries) == 1
    assert entries[0].changed is False
    assert entries[0].from_timestamp is None


def test_two_identical_snapshots_no_change(store):
    _snap(store, ENDPOINT, "2024-01-01T00:00:00", {"v": 1})
    _snap(store, ENDPOINT, "2024-01-02T00:00:00", {"v": 1})
    entries = build_diff_history(store, ENDPOINT)
    assert len(entries) == 2
    assert entries[1].changed is False
    assert entries[1].diff_lines == []


def test_two_different_snapshots_detects_change(store):
    _snap(store, ENDPOINT, "2024-01-01T00:00:00", {"v": 1})
    _snap(store, ENDPOINT, "2024-01-02T00:00:00", {"v": 2})
    entries = build_diff_history(store, ENDPOINT)
    assert len(entries) == 2
    assert entries[1].changed is True
    assert len(entries[1].diff_lines) > 0


def test_multiple_snapshots_mixed_changes(store):
    _snap(store, ENDPOINT, "2024-01-01T00:00:00", {"v": 1})
    _snap(store, ENDPOINT, "2024-01-02T00:00:00", {"v": 1})
    _snap(store, ENDPOINT, "2024-01-03T00:00:00", {"v": 2})
    _snap(store, ENDPOINT, "2024-01-04T00:00:00", {"v": 2})
    entries = build_diff_history(store, ENDPOINT)
    assert len(entries) == 4
    changed = [e.changed for e in entries]
    assert changed == [False, False, True, False]


def test_entries_ordered_oldest_to_newest(store):
    _snap(store, ENDPOINT, "2024-01-01T00:00:00", {"v": 1})
    _snap(store, ENDPOINT, "2024-01-02T00:00:00", {"v": 2})
    _snap(store, ENDPOINT, "2024-01-03T00:00:00", {"v": 3})
    entries = build_diff_history(store, ENDPOINT)
    timestamps = [e.to_timestamp for e in entries]
    assert timestamps == sorted(timestamps)


def test_summarize_diff_history_counts(store):
    _snap(store, ENDPOINT, "2024-01-01T00:00:00", {"v": 1})
    _snap(store, ENDPOINT, "2024-01-02T00:00:00", {"v": 2})
    _snap(store, ENDPOINT, "2024-01-03T00:00:00", {"v": 2})
    entries = build_diff_history(store, ENDPOINT)
    summary = summarize_diff_history(entries)
    assert summary["total_snapshots"] == 3
    assert summary["total_changes"] == 1
    assert summary["change_rate"] == pytest.approx(1 / 3, rel=1e-3)


def test_summarize_empty_entries():
    summary = summarize_diff_history([])
    assert summary["total_snapshots"] == 0
    assert summary["change_rate"] == 0.0
    assert summary["first_timestamp"] is None
