"""Compute and verify checksums for snapshots to detect silent data corruption."""

import hashlib
import json
from pathlib import Path
from typing import Optional

from reqwatch.storage import load_snapshot, list_snapshots


class ChecksumError(Exception):
    pass


def _checksum_path(store_dir: str, endpoint: str) -> Path:
    safe = endpoint.replace("://", "_").replace("/", "_").replace(":", "_")
    return Path(store_dir) / safe / "checksums.json"


def _load_checksums(store_dir: str, endpoint: str) -> dict:
    path = _checksum_path(store_dir, endpoint)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_checksums(store_dir: str, endpoint: str, data: dict) -> None:
    path = _checksum_path(store_dir, endpoint)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def compute_checksum(snapshot: dict) -> str:
    """Return SHA-256 hex digest of the canonical JSON representation of a snapshot."""
    canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def store_checksum(store_dir: str, endpoint: str, timestamp: str, snapshot: dict) -> str:
    """Compute and persist the checksum for a given snapshot timestamp."""
    digest = compute_checksum(snapshot)
    data = _load_checksums(store_dir, endpoint)
    data[timestamp] = digest
    _save_checksums(store_dir, endpoint, data)
    return digest


def verify_checksum(store_dir: str, endpoint: str, timestamp: str) -> bool:
    """Return True if the stored checksum matches the current snapshot on disk."""
    data = _load_checksums(store_dir, endpoint)
    if timestamp not in data:
        raise ChecksumError(f"No checksum stored for {endpoint!r} at {timestamp!r}")
    snapshot = load_snapshot(store_dir, endpoint, timestamp)
    if snapshot is None:
        raise ChecksumError(f"Snapshot not found for {endpoint!r} at {timestamp!r}")
    return compute_checksum(snapshot) == data[timestamp]


def verify_all(store_dir: str, endpoint: str) -> dict:
    """Verify every stored checksum for an endpoint. Returns {timestamp: bool}."""
    results = {}
    for ts in list_snapshots(store_dir, endpoint):
        try:
            results[ts] = verify_checksum(store_dir, endpoint, ts)
        except ChecksumError:
            results[ts] = False
    return results


def get_checksum(store_dir: str, endpoint: str, timestamp: str) -> Optional[str]:
    """Return the stored checksum for a snapshot, or None if not found."""
    return _load_checksums(store_dir, endpoint).get(timestamp)
