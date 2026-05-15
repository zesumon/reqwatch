"""Snapshot health check — assess endpoint health based on recent snapshot history."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from reqwatch.storage import list_snapshots, load_snapshot


class HealthError(Exception):
    pass


@dataclass
class HealthReport:
    endpoint: str
    total: int
    error_count: int
    consecutive_errors: int
    last_status: Optional[int]
    healthy: bool
    reason: str


def _consecutive_errors(snapshots: list) -> int:
    """Count trailing consecutive snapshots that have an error field set."""
    count = 0
    for snap in reversed(snapshots):
        if snap.get("error"):
            count += 1
        else:
            break
    return count


def check_health(
    store_dir: str,
    endpoint: str,
    *,
    error_threshold: float = 0.5,
    consecutive_limit: int = 3,
    window: int = 10,
) -> HealthReport:
    """Return a HealthReport for the given endpoint.

    Parameters
    ----------
    store_dir:
        Root storage directory.
    endpoint:
        Endpoint key to evaluate.
    error_threshold:
        Fraction of errors in *window* snapshots that marks unhealthy.
    consecutive_limit:
        Number of back-to-back errors that marks unhealthy regardless of rate.
    window:
        How many most-recent snapshots to consider.
    """
    ids = list_snapshots(store_dir, endpoint)
    if not ids:
        raise HealthError(f"No snapshots found for endpoint '{endpoint}'")

    recent_ids = ids[-window:]
    snaps = [s for sid in recent_ids if (s := load_snapshot(store_dir, endpoint, sid)) is not None]

    if not snaps:
        raise HealthError(f"Could not load any snapshots for endpoint '{endpoint}'")

    total = len(snaps)
    error_count = sum(1 for s in snaps if s.get("error"))
    consec = _consecutive_errors(snaps)
    last_status = snaps[-1].get("status")

    rate = error_count / total
    if consec >= consecutive_limit:
        healthy = False
        reason = f"{consec} consecutive errors"
    elif rate >= error_threshold:
        healthy = False
        reason = f"error rate {rate:.0%} exceeds threshold {error_threshold:.0%}"
    else:
        healthy = True
        reason = "ok"

    return HealthReport(
        endpoint=endpoint,
        total=total,
        error_count=error_count,
        consecutive_errors=consec,
        last_status=last_status,
        healthy=healthy,
        reason=reason,
    )


def check_all_endpoints(store_dir: str, **kwargs) -> List[HealthReport]:
    """Run health checks for every endpoint that has snapshots."""
    from reqwatch.storage import list_snapshots as _ls
    import os

    endpoints = [
        d for d in os.listdir(store_dir)
        if os.path.isdir(os.path.join(store_dir, d))
    ]
    reports = []
    for ep in sorted(endpoints):
        try:
            reports.append(check_health(store_dir, ep, **kwargs))
        except HealthError:
            pass
    return reports
