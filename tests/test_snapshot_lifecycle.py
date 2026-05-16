"""Tests for reqwatch.snapshot_lifecycle."""

from __future__ import annotations

import pytest

from reqwatch.snapshot_lifecycle import (
    LifecycleError,
    delete_state,
    get_state,
    list_by_state,
    set_state,
    transition,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def test_set_and_get_state(store):
    set_state(store, "snap-1", "active")
    assert get_state(store, "snap-1") == "active"


def test_get_missing_returns_none(store):
    assert get_state(store, "nonexistent") is None


def test_set_invalid_state_raises(store):
    with pytest.raises(LifecycleError, match="Invalid state"):
        set_state(store, "snap-1", "limbo")


def test_set_empty_id_raises(store):
    with pytest.raises(LifecycleError, match="snapshot_id"):
        set_state(store, "", "active")


def test_set_overwrites_existing(store):
    set_state(store, "snap-1", "draft")
    set_state(store, "snap-1", "active")
    assert get_state(store, "snap-1") == "active"


def test_list_by_state_returns_matching(store):
    set_state(store, "snap-1", "active")
    set_state(store, "snap-2", "active")
    set_state(store, "snap-3", "deprecated")
    result = list_by_state(store, "active")
    assert set(result) == {"snap-1", "snap-2"}


def test_list_by_state_empty_when_none_match(store):
    set_state(store, "snap-1", "draft")
    assert list_by_state(store, "archived") == []


def test_list_by_state_invalid_raises(store):
    with pytest.raises(LifecycleError, match="Invalid state"):
        list_by_state(store, "unknown")


def test_delete_existing_returns_true(store):
    set_state(store, "snap-1", "active")
    assert delete_state(store, "snap-1") is True
    assert get_state(store, "snap-1") is None


def test_delete_missing_returns_false(store):
    assert delete_state(store, "ghost") is False


def test_delete_does_not_affect_others(store):
    set_state(store, "snap-1", "active")
    set_state(store, "snap-2", "draft")
    delete_state(store, "snap-1")
    assert get_state(store, "snap-2") == "draft"


def test_transition_succeeds_from_correct_state(store):
    set_state(store, "snap-1", "draft")
    result = transition(store, "snap-1", "draft", "active")
    assert result == "active"
    assert get_state(store, "snap-1") == "active"


def test_transition_fails_wrong_current_state(store):
    set_state(store, "snap-1", "active")
    with pytest.raises(LifecycleError, match="Expected state"):
        transition(store, "snap-1", "draft", "deprecated")


def test_transition_from_none_raises(store):
    with pytest.raises(LifecycleError, match="Expected state"):
        transition(store, "snap-99", "draft", "active")


def test_multiple_endpoints_isolated(store):
    set_state(store, "a", "active")
    set_state(store, "b", "archived")
    assert get_state(store, "a") == "active"
    assert get_state(store, "b") == "archived"
