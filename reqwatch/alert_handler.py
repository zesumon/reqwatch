"""High-level alert handler wired into the watcher change callback."""

from __future__ import annotations

import datetime
from typing import Any

from reqwatch.alerts import AlertError, build_change_payload, send_email, send_webhook
from reqwatch.diff import format_diff


class AlertHandler:
    """Dispatches alerts when changes are detected.

    Configure via a dict that matches the ``alerts`` section of a config file::

        {
            "webhook": {"url": "https://hooks.example.com/abc"},
            "email": {
                "smtp_host": "smtp.example.com",
                "smtp_port": 587,
                "sender": "reqwatch@example.com",
                "recipient": "ops@example.com",
                "username": "reqwatch@example.com",
                "password": "secret",
            },
        }
    """

    def __init__(self, config: dict[str, Any], silent: bool = False) -> None:
        self._config = config
        self._silent = silent  # suppress exceptions — log only

    def __call__(self, endpoint: str, diff: dict[str, Any]) -> None:
        """Invoked by watcher when a change is detected."""
        diff_lines = format_diff(diff).splitlines()
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        payload = build_change_payload(endpoint, diff_lines, timestamp)

        if "webhook" in self._config:
            self._dispatch_webhook(payload)

        if "email" in self._config:
            self._dispatch_email(endpoint, diff_lines, timestamp)

    def _dispatch_webhook(self, payload: dict[str, Any]) -> None:
        cfg = self._config["webhook"]
        try:
            send_webhook(cfg["url"], payload, timeout=cfg.get("timeout", 5))
        except AlertError as exc:
            if not self._silent:
                raise
            print(f"[reqwatch] webhook alert error: {exc}")

    def _dispatch_email(self, endpoint: str, diff_lines: list[str], timestamp: str) -> None:
        cfg = self._config["email"]
        subject = f"[reqwatch] change detected — {endpoint}"
        body = "\n".join([f"Timestamp: {timestamp}", ""] + diff_lines)
        try:
            send_email(
                smtp_host=cfg["smtp_host"],
                smtp_port=cfg.get("smtp_port", 587),
                sender=cfg["sender"],
                recipient=cfg["recipient"],
                subject=subject,
                body=body,
                username=cfg.get("username"),
                password=cfg.get("password"),
                use_tls=cfg.get("use_tls", True),
            )
        except AlertError as exc:
            if not self._silent:
                raise
            print(f"[reqwatch] email alert error: {exc}")
