"""Tests for reqwatch.snapshot_rate_limit."""

from __future__ import annotations

import time
import pytest

from reqwatch.snapshot_rate_limit import (
    RateLimitError,
    clear_rate_limit,
    get_rate_limit,
    is_allowed,
    record_fetch,
    set_rate_limit,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def test_is_allowed_when_no_config(store):
    assert is_allowed(store, "https://api.example.com/v1") is True


def test_set_rate_limit_persists(store):
    set_rate_limit(store, "https://api.example.com/v1", 30.0)
    entry = get_rate_limit(store, "https://api.example.com/v1")
    assert entry is not None
    assert entry["min_interval"] == 30.0


def test_set_rate_limit_zero_raises(store):
    with pytest.raises(RateLimitError, match="positive"):
        set_rate_limit(store, "https://api.example.com/v1", 0)


def test_set_rate_limit_negative_raises(store):
    with pytest.raises(RateLimitError):
        set_rate_limit(store, "https://api.example.com/v1", -5.0)


def test_record_fetch_stores_timestamp(store):
    endpoint = "https://api.example.com/v1"
    before = time.time()
    record_fetch(store, endpoint)
    after = time.time()
    entry = get_rate_limit(store, endpoint)
    assert entry is not None
    assert before <= entry["last_fetch"] <= after


def test_is_allowed_false_immediately_after_fetch(store):
    endpoint = "https://api.example.com/v1"
    set_rate_limit(store, endpoint, 60.0)
    record_fetch(store, endpoint)
    assert is_allowed(store, endpoint) is False


def test_is_allowed_true_after_interval_elapsed(store, monkeypatch):
    endpoint = "https://api.example.com/v1"
    set_rate_limit(store, endpoint, 10.0)
    record_fetch(store, endpoint)
    # Advance time beyond the interval
    future = time.time() + 11.0
    monkeypatch.setattr("reqwatch.snapshot_rate_limit.time.time", lambda: future)
    assert is_allowed(store, endpoint) is True


def test_get_rate_limit_missing_returns_none(store):
    assert get_rate_limit(store, "https://missing.example.com") is None


def test_clear_rate_limit_returns_true_when_exists(store):
    endpoint = "https://api.example.com/v1"
    set_rate_limit(store, endpoint, 15.0)
    assert clear_rate_limit(store, endpoint) is True
    assert get_rate_limit(store, endpoint) is None


def test_clear_rate_limit_returns_false_when_missing(store):
    assert clear_rate_limit(store, "https://never-set.example.com") is False


def test_multiple_endpoints_tracked_independently(store):
    ep1 = "https://api.example.com/v1"
    ep2 = "https://api.example.com/v2"
    set_rate_limit(store, ep1, 5.0)
    set_rate_limit(store, ep2, 120.0)
    record_fetch(store, ep1)
    assert is_allowed(store, ep1) is False
    assert is_allowed(store, ep2) is True


def test_record_fetch_without_set_still_stores(store):
    endpoint = "https://api.example.com/bare"
    record_fetch(store, endpoint)
    entry = get_rate_limit(store, endpoint)
    assert entry is not None
    assert "last_fetch" in entry
    # No min_interval means is_allowed returns True
    assert is_allowed(store, endpoint) is True
