"""Track and enforce per-endpoint request rate limiting for the watcher."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Optional


class RateLimitError(Exception):
    """Raised when a rate limit operation fails."""


def _rate_limit_path(store_dir: str) -> Path:
    return Path(store_dir) / "_rate_limits.json"


def _load_limits(store_dir: str) -> Dict[str, dict]:
    path = _rate_limit_path(store_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise RateLimitError(f"Failed to load rate limits: {exc}") from exc


def _save_limits(store_dir: str, data: Dict[str, dict]) -> None:
    path = _rate_limit_path(store_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(data, indent=2))
    except OSError as exc:
        raise RateLimitError(f"Failed to save rate limits: {exc}") from exc


def set_rate_limit(store_dir: str, endpoint: str, min_interval: float) -> None:
    """Set the minimum seconds between fetches for *endpoint*."""
    if min_interval <= 0:
        raise RateLimitError("min_interval must be a positive number")
    data = _load_limits(store_dir)
    entry = data.get(endpoint, {})
    entry["min_interval"] = min_interval
    data[endpoint] = entry
    _save_limits(store_dir, data)


def record_fetch(store_dir: str, endpoint: str) -> None:
    """Record the current time as the last fetch time for *endpoint*."""
    data = _load_limits(store_dir)
    entry = data.get(endpoint, {})
    entry["last_fetch"] = time.time()
    data[endpoint] = entry
    _save_limits(store_dir, data)


def is_allowed(store_dir: str, endpoint: str) -> bool:
    """Return True if enough time has passed since the last fetch."""
    data = _load_limits(store_dir)
    entry = data.get(endpoint, {})
    min_interval: Optional[float] = entry.get("min_interval")
    last_fetch: Optional[float] = entry.get("last_fetch")
    if min_interval is None or last_fetch is None:
        return True
    return (time.time() - last_fetch) >= min_interval


def get_rate_limit(store_dir: str, endpoint: str) -> Optional[dict]:
    """Return the rate limit entry for *endpoint*, or None if not set."""
    data = _load_limits(store_dir)
    return data.get(endpoint) or None


def clear_rate_limit(store_dir: str, endpoint: str) -> bool:
    """Remove rate limit config for *endpoint*. Returns True if it existed."""
    data = _load_limits(store_dir)
    if endpoint not in data:
        return False
    del data[endpoint]
    _save_limits(store_dir, data)
    return True
