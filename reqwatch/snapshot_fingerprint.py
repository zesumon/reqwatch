"""Fingerprint snapshots by endpoint to detect structural schema changes."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from reqwatch.storage import list_snapshots, load_snapshot


class FingerprintError(Exception):
    """Raised when fingerprinting fails."""


def _extract_schema(body: Any, depth: int = 0, max_depth: int = 4) -> Any:
    """Recursively extract structural schema (keys + types, not values)."""
    if depth >= max_depth:
        return "..."
    if isinstance(body, dict):
        return {k: _extract_schema(v, depth + 1, max_depth) for k, v in sorted(body.items())}
    if isinstance(body, list):
        if not body:
            return []
        return [_extract_schema(body[0], depth + 1, max_depth)]
    return type(body).__name__


def compute_fingerprint(snapshot: dict) -> str:
    """Return a short hex fingerprint of the snapshot's body schema."""
    body = snapshot.get("body")
    schema = _extract_schema(body)
    raw = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_latest_fingerprint(store_dir: str, endpoint: str) -> str | None:
    """Return the fingerprint of the most recent snapshot for an endpoint."""
    ids = list_snapshots(store_dir, endpoint)
    if not ids:
        return None
    snap = load_snapshot(store_dir, endpoint, ids[-1])
    if snap is None:
        return None
    return compute_fingerprint(snap)


def fingerprint_history(store_dir: str, endpoint: str) -> list[dict]:
    """Return a list of {snapshot_id, fingerprint} dicts for all snapshots."""
    ids = list_snapshots(store_dir, endpoint)
    if not ids:
        raise FingerprintError(f"No snapshots found for endpoint '{endpoint}'")
    results = []
    for sid in ids:
        snap = load_snapshot(store_dir, endpoint, sid)
        if snap is None:
            continue
        results.append({"snapshot_id": sid, "fingerprint": compute_fingerprint(snap)})
    return results


def detect_schema_changes(store_dir: str, endpoint: str) -> list[dict]:
    """Return entries where the fingerprint differs from the previous snapshot."""
    history = fingerprint_history(store_dir, endpoint)
    changes = []
    for i in range(1, len(history)):
        prev = history[i - 1]
        curr = history[i]
        if curr["fingerprint"] != prev["fingerprint"]:
            changes.append({
                "from_snapshot": prev["snapshot_id"],
                "to_snapshot": curr["snapshot_id"],
                "from_fingerprint": prev["fingerprint"],
                "to_fingerprint": curr["fingerprint"],
            })
    return changes
