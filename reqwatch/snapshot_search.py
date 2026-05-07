"""Full-text and field search across stored snapshots."""

from __future__ import annotations

import json
from typing import Any

from reqwatch.storage import list_snapshots, load_snapshot


class SearchError(Exception):
    pass


def _body_contains(body: Any, text: str) -> bool:
    """Return True if *text* appears anywhere in the JSON-serialised body."""
    try:
        serialised = json.dumps(body, default=str)
    except (TypeError, ValueError):
        serialised = str(body)
    return text.lower() in serialised.lower()


def search_snapshots(
    store_dir: str,
    endpoint: str,
    *,
    text: str | None = None,
    status_code: int | None = None,
    has_error: bool | None = None,
    limit: int = 50,
) -> list[dict]:
    """Return snapshots for *endpoint* that match the given criteria.

    Parameters
    ----------
    text:
        Substring to search for inside the response body (case-insensitive).
    status_code:
        Exact HTTP status code to match.
    has_error:
        If True, only return snapshots with a non-None ``error`` field.
        If False, only return snapshots without errors.
    limit:
        Maximum number of results to return (newest first).
    """
    if limit < 1:
        raise SearchError("limit must be >= 1")

    names = list_snapshots(store_dir, endpoint)
    if not names:
        return []

    results: list[dict] = []
    for name in reversed(names):  # newest first
        if len(results) >= limit:
            break
        snap = load_snapshot(store_dir, endpoint, name)
        if snap is None:
            continue

        if status_code is not None and snap.get("status_code") != status_code:
            continue

        if has_error is True and not snap.get("error"):
            continue
        if has_error is False and snap.get("error"):
            continue

        if text is not None and not _body_contains(snap.get("body"), text):
            continue

        results.append(snap)

    return results
