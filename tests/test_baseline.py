"""Tests for reqwatch.baseline."""

from __future__ import annotations

import json
import pytest

from reqwatch.baseline import (
    BaselineError,
    baseline_exists,
    clear_baseline,
    load_baseline,
    save_baseline,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def snap():
    return {
        "url": "https://api.example.com/v1/items",
        "status": 200,
        "body": {"items": [1, 2, 3]},
        "timestamp": "2024-01-01T00:00:00",
    }


def test_save_and_load_roundtrip(store, snap):
    key = "https://api.example.com/v1/items"
    save_baseline(store, key, snap)
    loaded = load_baseline(store, key)
    assert loaded == snap


def test_load_missing_returns_none(store):
    assert load_baseline(store, "https://missing.example.com") is None


def test_baseline_exists_true_after_save(store, snap):
    key = "https://api.example.com/v1/items"
    assert not baseline_exists(store, key)
    save_baseline(store, key, snap)
    assert baseline_exists(store, key)


def test_clear_removes_baseline(store, snap):
    key = "https://api.example.com/v1/items"
    save_baseline(store, key, snap)
    removed = clear_baseline(store, key)
    assert removed is True
    assert not baseline_exists(store, key)


def test_clear_nonexistent_returns_false(store):
    removed = clear_baseline(store, "https://nope.example.com")
    assert removed is False


def test_save_creates_parent_dirs(store, snap):
    key = "https://api.example.com/v2/deeply/nested"
    path = save_baseline(store, key, snap)
    assert path.exists()


def test_saved_file_is_valid_json(store, snap):
    key = "https://api.example.com/v1/items"
    path = save_baseline(store, key, snap)
    data = json.loads(path.read_text())
    assert data["status"] == 200


def test_load_corrupt_file_raises_baseline_error(store):
    key = "https://api.example.com/corrupt"
    path = save_baseline(store, key, {"ok": True})
    path.write_text("NOT JSON", encoding="utf-8")
    with pytest.raises(BaselineError):
        load_baseline(store, key)


def test_multiple_keys_are_isolated(store, snap):
    key_a = "https://api.example.com/a"
    key_b = "https://api.example.com/b"
    snap_b = {**snap, "body": {"items": [9, 8, 7]}}
    save_baseline(store, key_a, snap)
    save_baseline(store, key_b, snap_b)
    assert load_baseline(store, key_a)["body"] == {"items": [1, 2, 3]}
    assert load_baseline(store, key_b)["body"] == {"items": [9, 8, 7]}
