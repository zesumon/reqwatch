"""Prune old snapshots for an endpoint, keeping only the N most recent."""

from __future__ import annotations

from typing import List

from reqwatch.storage import list_snapshots, get_snapshot_path


class PruneError(Exception):
    """Raised when pruning fails."""


def prune_snapshots(
    store_dir: str,
    endpoint_id: str,
    keep: int = 10,
) -> List[str]:
    """Delete all but the *keep* most-recent snapshots for *endpoint_id*.

    Returns a list of the deleted snapshot timestamps.

    Raises PruneError if *keep* < 1.
    """
    if keep < 1:
        raise PruneError(f"keep must be >= 1, got {keep}")

    snapshots = list_snapshots(store_dir, endpoint_id)  # newest-first
    to_delete = snapshots[keep:]

    deleted: List[str] = []
    for ts in to_delete:
        path = get_snapshot_path(store_dir, endpoint_id, ts)
        try:
            path.unlink()
            deleted.append(ts)
        except FileNotFoundError:
            pass  # already gone — not an error
        except OSError as exc:
            raise PruneError(f"Failed to delete snapshot {ts}: {exc}") from exc

    return deleted


def prune_all_endpoints(
    store_dir: str,
    keep: int = 10,
) -> dict:
    """Prune snapshots for every endpoint found under *store_dir*.

    Returns a mapping of endpoint_id -> list of deleted timestamps.
    """
    import os

    results: dict = {}
    try:
        entries = os.scandir(store_dir)
    except FileNotFoundError:
        return results

    for entry in entries:
        if entry.is_dir():
            deleted = prune_snapshots(store_dir, entry.name, keep=keep)
            if deleted:
                results[entry.name] = deleted

    return results
