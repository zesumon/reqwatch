"""Computes and formats diffs between two API response snapshots."""

from typing import Any


def _flatten(obj: Any, prefix: str = "") -> dict:
    """Recursively flatten a nested dict/list into dot-notation keys."""
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            items.update(_flatten(v, full_key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            full_key = f"{prefix}[{i}]"
            items.update(_flatten(v, full_key))
    else:
        items[prefix] = obj
    return items


def diff_snapshots(old: dict, new: dict) -> dict:
    """Compare two snapshots and return a structured diff.

    Args:
        old: Previously stored snapshot dict.
        new: Freshly captured snapshot dict.

    Returns:
        A dict with keys: 'status_changed', 'added', 'removed', 'changed'.
    """
    result = {
        "status_changed": None,
        "added": {},
        "removed": {},
        "changed": {},
    }

    if old.get("status_code") != new.get("status_code"):
        result["status_changed"] = {
            "from": old.get("status_code"),
            "to": new.get("status_code"),
        }

    old_body = _flatten(old.get("body") or {})
    new_body = _flatten(new.get("body") or {})

    old_keys = set(old_body.keys())
    new_keys = set(new_body.keys())

    result["removed"] = {k: old_body[k] for k in old_keys - new_keys}
    result["added"] = {k: new_body[k] for k in new_keys - old_keys}

    for k in old_keys & new_keys:
        if old_body[k] != new_body[k]:
            result["changed"][k] = {"from": old_body[k], "to": new_body[k]}

    return result


def has_changes(diff: dict) -> bool:
    """Return True if the diff contains any meaningful differences."""
    return bool(
        diff.get("status_changed")
        or diff.get("added")
        or diff.get("removed")
        or diff.get("changed")
    )


def format_diff(diff: dict) -> str:
    """Render a human-readable summary of a diff."""
    lines = []
    if diff.get("status_changed"):
        sc = diff["status_changed"]
        lines.append(f"  [STATUS] {sc['from']} → {sc['to']}")
    for k, v in diff.get("added", {}).items():
        lines.append(f"  [+] {k}: {v!r}")
    for k, v in diff.get("removed", {}).items():
        lines.append(f"  [-] {k}: {v!r}")
    for k, info in diff.get("changed", {}).items():
        lines.append(f"  [~] {k}: {info['from']!r} → {info['to']!r}")
    return "\n".join(lines) if lines else "  (no changes)"
