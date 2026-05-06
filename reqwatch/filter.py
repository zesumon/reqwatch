"""Response filtering: include/exclude keys from snapshots before diffing."""

from typing import Any, Dict, List, Optional


class FilterError(Exception):
    pass


def _nested_delete(data: Any, key_path: List[str]) -> Any:
    """Remove a nested key from a dict/list structure by dot-separated path parts."""
    if not key_path or not isinstance(data, dict):
        return data
    head, *tail = key_path
    if head not in data:
        return data
    if not tail:
        result = dict(data)
        del result[head]
        return result
    result = dict(data)
    result[head] = _nested_delete(data[head], tail)
    return result


def _nested_pick(data: Any, key_path: List[str]) -> Any:
    """Traverse a nested structure and return the value at key_path."""
    if not key_path:
        return data
    head, *tail = key_path
    if not isinstance(data, dict) or head not in data:
        return None
    return _nested_pick(data[head], tail)


def apply_exclude(body: Any, exclude_keys: List[str]) -> Any:
    """Remove each key (dot-separated) from body recursively."""
    result = body
    for key in exclude_keys:
        parts = key.split(".")
        result = _nested_delete(result, parts)
    return result


def apply_include(body: Any, include_keys: List[str]) -> Optional[Dict]:
    """Return a new dict containing only the specified keys (dot-separated)."""
    if not isinstance(body, dict):
        raise FilterError("include_keys requires the response body to be a JSON object")
    result: Dict[str, Any] = {}
    for key in include_keys:
        parts = key.split(".")
        value = _nested_pick(body, parts)
        if value is not None:
            # Rebuild nested structure for the picked key
            node = result
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = value
    return result


def filter_body(
    body: Any,
    include_keys: Optional[List[str]] = None,
    exclude_keys: Optional[List[str]] = None,
) -> Any:
    """Apply include and/or exclude filters to a response body."""
    if include_keys:
        body = apply_include(body, include_keys)
    if exclude_keys:
        body = apply_exclude(body, exclude_keys)
    return body
