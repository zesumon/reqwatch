"""Tag management for snapshots — attach, remove, and query string labels."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

TAGS_FILENAME = "tags.json"


class TagError(Exception):
    pass


def _tags_path(store_dir: str) -> Path:
    return Path(store_dir) / TAGS_FILENAME


def _load_tags(store_dir: str) -> dict:
    path = _tags_path(store_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise TagError(f"Failed to read tags file: {exc}") from exc


def _save_tags(store_dir: str, data: dict) -> None:
    path = _tags_path(store_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(data, indent=2))
    except OSError as exc:
        raise TagError(f"Failed to write tags file: {exc}") from exc


def add_tag(store_dir: str, snapshot_id: str, tag: str) -> None:
    """Attach a tag to a snapshot. No-op if the tag already exists."""
    tag = tag.strip()
    if not tag:
        raise TagError("Tag must be a non-empty string.")
    data = _load_tags(store_dir)
    tags: List[str] = data.get(snapshot_id, [])
    if tag not in tags:
        tags.append(tag)
    data[snapshot_id] = tags
    _save_tags(store_dir, data)


def remove_tag(store_dir: str, snapshot_id: str, tag: str) -> None:
    """Remove a tag from a snapshot. No-op if the tag is absent."""
    data = _load_tags(store_dir)
    tags: List[str] = data.get(snapshot_id, [])
    data[snapshot_id] = [t for t in tags if t != tag]
    _save_tags(store_dir, data)


def get_tags(store_dir: str, snapshot_id: str) -> List[str]:
    """Return all tags for a given snapshot."""
    return _load_tags(store_dir).get(snapshot_id, [])


def find_by_tag(store_dir: str, tag: str) -> List[str]:
    """Return snapshot IDs that have the given tag."""
    data = _load_tags(store_dir)
    return [sid for sid, tags in data.items() if tag in tags]


def clear_tags(store_dir: str, snapshot_id: str) -> None:
    """Remove all tags from a snapshot."""
    data = _load_tags(store_dir)
    data.pop(snapshot_id, None)
    _save_tags(store_dir, data)
