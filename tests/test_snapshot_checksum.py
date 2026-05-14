"""Tests for reqwatch.snapshot_checksum."""

import json
import pytest

from reqwatch.snapshot_checksum import (
    ChecksumError,
    compute_checksum,
    store_checksum,
    verify_checksum,
    verify_all,
    get_checksum,
)
from reqwatch.storage import save_snapshot

ENDPOINT = "https://api.example.com/v1/items"


@pytest.fixture()
def store(tmp_path):
    return str(tmp_path)


def _snap(status=200, body=None):
    return {
        "endpoint": ENDPOINT,
        "timestamp": "2024-01-01T00:00:00",
        "status": status,
        "headers": {"content-type": "application/json"},
        "body": body or {"items": [1, 2, 3]},
        "error": None,
    }


def test_compute_checksum_is_deterministic():
    snap = _snap()
    assert compute_checksum(snap) == compute_checksum(snap)


def test_compute_checksum_differs_on_body_change():
    a = _snap(body={"items": [1, 2, 3]})
    b = _snap(body={"items": [1, 2, 4]})
    assert compute_checksum(a) != compute_checksum(b)


def test_compute_checksum_is_hex_string():
    digest = compute_checksum(_snap())
    assert isinstance(digest, str)
    assert len(digest) == 64
    int(digest, 16)  # must be valid hex


def test_store_checksum_returns_digest(store):
    snap = _snap()
    ts = "2024-01-01T00:00:00"
    save_snapshot(store, ENDPOINT, ts, snap)
    digest = store_checksum(store, ENDPOINT, ts, snap)
    assert digest == compute_checksum(snap)


def test_get_checksum_after_store(store):
    snap = _snap()
    ts = "2024-01-01T00:00:00"
    save_snapshot(store, ENDPOINT, ts, snap)
    store_checksum(store, ENDPOINT, ts, snap)
    assert get_checksum(store, ENDPOINT, ts) == compute_checksum(snap)


def test_get_checksum_missing_returns_none(store):
    assert get_checksum(store, ENDPOINT, "nonexistent") is None


def test_verify_checksum_passes_for_intact_snapshot(store):
    snap = _snap()
    ts = "2024-01-01T00:00:00"
    save_snapshot(store, ENDPOINT, ts, snap)
    store_checksum(store, ENDPOINT, ts, snap)
    assert verify_checksum(store, ENDPOINT, ts) is True


def test_verify_checksum_raises_when_no_checksum_stored(store):
    snap = _snap()
    ts = "2024-01-01T00:00:00"
    save_snapshot(store, ENDPOINT, ts, snap)
    with pytest.raises(ChecksumError, match="No checksum stored"):
        verify_checksum(store, ENDPOINT, ts)


def test_verify_checksum_detects_tampering(store, tmp_path):
    snap = _snap()
    ts = "2024-01-01T00:00:00"
    save_snapshot(store, ENDPOINT, ts, snap)
    store_checksum(store, ENDPOINT, ts, snap)

    # Tamper with the snapshot file on disk
    safe = ENDPOINT.replace("://", "_").replace("/", "_").replace(":", "_")
    snap_file = tmp_path / safe / f"{ts}.json"
    tampered = dict(snap)
    tampered["body"] = {"items": [9, 9, 9]}
    snap_file.write_text(json.dumps(tampered))

    assert verify_checksum(store, ENDPOINT, ts) is False


def test_verify_all_returns_dict_of_results(store):
    for i in range(3):
        ts = f"2024-01-0{i+1}T00:00:00"
        snap = _snap(body={"i": i})
        save_snapshot(store, ENDPOINT, ts, snap)
        store_checksum(store, ENDPOINT, ts, snap)

    results = verify_all(store, ENDPOINT)
    assert len(results) == 3
    assert all(v is True for v in results.values())


def test_verify_all_marks_missing_checksum_as_false(store):
    ts = "2024-01-01T00:00:00"
    snap = _snap()
    save_snapshot(store, ENDPOINT, ts, snap)
    # intentionally do NOT store checksum
    results = verify_all(store, ENDPOINT)
    assert results[ts] is False
