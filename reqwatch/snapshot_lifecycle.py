"""Lifecycle state tracking for snapshots (draft, active, deprecated, archived)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

VALID_STATES = {"draft", "active", "deprecated", "archived"}


class LifecycleError(Exception):
    pass


def _lifecycle_path(store_dir: str) -> Path:
    return Path(store_dir) / "_lifecycle.json"


def _load_states(store_dir: str) -> Dict[str, str]:
    p = _lifecycle_path(store_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_states(store_dir: str, states: Dict[str, str]) -> None:
    _lifecycle_path(store_dir).write_text(json.dumps(states, indent=2))


def set_state(store_dir: str, snapshot_id: str, state: str) -> str:
    """Set the lifecycle state for a snapshot. Returns the new state."""
    if state not in VALID_STATES:
        raise LifecycleError(
            f"Invalid state '{state}'. Must be one of: {sorted(VALID_STATES)}"
        )
    if not snapshot_id or not snapshot_id.strip():
        raise LifecycleError("snapshot_id must not be empty")
    states = _load_states(store_dir)
    states[snapshot_id] = state
    _save_states(store_dir, states)
    return state


def get_state(store_dir: str, snapshot_id: str) -> Optional[str]:
    """Return the lifecycle state for a snapshot, or None if unset."""
    return _load_states(store_dir).get(snapshot_id)


def list_by_state(store_dir: str, state: str) -> List[str]:
    """Return all snapshot IDs in the given lifecycle state."""
    if state not in VALID_STATES:
        raise LifecycleError(
            f"Invalid state '{state}'. Must be one of: {sorted(VALID_STATES)}"
        )
    return [
        sid for sid, s in _load_states(store_dir).items() if s == state
    ]


def delete_state(store_dir: str, snapshot_id: str) -> bool:
    """Remove lifecycle state for a snapshot. Returns True if it existed."""
    states = _load_states(store_dir)
    if snapshot_id not in states:
        return False
    del states[snapshot_id]
    _save_states(store_dir, states)
    return True


def transition(store_dir: str, snapshot_id: str, from_state: str, to_state: str) -> str:
    """Transition a snapshot from one state to another, enforcing current state."""
    current = get_state(store_dir, snapshot_id)
    if current != from_state:
        raise LifecycleError(
            f"Expected state '{from_state}' but snapshot is '{current}'"
        )
    return set_state(store_dir, snapshot_id, to_state)
