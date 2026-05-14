"""Attach and manage human-readable labels on snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

LABEL_FILE = "labels.json"


class LabelError(Exception):
    """Raised when a label operation fails."""


def _labels_path(store_dir: str) -> Path:
    return Path(store_dir) / LABEL_FILE


def _load_labels(store_dir: str) -> Dict[str, List[str]]:
    path = _labels_path(store_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save_labels(store_dir: str, data: Dict[str, List[str]]) -> None:
    path = _labels_path(store_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def add_label(store_dir: str, snapshot_id: str, label: str) -> None:
    """Attach *label* to *snapshot_id*.  Duplicate labels are silently ignored."""
    if not label or not label.strip():
        raise LabelError("label must be a non-empty string")
    data = _load_labels(store_dir)
    labels = data.setdefault(snapshot_id, [])
    if label not in labels:
        labels.append(label)
    _save_labels(store_dir, data)


def remove_label(store_dir: str, snapshot_id: str, label: str) -> bool:
    """Remove *label* from *snapshot_id*.  Returns True if it existed."""
    data = _load_labels(store_dir)
    labels = data.get(snapshot_id, [])
    if label not in labels:
        return False
    labels.remove(label)
    if not labels:
        del data[snapshot_id]
    _save_labels(store_dir, data)
    return True


def get_labels(store_dir: str, snapshot_id: str) -> List[str]:
    """Return all labels attached to *snapshot_id*."""
    return list(_load_labels(store_dir).get(snapshot_id, []))


def find_by_label(store_dir: str, label: str) -> List[str]:
    """Return snapshot IDs that carry *label*."""
    return [
        sid
        for sid, labels in _load_labels(store_dir).items()
        if label in labels
    ]


def clear_labels(store_dir: str, snapshot_id: str) -> None:
    """Remove every label from *snapshot_id*."""
    data = _load_labels(store_dir)
    data.pop(snapshot_id, None)
    _save_labels(store_dir, data)
