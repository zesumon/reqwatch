"""Redact sensitive fields from snapshot bodies before storage or display."""

from __future__ import annotations

from typing import Any

DEFAULT_REDACT_PLACEHOLDER = "**REDACTED**"


class RedactError(ValueError):
    pass


def _redact_nested(obj: Any, keys: list[str], placeholder: str) -> Any:
    """Recursively walk *obj* and replace matching keys with *placeholder*."""
    if isinstance(obj, dict):
        return {
            k: placeholder if k in keys else _redact_nested(v, keys, placeholder)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact_nested(item, keys, placeholder) for item in obj]
    return obj


def redact_snapshot(snapshot: dict, keys: list[str], placeholder: str = DEFAULT_REDACT_PLACEHOLDER) -> dict:
    """Return a *copy* of *snapshot* with sensitive keys redacted from the body.

    Parameters
    ----------
    snapshot:
        A snapshot dict as produced by ``fetcher.fetch_response``.
    keys:
        List of field names to redact (matched at any nesting level).
    placeholder:
        Replacement value for redacted fields.

    Returns
    -------
    dict
        New snapshot dict; the original is not mutated.
    """
    if not isinstance(snapshot, dict):
        raise RedactError("snapshot must be a dict")
    if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
        raise RedactError("keys must be a list of strings")

    result = dict(snapshot)
    body = result.get("body")
    if body is not None:
        result["body"] = _redact_nested(body, keys, placeholder)
    return result


def redact_keys_from_config(endpoint_cfg: dict) -> list[str]:
    """Extract the ``redact`` key list from an endpoint config dict.

    Returns an empty list when no redact config is present.
    """
    raw = endpoint_cfg.get("redact", [])
    if not isinstance(raw, list):
        raise RedactError("'redact' in endpoint config must be a list")
    return [str(k) for k in raw]
