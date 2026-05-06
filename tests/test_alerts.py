"""Tests for reqwatch.alerts and reqwatch.alert_handler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from reqwatch.alert_handler import AlertHandler
from reqwatch.alerts import AlertError, build_change_payload, send_webhook


# ---------------------------------------------------------------------------
# build_change_payload
# ---------------------------------------------------------------------------

def test_build_change_payload_structure():
    payload = build_change_payload("https://api.example.com", ["+foo", "-bar"], "2024-01-01T00:00:00Z")
    assert payload["event"] == "reqwatch.change_detected"
    assert payload["endpoint"] == "https://api.example.com"
    assert payload["diff"] == ["+foo", "-bar"]
    assert "2024-01-01" in payload["timestamp"]
    assert "2 diff line(s)" in payload["summary"]


# ---------------------------------------------------------------------------
# send_webhook
# ---------------------------------------------------------------------------

def test_send_webhook_posts_json():
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        send_webhook("https://hooks.example.com/test", {"key": "value"})
        mock_open.assert_called_once()
        req = mock_open.call_args[0][0]
        assert req.full_url == "https://hooks.example.com/test"
        assert req.get_header("Content-type") == "application/json"


def test_send_webhook_raises_alert_error_on_failure():
    with patch("urllib.request.urlopen", side_effect=OSError("connection refused")):
        with pytest.raises(AlertError, match="Webhook delivery failed"):
            send_webhook("https://hooks.example.com/test", {})


# ---------------------------------------------------------------------------
# AlertHandler — webhook
# ---------------------------------------------------------------------------

def test_alert_handler_calls_webhook():
    config = {"webhook": {"url": "https://hooks.example.com/abc"}}
    handler = AlertHandler(config)
    diff = {"status_code": {"old": 200, "new": 500}}

    with patch("reqwatch.alert_handler.send_webhook") as mock_wh:
        handler("https://api.example.com/v1", diff)
        mock_wh.assert_called_once()
        payload = mock_wh.call_args[0][1]
        assert payload["endpoint"] == "https://api.example.com/v1"


def test_alert_handler_silent_suppresses_webhook_error():
    config = {"webhook": {"url": "https://hooks.example.com/abc"}}
    handler = AlertHandler(config, silent=True)
    diff = {"status_code": {"old": 200, "new": 500}}

    with patch("reqwatch.alert_handler.send_webhook", side_effect=AlertError("boom")):
        # Should not raise
        handler("https://api.example.com/v1", diff)


def test_alert_handler_not_silent_raises_on_webhook_error():
    config = {"webhook": {"url": "https://hooks.example.com/abc"}}
    handler = AlertHandler(config, silent=False)
    diff = {"status_code": {"old": 200, "new": 500}}

    with patch("reqwatch.alert_handler.send_webhook", side_effect=AlertError("boom")):
        with pytest.raises(AlertError):
            handler("https://api.example.com/v1", diff)


# ---------------------------------------------------------------------------
# AlertHandler — email
# ---------------------------------------------------------------------------

def test_alert_handler_calls_email():
    config = {
        "email": {
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "sender": "a@example.com",
            "recipient": "b@example.com",
        }
    }
    handler = AlertHandler(config)
    diff = {"body.price": {"old": 10, "new": 20}}

    with patch("reqwatch.alert_handler.send_email") as mock_email:
        handler("https://api.example.com/prices", diff)
        mock_email.assert_called_once()
        kwargs = mock_email.call_args[1]
        assert "reqwatch" in kwargs["subject"]
        assert "prices" in kwargs["subject"]
