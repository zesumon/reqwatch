"""Compute summary statistics across a series of snapshots for an endpoint."""

from __future__ import annotations

from typing import Any

from reqwatch.storage import list_snapshots, load_snapshot


class StatsError(Exception):
    pass


def _status_counts(snapshots: list[dict]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for snap in snapshots:
        code = snap.get("status_code")
        if code is not None:
            counts[code] = counts.get(code, 0) + 1
    return counts


def _error_rate(snapshots: list[dict]) -> float:
    if not snapshots:
        return 0.0
    errors = sum(1 for s in snapshots if s.get("error") is not None)
    return round(errors / len(snapshots), 4)


def _avg_body_size(snapshots: list[dict]) -> float:
    sizes = []
    for snap in snapshots:
        body = snap.get("body")
        if isinstance(body, str):
            sizes.append(len(body))
        elif isinstance(body, (dict, list)):
            import json
            sizes.append(len(json.dumps(body)))
    if not sizes:
        return 0.0
    return round(sum(sizes) / len(sizes), 2)


def _avg_response_time(snapshots: list[dict]) -> float | None:
    """Return average response time in seconds, or None if no data is available."""
    times = [
        s["response_time"]
        for s in snapshots
        if isinstance(s.get("response_time"), (int, float))
    ]
    if not times:
        return None
    return round(sum(times) / len(times), 4)


def compute_stats(store_dir: str, endpoint: str, limit: int = 50) -> dict[str, Any]:
    """Return statistics for the *limit* most recent snapshots of *endpoint*."""
    names = list_snapshots(store_dir, endpoint)
    if not names:
        raise StatsError(f"No snapshots found for endpoint: {endpoint!r}")

    recent = names[-limit:]
    snapshots = []
    for name in recent:
        snap = load_snapshot(store_dir, endpoint, name)
        if snap is not None:
            snapshots.append(snap)

    return {
        "endpoint": endpoint,
        "total_snapshots": len(snapshots),
        "status_counts": _status_counts(snapshots),
        "error_rate": _error_rate(snapshots),
        "avg_body_size_chars": _avg_body_size(snapshots),
        "avg_response_time_seconds": _avg_response_time(snapshots),
        "first_timestamp": snapshots[0].get("timestamp") if snapshots else None,
        "last_timestamp": snapshots[-1].get("timestamp") if snapshots else None,
    }
