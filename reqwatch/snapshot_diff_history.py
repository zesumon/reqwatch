"""Compute a sequential diff history across all snapshots for an endpoint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from reqwatch.storage import list_snapshots, load_snapshot
from reqwatch.diff import diff_snapshots, has_changes, format_diff


class DiffHistoryError(Exception):
    """Raised when diff history cannot be computed."""


@dataclass
class DiffEntry:
    """Represents a single diff between two consecutive snapshots."""

    index: int
    from_timestamp: Optional[str]
    to_timestamp: str
    changed: bool
    diff_lines: List[str] = field(default_factory=list)


def build_diff_history(store_dir: str, endpoint: str) -> List[DiffEntry]:
    """Return a list of DiffEntry objects for each consecutive snapshot pair.

    The list is ordered oldest-to-newest so callers can iterate forward
    through time.
    """
    timestamps = list_snapshots(store_dir, endpoint)
    if not timestamps:
        raise DiffHistoryError(
            f"No snapshots found for endpoint '{endpoint}' in '{store_dir}'."
        )

    # list_snapshots returns newest-first; reverse for chronological order
    timestamps = list(reversed(timestamps))

    entries: List[DiffEntry] = []
    prev_snapshot = None

    for idx, ts in enumerate(timestamps):
        current_snapshot = load_snapshot(store_dir, endpoint, ts)
        if current_snapshot is None:
            continue

        if prev_snapshot is None:
            entries.append(
                DiffEntry(
                    index=idx,
                    from_timestamp=None,
                    to_timestamp=ts,
                    changed=False,
                    diff_lines=[],
                )
            )
        else:
            diff = diff_snapshots(prev_snapshot, current_snapshot)
            changed = has_changes(diff)
            lines = format_diff(diff) if changed else []
            entries.append(
                DiffEntry(
                    index=idx,
                    from_timestamp=prev_snapshot.get("timestamp"),
                    to_timestamp=ts,
                    changed=changed,
                    diff_lines=lines,
                )
            )

        prev_snapshot = current_snapshot

    return entries


def summarize_diff_history(entries: List[DiffEntry]) -> dict:
    """Return a summary dict describing the diff history."""
    total = len(entries)
    changed_count = sum(1 for e in entries if e.changed)
    return {
        "total_snapshots": total,
        "total_changes": changed_count,
        "change_rate": round(changed_count / total, 4) if total else 0.0,
        "first_timestamp": entries[0].to_timestamp if entries else None,
        "last_timestamp": entries[-1].to_timestamp if entries else None,
    }
