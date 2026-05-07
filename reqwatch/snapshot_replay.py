"""Replay stored snapshots through diff logic to reconstruct change history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from reqwatch.storage import list_snapshots, load_snapshot
from reqwatch.diff import diff_snapshots, has_changes


class ReplayError(Exception):
    pass


@dataclass
class ReplayEvent:
    index: int
    timestamp: str
    changed: bool
    diff: dict[str, Any] = field(default_factory=dict)


def replay_endpoint(
    store_dir: str,
    endpoint: str,
    *,
    limit: int | None = None,
) -> list[ReplayEvent]:
    """Walk snapshots oldest-first and produce a change event per transition."""
    names = list_snapshots(store_dir, endpoint)
    if not names:
        raise ReplayError(f"No snapshots found for endpoint: {endpoint!r}")

    # list_snapshots returns newest-first; reverse for chronological replay
    names = list(reversed(names))
    if limit is not None:
        if limit < 1:
            raise ReplayError("limit must be >= 1")
        names = names[:limit]

    events: list[ReplayEvent] = []
    prev = None

    for idx, name in enumerate(names):
        snap = load_snapshot(store_dir, endpoint, name)
        if snap is None:
            continue

        diff = diff_snapshots(prev, snap) if prev is not None else {}
        changed = has_changes(diff) if prev is not None else False

        events.append(
            ReplayEvent(
                index=idx,
                timestamp=snap.get("timestamp", name),
                changed=changed,
                diff=diff,
            )
        )
        prev = snap

    return events


def summarize_replay(events: list[ReplayEvent]) -> dict[str, Any]:
    """Return high-level stats over a replay event list."""
    if not events:
        return {"total": 0, "changes": 0, "stable": 0}
    changes = sum(1 for e in events if e.changed)
    return {
        "total": len(events),
        "changes": changes,
        "stable": len(events) - changes,
    }
