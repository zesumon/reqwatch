"""Unit tests for reqwatch.snapshot_label."""

from __future__ import annotations

import pytest

from reqwatch.snapshot_label import (
    LabelError,
    add_label,
    clear_labels,
    find_by_label,
    get_labels,
    remove_label,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


SNAP = "snap-001"


def test_add_and_get_label(store):
    add_label(store, SNAP, "production")
    assert "production" in get_labels(store, SNAP)


def test_add_duplicate_is_noop(store):
    add_label(store, SNAP, "stable")
    add_label(store, SNAP, "stable")
    assert get_labels(store, SNAP).count("stable") == 1


def test_add_empty_label_raises(store):
    with pytest.raises(LabelError):
        add_label(store, SNAP, "")


def test_add_whitespace_label_raises(store):
    with pytest.raises(LabelError):
        add_label(store, SNAP, "   ")


def test_remove_existing_label(store):
    add_label(store, SNAP, "beta")
    result = remove_label(store, SNAP, "beta")
    assert result is True
    assert "beta" not in get_labels(store, SNAP)


def test_remove_missing_label_returns_false(store):
    result = remove_label(store, SNAP, "nonexistent")
    assert result is False


def test_remove_last_label_cleans_entry(store):
    add_label(store, SNAP, "only")
    remove_label(store, SNAP, "only")
    assert get_labels(store, SNAP) == []


def test_get_labels_missing_snapshot_returns_empty(store):
    assert get_labels(store, "no-such-snap") == []


def test_find_by_label_returns_matching_ids(store):
    add_label(store, "snap-a", "v2")
    add_label(store, "snap-b", "v2")
    add_label(store, "snap-c", "v1")
    ids = find_by_label(store, "v2")
    assert set(ids) == {"snap-a", "snap-b"}


def test_find_by_label_no_match_returns_empty(store):
    assert find_by_label(store, "ghost") == []


def test_clear_labels_removes_all(store):
    add_label(store, SNAP, "x")
    add_label(store, SNAP, "y")
    clear_labels(store, SNAP)
    assert get_labels(store, SNAP) == []


def test_clear_labels_missing_snapshot_is_noop(store):
    clear_labels(store, "phantom")  # should not raise


def test_labels_persist_across_calls(store):
    add_label(store, SNAP, "persist")
    # re-read without caching
    assert "persist" in get_labels(store, SNAP)
