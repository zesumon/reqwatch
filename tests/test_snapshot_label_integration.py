"""Integration-style tests: label operations across multiple snapshots."""

from __future__ import annotations

import pytest

from reqwatch.snapshot_label import (
    add_label,
    clear_labels,
    find_by_label,
    get_labels,
    remove_label,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def test_multi_snapshot_multi_label(store):
    snaps = ["s1", "s2", "s3"]
    for s in snaps:
        add_label(store, s, "group-a")
    add_label(store, "s1", "special")

    assert set(find_by_label(store, "group-a")) == set(snaps)
    assert find_by_label(store, "special") == ["s1"]


def test_remove_then_find_no_longer_appears(store):
    add_label(store, "s1", "transient")
    add_label(store, "s2", "transient")
    remove_label(store, "s1", "transient")
    ids = find_by_label(store, "transient")
    assert "s1" not in ids
    assert "s2" in ids


def test_clear_does_not_affect_other_snapshots(store):
    add_label(store, "s1", "shared")
    add_label(store, "s2", "shared")
    clear_labels(store, "s1")
    assert get_labels(store, "s1") == []
    assert "shared" in get_labels(store, "s2")


def test_label_order_preserved(store):
    for lbl in ["z", "a", "m"]:
        add_label(store, "s1", lbl)
    assert get_labels(store, "s1") == ["z", "a", "m"]


def test_labels_file_created_in_store_dir(store, tmp_path):
    add_label(store, "s1", "check")
    assert (tmp_path / "labels.json").exists()
