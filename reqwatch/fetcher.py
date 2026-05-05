"""HTTP fetching utilities for reqwatch."""

import time
from datetime import datetime, timezone
from typing import Any

import requests


DEFAULT_TIMEOUT = 10


def fetch_response(url: str, method: str = "GET", headers: dict | None = None,
                   body: Any = None, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Fetch an HTTP response and return a structured snapshot dict."""
    method = method.upper()
    kwargs: dict = {"timeout": timeout, "headers": headers or {}}

    if body is not None:
        kwargs["json"] = body

    start = time.monotonic()
    try:
        resp = requests.request(method, url, **kwargs)
        elapsed = round(time.monotonic() - start, 4)
        try:
            response_body = resp.json()
        except ValueError:
            response_body = resp.text

        return {
            "url": url,
            "method": method,
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": response_body,
            "elapsed_seconds": elapsed,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
    except requests.RequestException as exc:
        elapsed = round(time.monotonic() - start, 4)
        return {
            "url": url,
            "method": method,
            "status_code": None,
            "headers": {},
            "body": None,
            "elapsed_seconds": elapsed,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
        }
