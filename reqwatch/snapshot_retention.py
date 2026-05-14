"""Retention policy enforcement for snapshots.

Allows defining time-based retention rules per endpoint so that snapshots
older than a given age (in days) are automatically removed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from reqwatch.storage import list_snapshots, load_snapshot
from reqwatch.snapshot_prune import prune_snapshots


class RetentionError(Exception):
    """Raised when a retention operation fails."""


@dataclass
class RetentionResult:
    endpoint: str
    total: int
    removed: int
    kept: int


def _cutoff_ts(max_age_days: int) -> float:
    """Return a UNIX timestamp representing *now minus max_age_days*."""
    if max_age_days < 1:
        raise RetentionError("max_age_days must be >= 1")
    return time.time() - max_age_days * 86_400


def apply_retention(
    store_dir: str,
    endpoint: str,
    max_age_days: int,
) -> RetentionResult:
    """Delete snapshots for *endpoint* that are older than *max_age_days*.

    Returns a :class:`RetentionResult` summarising what happened.
    """
    cutoff = _cutoff_ts(max_age_days)
    names = list_snapshots(store_dir, endpoint)
    if not names:
        return RetentionResult(endpoint=endpoint, total=0, removed=0, kept=0)

    expired: List[str] = []
    for name in names:
        snap = load_snapshot(store_dir, endpoint, name)
        if snap is None:
            continue
        ts = snap.get("timestamp", 0.0)
        if isinstance(ts, str):
            # iso-format timestamps stored as strings are ignored safely
            continue
        if float(ts) < cutoff:
            expired.append(name)

    keep_count = len(names) - len(expired)
    if keep_count < 1:
        keep_count = 1  # always keep at least one snapshot

    prune_snapshots(store_dir, endpoint, keep=keep_count)

    removed = max(0, len(names) - keep_count)
    return RetentionResult(
        endpoint=endpoint,
        total=len(names),
        removed=removed,
        kept=keep_count,
    )


def apply_retention_all(
    store_dir: str,
    policy: Dict[str, int],
) -> List[RetentionResult]:
    """Apply retention rules to multiple endpoints.

    *policy* maps endpoint name -> max_age_days.
    """
    results: List[RetentionResult] = []
    for endpoint, max_age_days in policy.items():
        results.append(apply_retention(store_dir, endpoint, max_age_days))
    return results
