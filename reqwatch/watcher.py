"""Core watch loop: fetch, snapshot, diff, and report changes."""

from __future__ import annotations

from typing import Callable

from reqwatch.fetcher import fetch_response
from reqwatch.storage import save_snapshot, load_snapshot, list_snapshots
from reqwatch.diff import diff_snapshots, has_changes, format_diff


def watch_endpoint(
    name: str,
    url: str,
    store_dir: str = ".reqwatch",
    method: str = "GET",
    headers: dict | None = None,
    body=None,
    on_change: Callable[[str, list], None] | None = None,
) -> dict:
    """Fetch *url*, persist snapshot, diff against previous run.

    Returns a result dict with keys: snapshot, diff, changed.
    """
    snapshot = fetch_response(url, method=method, headers=headers, body=body)
    save_snapshot(store_dir, name, snapshot)

    snapshots = list_snapshots(store_dir, name)
    if len(snapshots) < 2:
        return {"snapshot": snapshot, "diff": [], "changed": False}

    prev_ts, curr_ts = snapshots[-2], snapshots[-1]
    prev = load_snapshot(store_dir, name, prev_ts)
    curr = load_snapshot(store_dir, name, curr_ts)

    changes = diff_snapshots(prev, curr) if prev and curr else []
    changed = has_changes(changes)

    if changed and on_change:
        on_change(name, changes)

    return {"snapshot": snapshot, "diff": changes, "changed": changed}


def default_change_handler(name: str, changes: list) -> None:
    """Print a human-readable diff to stdout."""
    print(f"[reqwatch] Changes detected for '{name}':")
    print(format_diff(changes))
