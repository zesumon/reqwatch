"""Alert system for reqwatch — notify when breaking changes are detected."""

from __future__ import annotations

import json
import smtplib
import urllib.request
from email.message import EmailMessage
from typing import Any


class AlertError(Exception):
    """Raised when an alert fails to send."""


def send_webhook(url: str, payload: dict[str, Any], timeout: int = 5) -> None:
    """POST a JSON payload to a webhook URL."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            pass
    except Exception as exc:
        raise AlertError(f"Webhook delivery failed: {exc}") from exc


def send_email(
    smtp_host: str,
    smtp_port: int,
    sender: str,
    recipient: str,
    subject: str,
    body: str,
    username: str | None = None,
    password: str | None = None,
    use_tls: bool = True,
) -> None:
    """Send a plain-text alert email via SMTP."""
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(msg)
    except Exception as exc:
        raise AlertError(f"Email delivery failed: {exc}") from exc


def build_change_payload(endpoint: str, diff_lines: list[str], timestamp: str) -> dict[str, Any]:
    """Build a structured payload describing detected changes."""
    return {
        "event": "reqwatch.change_detected",
        "endpoint": endpoint,
        "timestamp": timestamp,
        "diff": diff_lines,
        "summary": f"{len(diff_lines)} diff line(s) detected for {endpoint}",
    }
