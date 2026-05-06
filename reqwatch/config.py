"""Load and validate reqwatch endpoint configuration from a TOML or JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore[no-reattr]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


REQUIRED_ENDPOINT_KEYS = {"name", "url"}


class ConfigError(ValueError):
    """Raised when the configuration file is invalid."""


def _validate_endpoint(ep: Any, idx: int) -> None:
    if not isinstance(ep, dict):
        raise ConfigError(f"endpoint[{idx}] must be a mapping, got {type(ep).__name__}")
    missing = REQUIRED_ENDPOINT_KEYS - ep.keys()
    if missing:
        raise ConfigError(f"endpoint[{idx}] missing required keys: {missing}")
    interval = ep.get("interval")
    if interval is not None and (not isinstance(interval, (int, float)) or interval <= 0):
        raise ConfigError(f"endpoint[{idx}] 'interval' must be a positive number")


def load_config(path: str | Path) -> dict:
    """Load a .toml or .json config file and return the parsed dict.

    Expected shape::

        [[endpoints]]
        name = "httpbin-get"
        url  = "https://httpbin.org/get"
        method   = "GET"          # optional, default GET
        interval = 60             # optional, seconds between polls
        headers  = {}             # optional
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
    elif suffix == ".toml":
        if tomllib is None:
            raise ConfigError("TOML support requires Python 3.11+ or 'tomli' package")
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    else:
        raise ConfigError(f"Unsupported config format: '{suffix}' (use .json or .toml)")

    endpoints = raw.get("endpoints", [])
    if not isinstance(endpoints, list):
        raise ConfigError("'endpoints' must be a list")
    for idx, ep in enumerate(endpoints):
        _validate_endpoint(ep, idx)

    return raw
