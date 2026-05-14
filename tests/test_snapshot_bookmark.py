"""Tests for reqwatch.snapshot_bookmark."""

import pytest

from reqwatch.snapshot_bookmark import (
    BookmarkError,
    delete_bookmark,
    get_bookmark,
    list_bookmarks,
    resolve_bookmark,
    set_bookmark,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def test_set_and_get_bookmark(store):
    set_bookmark(store, "stable", "snap-001")
    assert get_bookmark(store, "stable") == "snap-001"


def test_get_missing_returns_none(store):
    assert get_bookmark(store, "nonexistent") is None


def test_set_overwrites_existing(store):
    set_bookmark(store, "latest", "snap-001")
    set_bookmark(store, "latest", "snap-002")
    assert get_bookmark(store, "latest") == "snap-002"


def test_delete_existing_returns_true(store):
    set_bookmark(store, "v1", "snap-010")
    assert delete_bookmark(store, "v1") is True
    assert get_bookmark(store, "v1") is None


def test_delete_missing_returns_false(store):
    assert delete_bookmark(store, "ghost") is False


def test_list_bookmarks_empty(store):
    assert list_bookmarks(store) == {}


def test_list_bookmarks_multiple(store):
    set_bookmark(store, "a", "snap-1")
    set_bookmark(store, "b", "snap-2")
    result = list_bookmarks(store)
    assert result == {"a": "snap-1", "b": "snap-2"}


def test_resolve_bookmark_returns_id(store):
    set_bookmark(store, "prod", "snap-999")
    assert resolve_bookmark(store, "prod") == "snap-999"


def test_resolve_missing_raises(store):
    with pytest.raises(BookmarkError, match="No bookmark named 'missing'"):
        resolve_bookmark(store, "missing")


def test_set_empty_name_raises(store):
    with pytest.raises(BookmarkError):
        set_bookmark(store, "", "snap-001")


def test_set_empty_snapshot_id_raises(store):
    with pytest.raises(BookmarkError):
        set_bookmark(store, "valid-name", "")


def test_bookmarks_persist_across_calls(store):
    set_bookmark(store, "x", "snap-x")
    # Simulate a fresh call by not caching anything in memory
    assert list_bookmarks(store)["x"] == "snap-x"
