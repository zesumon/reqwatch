"""snapshot_watchdog.py — detect snapshots that have gone stale or silent.

A 'silent' endpoint is one that hasn't been fetched within an expected
interval.  The watchdog compares each endpoint's most-recent snapshot
timestamp against a caller-supplied threshold and returns a report.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from reqwatch.storage import list_snapshots, load_snapshot


class WatchdogError(Exception):
    """Raised when the watchdog cannot complete a check."""


@dataclass
class WatchdogResult:
    endpoint: str
    last_seen: Optional[float]   # Unix timestamp or None if no snapshots
    age_seconds: Optional[float] # seconds since last snapshot
    is_stale: bool
    is_silent: bool              # True when no snapshots exist at all


@dataclass
class WatchdogReport:
    checked_at: float = field(default_factory=time.time)
    results: List[WatchdogResult] = field(default_factory=list)

    @property
    def stale(self) -> List[WatchdogResult]:
        return [r for r in self.results if r.is_stale]

    @property
    def silent(self) -> List[WatchdogResult]:
        return [r for r in self.results if r.is_silent]

    def to_dict(self) -> Dict:
        return {
            "checked_at": self.checked_at,
            "total": len(self.results),
            "stale_count": len(self.stale),
            "silent_count": len(self.silent),
            "results": [
                {
                    "endpoint": r.endpoint,
                    "last_seen": r.last_seen,
                    "age_seconds": r.age_seconds,
                    "is_stale": r.is_stale,
                    "is_silent": r.is_silent,
                }
                for r in self.results
            ],
        }


def check_endpoint(
    store_dir: str,
    endpoint: str,
    threshold_seconds: float,
    now: Optional[float] = None,
) -> WatchdogResult:
    """Return a WatchdogResult for a single endpoint."""
    if threshold_seconds <= 0:
        raise WatchdogError("threshold_seconds must be positive")
    now = now if now is not None else time.time()
    snapshots = list_snapshots(store_dir, endpoint)
    if not snapshots:
        return WatchdogResult(
            endpoint=endpoint,
            last_seen=None,
            age_seconds=None,
            is_stale=True,
            is_silent=True,
        )
    latest_id = snapshots[-1]
    snap = load_snapshot(store_dir, endpoint, latest_id)
    last_seen = snap.get("timestamp") if snap else None
    if last_seen is None:
        return WatchdogResult(
            endpoint=endpoint,
            last_seen=None,
            age_seconds=None,
            is_stale=True,
            is_silent=False,
        )
    age = now - last_seen
    return WatchdogResult(
        endpoint=endpoint,
        last_seen=last_seen,
        age_seconds=age,
        is_stale=age > threshold_seconds,
        is_silent=False,
    )


def run_watchdog(
    store_dir: str,
    endpoints: List[str],
    threshold_seconds: float,
    now: Optional[float] = None,
) -> WatchdogReport:
    """Check all endpoints and return a consolidated WatchdogReport."""
    if not endpoints:
        raise WatchdogError("endpoints list must not be empty")
    now = now if now is not None else time.time()
    report = WatchdogReport(checked_at=now)
    for ep in endpoints:
        result = check_endpoint(store_dir, ep, threshold_seconds, now=now)
        report.results.append(result)
    return report
