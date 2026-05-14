"""Stability scoring for endpoints based on snapshot history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from reqwatch.storage import list_snapshots, load_snapshot
from reqwatch.diff import diff_snapshots, has_changes


class ScoreError(Exception):
    """Raised when scoring cannot be completed."""


@dataclass
class StabilityScore:
    endpoint: str
    total_snapshots: int
    change_count: int
    stability: float  # 0.0 (always changing) to 1.0 (never changes)
    grade: str  # A / B / C / D / F


def _grade(stability: float) -> str:
    if stability >= 0.90:
        return "A"
    if stability >= 0.75:
        return "B"
    if stability >= 0.55:
        return "C"
    if stability >= 0.35:
        return "D"
    return "F"


def score_endpoint(store_dir: str, endpoint: str) -> StabilityScore:
    """Compute a stability score for *endpoint* from its saved snapshots."""
    names = list_snapshots(store_dir, endpoint)
    if not names:
        raise ScoreError(f"No snapshots found for endpoint '{endpoint}'")

    snapshots = []
    for name in names:
        snap = load_snapshot(store_dir, endpoint, name)
        if snap is not None:
            snapshots.append(snap)

    if len(snapshots) < 2:
        return StabilityScore(
            endpoint=endpoint,
            total_snapshots=len(snapshots),
            change_count=0,
            stability=1.0,
            grade="A",
        )

    change_count = 0
    for i in range(1, len(snapshots)):
        diff = diff_snapshots(snapshots[i - 1], snapshots[i])
        if has_changes(diff):
            change_count += 1

    transitions = len(snapshots) - 1
    stability = round(1.0 - (change_count / transitions), 4)
    return StabilityScore(
        endpoint=endpoint,
        total_snapshots=len(snapshots),
        change_count=change_count,
        stability=stability,
        grade=_grade(stability),
    )


def score_all_endpoints(store_dir: str, endpoints: List[str]) -> List[StabilityScore]:
    """Score every endpoint in *endpoints*, sorted best-to-worst."""
    scores = []
    for ep in endpoints:
        try:
            scores.append(score_endpoint(store_dir, ep))
        except ScoreError:
            pass
    scores.sort(key=lambda s: s.stability, reverse=True)
    return scores
