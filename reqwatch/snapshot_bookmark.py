"""Named bookmarks for snapshots — save a human-friendly alias pointing to a snapshot ID."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class BookmarkError(Exception):
    pass


def _bookmarks_path(store_dir: str) -> Path:
    return Path(store_dir) / "_bookmarks.json"


def _load_bookmarks(store_dir: str) -> dict[str, str]:
    p = _bookmarks_path(store_dir)
    if not p.exists():
        return {}
    with p.open() as f:
        return json.load(f)


def _save_bookmarks(store_dir: str, data: dict[str, str]) -> None:
    _bookmarks_path(store_dir).write_text(json.dumps(data, indent=2))


def set_bookmark(store_dir: str, name: str, snapshot_id: str) -> None:
    """Create or update a named bookmark pointing to *snapshot_id*."""
    if not name or not name.strip():
        raise BookmarkError("Bookmark name must not be empty.")
    if not snapshot_id or not snapshot_id.strip():
        raise BookmarkError("snapshot_id must not be empty.")
    bookmarks = _load_bookmarks(store_dir)
    bookmarks[name] = snapshot_id
    _save_bookmarks(store_dir, bookmarks)


def get_bookmark(store_dir: str, name: str) -> Optional[str]:
    """Return the snapshot ID for *name*, or None if not found."""
    return _load_bookmarks(store_dir).get(name)


def delete_bookmark(store_dir: str, name: str) -> bool:
    """Remove a bookmark.  Returns True if it existed, False otherwise."""
    bookmarks = _load_bookmarks(store_dir)
    if name not in bookmarks:
        return False
    del bookmarks[name]
    _save_bookmarks(store_dir, bookmarks)
    return True


def list_bookmarks(store_dir: str) -> dict[str, str]:
    """Return all bookmarks as {name: snapshot_id}."""
    return dict(_load_bookmarks(store_dir))


def resolve_bookmark(store_dir: str, name: str) -> str:
    """Like get_bookmark but raises BookmarkError when the name is missing."""
    sid = get_bookmark(store_dir, name)
    if sid is None:
        raise BookmarkError(f"No bookmark named '{name}'.")
    return sid
