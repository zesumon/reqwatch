"""Compare two named snapshots or snapshot ranges for an endpoint."""

from __future__ import annotations

from typing import Any

from reqwatch.storage import load_snapshot, list_snapshots
from reqwatch.diff import diff_snapshots, format_diff, has_changes


class CompareError(Exception):
    pass


def _resolve_snapshot(store_dir: str, endpoint: str, ref: str) -> dict[str, Any]:
    """Resolve a snapshot by index (e.g. '-1', '-2') or full timestamp key."""
    snaps = list_snapshots(store_dir, endpoint)
    if not snaps:
        raise CompareError(f"No snapshots found for endpoint '{endpoint}'")

    if ref.lstrip("-").isdigit():
        idx = int(ref)
        try:
            key = snaps[idx]
        except IndexError:
            raise CompareError(
                f"Snapshot index {ref} out of range (have {len(snaps)} snapshots)"
            )
        snap = load_snapshot(store_dir, endpoint, key)
    else:
        snap = load_snapshot(store_dir, endpoint, ref)

    if snap is None:
        raise CompareError(f"Snapshot '{ref}' not found for endpoint '{endpoint}'")
    return snap


def compare_snapshots(
    store_dir: str,
    endpoint: str,
    ref_a: str = "-2",
    ref_b: str = "-1",
) -> dict[str, Any]:
    """Return a comparison result dict between two snapshots.

    ref_a / ref_b can be integer indices ('-1' = latest, '-2' = second-latest)
    or explicit timestamp keys.
    """
    snap_a = _resolve_snapshot(store_dir, endpoint, ref_a)
    snap_b = _resolve_snapshot(store_dir, endpoint, ref_b)

    diff = diff_snapshots(snap_a, snap_b)
    changed = has_changes(diff)
    lines = format_diff(diff)

    return {
        "endpoint": endpoint,
        "ref_a": snap_a.get("timestamp", ref_a),
        "ref_b": snap_b.get("timestamp", ref_b),
        "changed": changed,
        "diff_lines": lines,
        "diff": diff,
    }
