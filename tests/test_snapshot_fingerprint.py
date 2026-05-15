"""Tests for reqwatch.snapshot_fingerprint."""

import time
import pytest

from reqwatch.storage import save_snapshot
from reqwatch.snapshot_fingerprint import (
    FingerprintError,
    compute_fingerprint,
    get_latest_fingerprint,
    fingerprint_history,
    detect_schema_changes,
)


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(body, status=200, ts=None):
    return {
        "url": "https://example.com/api",
        "status": status,
        "body": body,
        "headers": {},
        "timestamp": ts or time.time(),
        "error": None,
    }


def _seed(store, endpoint, bodies):
    ids = []
    for i, body in enumerate(bodies):
        snap = _snap(body, ts=1_000_000.0 + i)
        sid = save_snapshot(store, endpoint, snap)
        ids.append(sid)
    return ids


# --- compute_fingerprint ---

def test_fingerprint_is_16_hex_chars():
    snap = _snap({"a": 1, "b": "hello"})
    fp = compute_fingerprint(snap)
    assert len(fp) == 16
    assert all(c in "0123456789abcdef" for c in fp)


def test_fingerprint_same_schema_different_values():
    s1 = _snap({"count": 1, "name": "alice"})
    s2 = _snap({"count": 99, "name": "bob"})
    assert compute_fingerprint(s1) == compute_fingerprint(s2)


def test_fingerprint_differs_on_schema_change():
    s1 = _snap({"count": 1})
    s2 = _snap({"count": 1, "extra": True})
    assert compute_fingerprint(s1) != compute_fingerprint(s2)


def test_fingerprint_non_dict_body():
    s1 = _snap([1, 2, 3])
    s2 = _snap(["a", "b"])
    assert compute_fingerprint(s1) == compute_fingerprint(s2)


def test_fingerprint_none_body():
    s = _snap(None)
    fp = compute_fingerprint(s)
    assert isinstance(fp, str) and len(fp) == 16


# --- get_latest_fingerprint ---

def test_get_latest_fingerprint_returns_none_when_empty(store):
    assert get_latest_fingerprint(store, "ep") is None


def test_get_latest_fingerprint_returns_string(store):
    _seed(store, "ep", [{"x": 1}])
    fp = get_latest_fingerprint(store, "ep")
    assert fp is not None and len(fp) == 16


# --- fingerprint_history ---

def test_fingerprint_history_raises_when_no_snapshots(store):
    with pytest.raises(FingerprintError):
        fingerprint_history(store, "missing")


def test_fingerprint_history_length_matches_snapshots(store):
    _seed(store, "ep", [{"a": 1}, {"a": 2}, {"a": 3}])
    history = fingerprint_history(store, "ep")
    assert len(history) == 3
    assert all("snapshot_id" in h and "fingerprint" in h for h in history)


# --- detect_schema_changes ---

def test_detect_no_schema_changes(store):
    _seed(store, "ep", [{"a": 1}, {"a": 99}, {"a": 7}])
    changes = detect_schema_changes(store, "ep")
    assert changes == []


def test_detect_schema_change_event(store):
    _seed(store, "ep", [{"a": 1}, {"a": 2, "b": "new"}])
    changes = detect_schema_changes(store, "ep")
    assert len(changes) == 1
    c = changes[0]
    assert "from_snapshot" in c and "to_snapshot" in c
    assert c["from_fingerprint"] != c["to_fingerprint"]


def test_detect_multiple_schema_changes(store):
    bodies = [{"x": 1}, {"x": 1, "y": 2}, {"z": True}]
    _seed(store, "ep", bodies)
    changes = detect_schema_changes(store, "ep")
    assert len(changes) == 2
