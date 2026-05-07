"""Baseline management: pin a snapshot as the reference point for future diffs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

BASELINE_FILENAME = "baseline.json"


class BaselineError(Exception):
    pass


def _baseline_path(store_dir: str, endpoint_key: str) -> Path:
    safe_key = endpoint_key.replace("/", "_").replace(":", "-").strip("_")
    return Path(store_dir) / safe_key / BASELINE_FILENAME


def save_baseline(store_dir: str, endpoint_key: str, snapshot: dict) -> Path:
    """Persist *snapshot* as the baseline for *endpoint_key*."""
    path = _baseline_path(store_dir, endpoint_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    except OSError as exc:
        raise BaselineError(f"Could not write baseline: {exc}") from exc
    return path


def load_baseline(store_dir: str, endpoint_key: str) -> Optional[dict]:
    """Return the pinned baseline snapshot, or *None* if none exists."""
    path = _baseline_path(store_dir, endpoint_key)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"Could not read baseline: {exc}") from exc


def clear_baseline(store_dir: str, endpoint_key: str) -> bool:
    """Delete the baseline file.  Returns True if a file was removed."""
    path = _baseline_path(store_dir, endpoint_key)
    if path.exists():
        path.unlink()
        return True
    return False


def baseline_exists(store_dir: str, endpoint_key: str) -> bool:
    return _baseline_path(store_dir, endpoint_key).exists()
