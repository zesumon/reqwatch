"""Track how many times each endpoint has been watched/fetched."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


class WatchCountError(Exception):
    pass


def _counts_path(store_dir: str) -> Path:
    return Path(store_dir) / "_watch_counts.json"


def _load_counts(store_dir: str) -> Dict[str, int]:
    path = _counts_path(store_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise WatchCountError(f"Failed to load watch counts: {exc}") from exc


def _save_counts(store_dir: str, counts: Dict[str, int]) -> None:
    path = _counts_path(store_dir)
    try:
        path.write_text(json.dumps(counts, indent=2))
    except OSError as exc:
        raise WatchCountError(f"Failed to save watch counts: {exc}") from exc


def increment(store_dir: str, endpoint: str) -> int:
    """Increment the watch count for *endpoint* and return the new value."""
    if not endpoint:
        raise WatchCountError("endpoint must not be empty")
    counts = _load_counts(store_dir)
    counts[endpoint] = counts.get(endpoint, 0) + 1
    _save_counts(store_dir, counts)
    return counts[endpoint]


def get_count(store_dir: str, endpoint: str) -> int:
    """Return the current watch count for *endpoint* (0 if never watched)."""
    if not endpoint:
        raise WatchCountError("endpoint must not be empty")
    return _load_counts(store_dir).get(endpoint, 0)


def reset(store_dir: str, endpoint: str) -> None:
    """Reset the watch count for *endpoint* to zero."""
    if not endpoint:
        raise WatchCountError("endpoint must not be empty")
    counts = _load_counts(store_dir)
    if endpoint in counts:
        del counts[endpoint]
        _save_counts(store_dir, counts)


def all_counts(store_dir: str) -> Dict[str, int]:
    """Return a copy of all endpoint watch counts."""
    return dict(_load_counts(store_dir))
