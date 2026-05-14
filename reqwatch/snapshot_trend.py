"""Trend analysis for snapshot response times and status codes over time."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from reqwatch.storage import list_snapshots, load_snapshot


class TrendError(Exception):
    pass


@dataclass
class TrendPoint:
    timestamp: str
    status: int
    response_time: Optional[float]
    has_error: bool


@dataclass
class TrendSummary:
    endpoint: str
    points: List[TrendPoint] = field(default_factory=list)
    avg_response_time: Optional[float] = None
    p95_response_time: Optional[float] = None
    error_rate: float = 0.0
    dominant_status: Optional[int] = None


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int(len(sorted_vals) * pct / 100)
    idx = min(idx, len(sorted_vals) - 1)
    return sorted_vals[idx]


def build_trend(store_dir: str, endpoint: str, limit: int = 50) -> TrendSummary:
    """Build a TrendSummary for *endpoint* using up to *limit* most recent snapshots."""
    names = list_snapshots(store_dir, endpoint)
    if not names:
        raise TrendError(f"No snapshots found for endpoint '{endpoint}'")

    names = sorted(names, reverse=True)[:limit]
    points: List[TrendPoint] = []

    for name in names:
        snap = load_snapshot(store_dir, endpoint, name)
        if snap is None:
            continue
        points.append(
            TrendPoint(
                timestamp=snap.get("timestamp", name),
                status=snap.get("status", 0),
                response_time=snap.get("response_time"),
                has_error=bool(snap.get("error")),
            )
        )

    if not points:
        raise TrendError(f"Could not load any snapshots for endpoint '{endpoint}'")

    times = [p.response_time for p in points if p.response_time is not None]
    avg_rt = sum(times) / len(times) if times else None
    p95_rt = _percentile(times, 95) if times else None
    error_rate = sum(1 for p in points if p.has_error) / len(points)

    from collections import Counter
    status_counts = Counter(p.status for p in points if not p.has_error)
    dominant = status_counts.most_common(1)[0][0] if status_counts else None

    return TrendSummary(
        endpoint=endpoint,
        points=points,
        avg_response_time=round(avg_rt, 4) if avg_rt is not None else None,
        p95_response_time=round(p95_rt, 4) if p95_rt is not None else None,
        error_rate=round(error_rate, 4),
        dominant_status=dominant,
    )
