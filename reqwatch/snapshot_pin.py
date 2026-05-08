"""Pin specific snapshots so they are protected from pruning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from reqwatch.storage import get_snapshot_path


class PinError(Exception):
    pass


def _pins_path(store_dir: str, endpoint: str) -> Path:
    base = Path(get_snapshot_path(store_dir, endpoint, "dummy")).parent
    return base / "_pins.json"


def _load_pins(store_dir: str, endpoint: str) -> List[str]:
    path = _pins_path(store_dir, endpoint)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _save_pins(store_dir: str, endpoint: str, pins: List[str]) -> None:
    path = _pins_path(store_dir, endpoint)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(set(pins)), indent=2))


def pin_snapshot(store_dir: str, endpoint: str, timestamp: str) -> None:
    """Mark a snapshot timestamp as pinned."""
    if not timestamp:
        raise PinError("timestamp must not be empty")
    snap_path = Path(get_snapshot_path(store_dir, endpoint, timestamp))
    if not snap_path.exists():
        raise PinError(f"snapshot not found: {timestamp}")
    pins = _load_pins(store_dir, endpoint)
    if timestamp not in pins:
        pins.append(timestamp)
    _save_pins(store_dir, endpoint, pins)


def unpin_snapshot(store_dir: str, endpoint: str, timestamp: str) -> None:
    """Remove a pin from a snapshot timestamp."""
    pins = _load_pins(store_dir, endpoint)
    if timestamp not in pins:
        raise PinError(f"snapshot is not pinned: {timestamp}")
    pins.remove(timestamp)
    _save_pins(store_dir, endpoint, pins)


def list_pinned(store_dir: str, endpoint: str) -> List[str]:
    """Return all pinned timestamps for an endpoint."""
    return _load_pins(store_dir, endpoint)


def is_pinned(store_dir: str, endpoint: str, timestamp: str) -> bool:
    """Return True if the given snapshot timestamp is pinned."""
    return timestamp in _load_pins(store_dir, endpoint)
