"""Snapshot TTL (time-to-live) management — mark snapshots as stale after a given duration."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from reqwatch.storage import list_snapshots, load_snapshot


class TTLError(Exception):
    """Raised when a TTL operation fails."""


def _ttl_path(store_dir: str) -> Path:
    return Path(store_dir) / "_ttl.json"


def _load_ttls(store_dir: str) -> Dict[str, float]:
    path = _ttl_path(store_dir)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_ttls(store_dir: str, ttls: Dict[str, float]) -> None:
    _ttl_path(store_dir).write_text(json.dumps(ttls, indent=2))


def set_ttl(store_dir: str, endpoint: str, seconds: float) -> None:
    """Set a TTL in seconds for all snapshots of *endpoint*."""
    if seconds <= 0:
        raise TTLError("TTL must be a positive number of seconds.")
    ttls = _load_ttls(store_dir)
    ttls[endpoint] = seconds
    _save_ttls(store_dir, ttls)


def get_ttl(store_dir: str, endpoint: str) -> Optional[float]:
    """Return the TTL (seconds) for *endpoint*, or None if unset."""
    return _load_ttls(store_dir).get(endpoint)


def clear_ttl(store_dir: str, endpoint: str) -> bool:
    """Remove the TTL for *endpoint*. Returns True if it existed."""
    ttls = _load_ttls(store_dir)
    if endpoint not in ttls:
        return False
    del ttls[endpoint]
    _save_ttls(store_dir, ttls)
    return True


@dataclass
class StaleSnapshot:
    snapshot_id: str
    endpoint: str
    age_seconds: float
    ttl_seconds: float


def find_stale(store_dir: str, endpoint: str, now: Optional[float] = None) -> List[StaleSnapshot]:
    """Return snapshots for *endpoint* whose age exceeds the configured TTL."""
    ttl = get_ttl(store_dir, endpoint)
    if ttl is None:
        return []
    now = now or time.time()
    stale: List[StaleSnapshot] = []
    for snap_id in list_snapshots(store_dir, endpoint):
        snap = load_snapshot(store_dir, endpoint, snap_id)
        if snap is None:
            continue
        ts = snap.get("timestamp", 0)
        age = now - ts
        if age > ttl:
            stale.append(StaleSnapshot(snap_id, endpoint, age, ttl))
    return stale
