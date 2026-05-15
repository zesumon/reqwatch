"""Snapshot locking — mark snapshots as immutable to prevent pruning or overwriting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from reqwatch.storage import get_snapshot_path


class LockError(Exception):
    pass


def _lock_path(store_dir: str, endpoint: str) -> Path:
    base = Path(get_snapshot_path(store_dir, endpoint)).parent
    return base / "locks.json"


def _load_locks(store_dir: str, endpoint: str) -> List[str]:
    p = _lock_path(store_dir, endpoint)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_locks(store_dir: str, endpoint: str, locks: List[str]) -> None:
    p = _lock_path(store_dir, endpoint)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(sorted(set(locks)), indent=2))


def lock_snapshot(store_dir: str, endpoint: str, snapshot_id: str) -> None:
    """Mark *snapshot_id* as locked for *endpoint*."""
    if not snapshot_id or not snapshot_id.strip():
        raise LockError("snapshot_id must not be empty")
    locks = _load_locks(store_dir, endpoint)
    if snapshot_id not in locks:
        locks.append(snapshot_id)
        _save_locks(store_dir, endpoint, locks)


def unlock_snapshot(store_dir: str, endpoint: str, snapshot_id: str) -> bool:
    """Remove the lock on *snapshot_id*.  Returns True if it was locked."""
    locks = _load_locks(store_dir, endpoint)
    if snapshot_id in locks:
        locks.remove(snapshot_id)
        _save_locks(store_dir, endpoint, locks)
        return True
    return False


def is_locked(store_dir: str, endpoint: str, snapshot_id: str) -> bool:
    """Return True if *snapshot_id* is currently locked."""
    return snapshot_id in _load_locks(store_dir, endpoint)


def list_locked(store_dir: str, endpoint: str) -> List[str]:
    """Return all locked snapshot IDs for *endpoint*."""
    return list(_load_locks(store_dir, endpoint))


def clear_locks(store_dir: str, endpoint: str) -> int:
    """Remove all locks for *endpoint*.  Returns the number of locks cleared."""
    locks = _load_locks(store_dir, endpoint)
    count = len(locks)
    if count:
        _save_locks(store_dir, endpoint, [])
    return count
