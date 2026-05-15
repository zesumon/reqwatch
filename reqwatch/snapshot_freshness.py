"""Snapshot freshness checker — reports how recently each endpoint was fetched."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from reqwatch.storage import list_snapshots, load_snapshot


class FreshnessError(Exception):
    pass


@dataclass
class FreshnessReport:
    endpoint: str
    latest_ts: Optional[float]  # Unix timestamp of most recent snapshot
    age_seconds: Optional[float]  # seconds since last snapshot
    snapshot_count: int
    is_fresh: bool  # True if age_seconds <= max_age_seconds


def _age(ts: float, now: float) -> float:
    return max(0.0, now - ts)


def check_freshness(
    store_dir: str,
    endpoint: str,
    max_age_seconds: float = 3600.0,
    *,
    _now: Optional[float] = None,
) -> FreshnessReport:
    """Return a FreshnessReport for a single endpoint."""
    if max_age_seconds <= 0:
        raise FreshnessError("max_age_seconds must be positive")

    now = _now if _now is not None else time.time()
    snapshots = list_snapshots(store_dir, endpoint)

    if not snapshots:
        return FreshnessReport(
            endpoint=endpoint,
            latest_ts=None,
            age_seconds=None,
            snapshot_count=0,
            is_fresh=False,
        )

    latest_id = snapshots[-1]
    snap = load_snapshot(store_dir, endpoint, latest_id)
    latest_ts = snap.get("timestamp") if snap else None

    if latest_ts is None:
        return FreshnessReport(
            endpoint=endpoint,
            latest_ts=None,
            age_seconds=None,
            snapshot_count=len(snapshots),
            is_fresh=False,
        )

    age = _age(float(latest_ts), now)
    return FreshnessReport(
        endpoint=endpoint,
        latest_ts=float(latest_ts),
        age_seconds=age,
        snapshot_count=len(snapshots),
        is_fresh=age <= max_age_seconds,
    )


def check_all_freshness(
    store_dir: str,
    endpoints: List[str],
    max_age_seconds: float = 3600.0,
    *,
    _now: Optional[float] = None,
) -> Dict[str, FreshnessReport]:
    """Return freshness reports for multiple endpoints."""
    return {
        ep: check_freshness(store_dir, ep, max_age_seconds, _now=_now)
        for ep in endpoints
    }
