"""Attach human-readable notes to individual snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from reqwatch.storage import get_snapshot_path


class AnnotateError(Exception):
    pass


def _annotation_path(store_dir: str, endpoint: str, ref: str) -> Path:
    base = get_snapshot_path(store_dir, endpoint, ref)
    return Path(str(base).replace(".json", ".note.json"))


def save_annotation(store_dir: str, endpoint: str, ref: str, note: str) -> None:
    """Persist a note string for the given snapshot ref."""
    if not note or not note.strip():
        raise AnnotateError("Annotation note must not be empty.")

    snap_path = get_snapshot_path(store_dir, endpoint, ref)
    if not snap_path.exists():
        raise AnnotateError(f"Snapshot not found: endpoint={endpoint!r} ref={ref!r}")

    ann_path = _annotation_path(store_dir, endpoint, ref)
    ann_path.parent.mkdir(parents=True, exist_ok=True)
    ann_path.write_text(json.dumps({"ref": ref, "note": note.strip()}), encoding="utf-8")


def load_annotation(store_dir: str, endpoint: str, ref: str) -> Optional[str]:
    """Return the note for the given snapshot ref, or None if absent."""
    ann_path = _annotation_path(store_dir, endpoint, ref)
    if not ann_path.exists():
        return None
    data = json.loads(ann_path.read_text(encoding="utf-8"))
    return data.get("note")


def delete_annotation(store_dir: str, endpoint: str, ref: str) -> bool:
    """Remove an annotation. Returns True if something was deleted."""
    ann_path = _annotation_path(store_dir, endpoint, ref)
    if ann_path.exists():
        ann_path.unlink()
        return True
    return False


def list_annotations(store_dir: str, endpoint: str) -> list[dict]:
    """Return all annotations for an endpoint, sorted by ref."""
    ep_dir = Path(store_dir) / endpoint.replace("://", "_").replace("/", "_")
    if not ep_dir.exists():
        return []
    results = []
    for ann_file in sorted(ep_dir.glob("*.note.json")):
        try:
            data = json.loads(ann_file.read_text(encoding="utf-8"))
            results.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return results
