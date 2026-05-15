"""snapshot_chain.py — build a linked chain of snapshots showing lineage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from reqwatch.storage import list_snapshots, load_snapshot


class ChainError(Exception):
    pass


@dataclass
class ChainLink:
    snapshot_id: str
    timestamp: str
    status: int
    has_change: bool
    parent_id: Optional[str]
    child_id: Optional[str]
    summary: str


@dataclass
class SnapshotChain:
    endpoint: str
    links: List[ChainLink] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.links)

    @property
    def change_count(self) -> int:
        return sum(1 for lk in self.links if lk.has_change)


def build_chain(store_dir: str, endpoint: str) -> SnapshotChain:
    """Build a chronological chain of snapshots for an endpoint."""
    ids = list_snapshots(store_dir, endpoint)
    if not ids:
        raise ChainError(f"No snapshots found for endpoint: {endpoint!r}")

    # list_snapshots returns newest-first; reverse for chronological order
    ids_chrono = list(reversed(ids))
    snaps = []
    for sid in ids_chrono:
        snap = load_snapshot(store_dir, endpoint, sid)
        if snap is not None:
            snaps.append((sid, snap))

    if not snaps:
        raise ChainError(f"Could not load any snapshots for endpoint: {endpoint!r}")

    from reqwatch.diff import diff_snapshots, has_changes

    chain = SnapshotChain(endpoint=endpoint)
    for i, (sid, snap) in enumerate(snaps):
        parent_id = snaps[i - 1][0] if i > 0 else None
        child_id = snaps[i + 1][0] if i < len(snaps) - 1 else None

        changed = False
        if parent_id is not None:
            prev_snap = snaps[i - 1][1]
            diff = diff_snapshots(prev_snap, snap)
            changed = has_changes(diff)

        summary = f"HTTP {snap.get('status', '?')} — {'changed' if changed else 'stable'}"
        link = ChainLink(
            snapshot_id=sid,
            timestamp=snap.get("timestamp", ""),
            status=snap.get("status", 0),
            has_change=changed,
            parent_id=parent_id,
            child_id=child_id,
            summary=summary,
        )
        chain.links.append(link)

    return chain


def summarize_chain(chain: SnapshotChain) -> dict:
    """Return a plain-dict summary of the chain."""
    return {
        "endpoint": chain.endpoint,
        "total_snapshots": chain.length,
        "total_changes": chain.change_count,
        "stability_pct": round(
            100.0 * (chain.length - chain.change_count) / chain.length, 2
        ) if chain.length else 0.0,
        "links": [
            {
                "id": lk.snapshot_id,
                "timestamp": lk.timestamp,
                "status": lk.status,
                "has_change": lk.has_change,
                "parent_id": lk.parent_id,
                "child_id": lk.child_id,
                "summary": lk.summary,
            }
            for lk in chain.links
        ],
    }
