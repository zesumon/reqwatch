"""Tests for reqwatch.snapshot_watch_count."""

from __future__ import annotations

import pytest

from reqwatch.snapshot_watch_count import (
    WatchCountError,
    all_counts,
    get_count,
    increment,
    reset,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def test_initial_count_is_zero(store):
    assert get_count(store, "https://api.example.com") == 0


def test_increment_returns_new_count(store):
    ep = "https://api.example.com"
    assert increment(store, ep) == 1
    assert increment(store, ep) == 2
    assert increment(store, ep) == 3


def test_get_count_reflects_increments(store):
    ep = "https://api.example.com/users"
    increment(store, ep)
    increment(store, ep)
    assert get_count(store, ep) == 2


def test_multiple_endpoints_tracked_independently(store):
    ep1 = "https://api.example.com/a"
    ep2 = "https://api.example.com/b"
    increment(store, ep1)
    increment(store, ep1)
    increment(store, ep2)
    assert get_count(store, ep1) == 2
    assert get_count(store, ep2) == 1


def test_all_counts_returns_all(store):
    increment(store, "ep1")
    increment(store, "ep2")
    increment(store, "ep2")
    counts = all_counts(store)
    assert counts == {"ep1": 1, "ep2": 2}


def test_all_counts_empty_when_no_data(store):
    assert all_counts(store) == {}


def test_reset_removes_endpoint(store):
    ep = "https://api.example.com"
    increment(store, ep)
    reset(store, ep)
    assert get_count(store, ep) == 0


def test_reset_nonexistent_is_noop(store):
    # Should not raise
    reset(store, "https://api.example.com/never")


def test_increment_empty_endpoint_raises(store):
    with pytest.raises(WatchCountError):
        increment(store, "")


def test_get_empty_endpoint_raises(store):
    with pytest.raises(WatchCountError):
        get_count(store, "")


def test_reset_empty_endpoint_raises(store):
    with pytest.raises(WatchCountError):
        reset(store, "")


def test_counts_persist_across_calls(store):
    ep = "https://api.example.com/persist"
    for _ in range(5):
        increment(store, ep)
    # Reload by calling get_count fresh (reads from disk)
    assert get_count(store, ep) == 5


def test_all_counts_does_not_mutate_internal_state(store):
    increment(store, "ep")
    counts = all_counts(store)
    counts["ep"] = 999
    assert get_count(store, "ep") == 1
