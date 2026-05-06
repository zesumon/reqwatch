"""Configuration loader for reqwatch."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Raised for invalid configuration."""


_REQUIRED_ENDPOINT_KEYS = {"url"}
_VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"}


def _validate_endpoint(ep: Any, index: int) -> None:
    if not isinstance(ep, dict):
        raise ConfigError(f"endpoint[{index}] must be a mapping, got {type(ep).__name__}")
    missing = _REQUIRED_ENDPOINT_KEYS - ep.keys()
    if missing:
        raise ConfigError(f"endpoint[{index}] missing required keys: {missing}")
    if not isinstance(ep["url"], str) or not ep["url"].startswith(("http://", "https://")):
        raise ConfigError(f"endpoint[{index}] 'url' must be an http/https URL")
    method = ep.get("method", "GET").upper()
    if method not in _VALID_METHODS:
        raise ConfigError(f"endpoint[{index}] unsupported method '{method}'")
    headers = ep.get("headers", {})
    if not isinstance(headers, dict):
        raise ConfigError(f"endpoint[{index}] 'headers' must be a mapping")


def _validate_alerts(alerts: Any) -> None:
    """Validate the optional alerts block."""
    if not isinstance(alerts, dict):
        raise ConfigError("'alerts' must be a mapping")
    if "webhook" in alerts:
        wh = alerts["webhook"]
        if not isinstance(wh, dict) or "url" not in wh:
            raise ConfigError("alerts.webhook must have a 'url' key")
    if "email" in alerts:
        em = alerts["email"]
        for key in ("smtp_host", "sender", "recipient"):
            if key not in em:
                raise ConfigError(f"alerts.email missing required key '{key}'")


def load_config(path: str | Path) -> dict[str, Any]:
    """Load and validate a JSON config file.

    Returns the parsed config dict on success, raises ConfigError otherwise.
    """
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"Config file not found: {path}")
    try:
        raw = p.read_text(encoding="utf-8")
        config = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config: {exc}") from exc

    if not isinstance(config, dict):
        raise ConfigError("Config root must be a JSON object")

    endpoints = config.get("endpoints")
    if not endpoints:
        raise ConfigError("Config must define at least one endpoint")
    if not isinstance(endpoints, list):
        raise ConfigError("'endpoints' must be a list")

    for i, ep in enumerate(endpoints):
        _validate_endpoint(ep, i)

    if "alerts" in config:
        _validate_alerts(config["alerts"])

    return config
