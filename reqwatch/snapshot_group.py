"""Group snapshots by a shared label and query across groups."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from reqwatch.storage import list_snapshots, load_snapshot


class GroupError(Exception):
    pass


def _groups_path(store_dir: str) -> Path:
    return Path(store_dir) / "_groups.json"


def _load_groups(store_dir: str) -> Dict[str, List[str]]:
    p = _groups_path(store_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_groups(store_dir: str, groups: Dict[str, List[str]]) -> None:
    _groups_path(store_dir).write_text(json.dumps(groups, indent=2))


def add_to_group(store_dir: str, group: str, endpoint: str) -> None:
    """Add an endpoint to a named group."""
    if not group.strip():
        raise GroupError("Group name must not be empty.")
    groups = _load_groups(store_dir)
    members = groups.setdefault(group, [])
    if endpoint not in members:
        members.append(endpoint)
    _save_groups(store_dir, groups)


def remove_from_group(store_dir: str, group: str, endpoint: str) -> bool:
    """Remove an endpoint from a group. Returns True if it was present."""
    groups = _load_groups(store_dir)
    members = groups.get(group, [])
    if endpoint not in members:
        return False
    members.remove(endpoint)
    if not members:
        del groups[group]
    _save_groups(store_dir, groups)
    return True


def list_groups(store_dir: str) -> Dict[str, List[str]]:
    """Return all groups and their endpoint members."""
    return _load_groups(store_dir)


def get_group_members(store_dir: str, group: str) -> List[str]:
    """Return endpoints belonging to a group."""
    groups = _load_groups(store_dir)
    if group not in groups:
        raise GroupError(f"Group '{group}' does not exist.")
    return list(groups[group])


def latest_snapshots_for_group(store_dir: str, group: str) -> List[Optional[dict]]:
    """Return the most recent snapshot for each endpoint in the group."""
    members = get_group_members(store_dir, group)
    results = []
    for endpoint in members:
        snaps = list_snapshots(store_dir, endpoint)
        if snaps:
            results.append(load_snapshot(store_dir, endpoint, snaps[-1]))
        else:
            results.append(None)
    return results
