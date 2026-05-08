"""Merge two snapshots into a single combined snapshot.

Useful for combining partial API responses or stitching together
paginated results captured at different times.
"""

from __future__ import annotations

from typing import Any

from reqwatch.storage import load_snapshot, save_snapshot


class MergeError(Exception):
    """Raised when a merge operation cannot be completed."""


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*, returning a new dict.

    Nested dicts are merged recursively; all other types are replaced by
    the value from *override*.
    """
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def merge_snapshots(
    snap_a: dict[str, Any],
    snap_b: dict[str, Any],
    *,
    prefer: str = "b",
) -> dict[str, Any]:
    """Return a new snapshot whose *body* is the deep-merge of *snap_a* and *snap_b*.

    ``prefer`` controls which snapshot wins on scalar conflicts:
    - ``"b"`` (default): values from *snap_b* overwrite *snap_a*.
    - ``"a"``: values from *snap_a* overwrite *snap_b*.

    Metadata (url, status, headers, timestamp) is taken from *snap_b* by default
    or from *snap_a* when ``prefer="a"``.

    Raises ``MergeError`` if either snapshot body is not a dict.
    """
    if prefer not in ("a", "b"):
        raise MergeError(f"prefer must be 'a' or 'b', got {prefer!r}")

    body_a = snap_a.get("body")
    body_b = snap_b.get("body")

    if not isinstance(body_a, dict) or not isinstance(body_b, dict):
        raise MergeError(
            "Both snapshot bodies must be dicts to perform a deep merge; "
            f"got {type(body_a).__name__} and {type(body_b).__name__}."
        )

    if prefer == "b":
        merged_body = _deep_merge(body_a, body_b)
        meta_source = snap_b
    else:
        merged_body = _deep_merge(body_b, body_a)
        meta_source = snap_a

    return {
        "url": meta_source.get("url"),
        "status": meta_source.get("status"),
        "headers": meta_source.get("headers", {}),
        "body": merged_body,
        "timestamp": meta_source.get("timestamp"),
        "error": meta_source.get("error"),
    }


def merge_and_save(
    store_dir: str,
    endpoint: str,
    ref_a: str,
    ref_b: str,
    *,
    prefer: str = "b",
) -> dict[str, Any]:
    """Load two snapshots by timestamp refs, merge them, and save the result.

    Returns the merged snapshot dict.
    Raises ``MergeError`` if either ref cannot be found.
    """
    snap_a = load_snapshot(store_dir, endpoint, ref_a)
    snap_b = load_snapshot(store_dir, endpoint, ref_b)

    if snap_a is None:
        raise MergeError(f"Snapshot not found: endpoint={endpoint!r} ref={ref_a!r}")
    if snap_b is None:
        raise MergeError(f"Snapshot not found: endpoint={endpoint!r} ref={ref_b!r}")

    merged = merge_snapshots(snap_a, snap_b, prefer=prefer)
    save_snapshot(store_dir, endpoint, merged)
    return merged
