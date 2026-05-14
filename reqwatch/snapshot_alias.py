"""snapshot_alias.py — assign human-readable aliases to snapshot IDs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from reqwatch.storage import list_snapshots


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _aliases_path(store_dir: str) -> Path:
    return Path(store_dir) / "_aliases.json"


def _load_aliases(store_dir: str) -> Dict[str, str]:
    path = _aliases_path(store_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_aliases(store_dir: str, aliases: Dict[str, str]) -> None:
    _aliases_path(store_dir).write_text(json.dumps(aliases, indent=2))


def set_alias(store_dir: str, alias: str, snapshot_id: str) -> None:
    """Bind *alias* to *snapshot_id*. Raises AliasError if snapshot not found."""
    alias = alias.strip()
    if not alias:
        raise AliasError("Alias must be a non-empty string.")
    # Verify the snapshot actually exists somewhere in the store.
    all_ids = {
        sid
        for endpoint in (Path(store_dir).iterdir() if Path(store_dir).exists() else [])
        if endpoint.is_dir()
        for sid in list_snapshots(store_dir, endpoint.name)
    }
    if snapshot_id not in all_ids:
        raise AliasError(f"Snapshot '{snapshot_id}' not found in store.")
    aliases = _load_aliases(store_dir)
    aliases[alias] = snapshot_id
    _save_aliases(store_dir, aliases)


def get_alias(store_dir: str, alias: str) -> Optional[str]:
    """Return the snapshot ID for *alias*, or None if not set."""
    return _load_aliases(store_dir).get(alias)


def delete_alias(store_dir: str, alias: str) -> bool:
    """Remove *alias*. Returns True if it existed, False otherwise."""
    aliases = _load_aliases(store_dir)
    if alias not in aliases:
        return False
    del aliases[alias]
    _save_aliases(store_dir, aliases)
    return True


def list_aliases(store_dir: str) -> Dict[str, str]:
    """Return a copy of all currently defined aliases."""
    return dict(_load_aliases(store_dir))


def resolve(store_dir: str, ref: str) -> str:
    """Resolve *ref* as an alias first, falling back to treating it as a raw ID."""
    resolved = get_alias(store_dir, ref)
    return resolved if resolved is not None else ref
