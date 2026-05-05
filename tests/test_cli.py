"""Tests for reqwatch.cli."""

import json
import pytest
from unittest.mock import patch, MagicMock

from reqwatch.cli import main, _parse_headers


# ---------------------------------------------------------------------------
# _parse_headers
# ---------------------------------------------------------------------------

def test_parse_headers_empty():
    assert _parse_headers(None) == {}
    assert _parse_headers([]) == {}


def test_parse_headers_valid():
    result = _parse_headers(["Authorization: Bearer tok", "Accept: application/json"])
    assert result == {"Authorization": "Bearer tok", "Accept": "application/json"}


def test_parse_headers_malformed_skipped(capsys):
    result = _parse_headers(["BadHeader"])
    assert result == {}
    captured = capsys.readouterr()
    assert "malformed" in captured.err


# ---------------------------------------------------------------------------
# fetch command
# ---------------------------------------------------------------------------

def test_fetch_command_prints_json(capsys):
    fake_snap = {"status": 200, "body": {"ok": True}, "error": None}
    with patch("reqwatch.cli.fetch_response", return_value=fake_snap) as mock_fetch:
        rc = main(["fetch", "https://example.com/api"])
    assert rc == 0
    mock_fetch.assert_called_once_with(
        "https://example.com/api", method="GET", headers={}, body=None
    )
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["status"] == 200


def test_fetch_command_passes_method_and_body(capsys):
    fake_snap = {"status": 201, "body": {}, "error": None}
    with patch("reqwatch.cli.fetch_response", return_value=fake_snap):
        rc = main(["fetch", "https://example.com/api", "-X", "POST", "--body", '{"x": 1}'])
    assert rc == 0


# ---------------------------------------------------------------------------
# watch command
# ---------------------------------------------------------------------------

def test_watch_first_run_exits_0(capsys):
    with patch("reqwatch.cli.watch_endpoint", return_value=None):
        rc = main(["watch", "https://example.com/api"])
    assert rc == 0
    assert "first snapshot" in capsys.readouterr().out


def test_watch_no_changes_exits_0(capsys):
    with patch("reqwatch.cli.watch_endpoint", return_value={}):
        rc = main(["watch", "https://example.com/api"])
    assert rc == 0
    assert "no changes" in capsys.readouterr().out


def test_watch_with_changes_exits_1(capsys):
    fake_diff = {"body.price": {"old": 10, "new": 20}}
    with patch("reqwatch.cli.watch_endpoint", return_value=fake_diff):
        with patch("reqwatch.cli.format_diff", return_value="body.price: 10 -> 20"):
            rc = main(["watch", "https://example.com/api"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "changes detected" in out


# ---------------------------------------------------------------------------
# list command
# ---------------------------------------------------------------------------

def test_list_no_snapshots(capsys):
    with patch("reqwatch.cli.list_snapshots", return_value=[]):
        rc = main(["list", "https://example.com/api"])
    assert rc == 0
    assert "No snapshots" in capsys.readouterr().out


def test_list_prints_timestamps(capsys):
    timestamps = ["2024-01-01T00:00:00", "2024-01-02T00:00:00"]
    with patch("reqwatch.cli.list_snapshots", return_value=timestamps):
        rc = main(["list", "https://example.com/api", "--store-dir", "/tmp/rw"])
    assert rc == 0
    out = capsys.readouterr().out
    for ts in timestamps:
        assert ts in out
