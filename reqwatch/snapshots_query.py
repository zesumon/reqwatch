"""Query and filter stored snapshots by various criteria."""

from __future__ import annotations

from typing import List, Optional
from reqwatch.storage import list_snapshots, load_snapshot


class QueryError(Exception):
    pass


def query_snapshots(
    store_dir: str,
    endpoint: str,
    limit: Optional[int] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    status_code: Optional[int] = None,
    has_error: Optional[bool] = None,
) -> List[dict]:
    """Return snapshots matching the given criteria, newest first."""
    names = list_snapshots(store_dir, endpoint)
    if not names:
        return []

    results = []
    for name in reversed(names):  # newest first
        snap = load_snapshot(store_dir, endpoint, name)
        if snap is None:
            continue

        ts = snap.get("timestamp", "")
        if since and ts < since:
            continue
        if until and ts > until:
            continue
        if status_code is not None and snap.get("status_code") != status_code:
            continue
        if has_error is True and not snap.get("error"):
            continue
        if has_error is False and snap.get("error"):
            continue

        results.append(snap)
        if limit and len(results) >= limit:
            break

    return results


def summarize_snapshots(snapshots: List[dict]) -> dict:
    """Return aggregate statistics over a list of snapshots."""
    if not snapshots:
        return {"count": 0}

    status_codes = [s["status_code"] for s in snapshots if "status_code" in s]
    errors = [s for s in snapshots if s.get("error")]
    timestamps = [s["timestamp"] for s in snapshots if "timestamp" in s]

    return {
        "count": len(snapshots),
        "earliest": min(timestamps) if timestamps else None,
        "latest": max(timestamps) if timestamps else None,
        "error_count": len(errors),
        "status_codes": sorted(set(status_codes)),
    }
