"""Tests for reqwatch.export."""

from __future__ import annotations

import json

import pytest

from reqwatch.export import (
    export_diff_markdown,
    export_snapshot_json,
    export_snapshots_csv,
)


@pytest.fixture()
def base_snapshot():
    return {
        "timestamp": "2024-01-01T00:00:00",
        "url": "https://api.example.com/v1/status",
        "status": 200,
        "body": {"version": "1.0", "healthy": True},
        "error": None,
    }


@pytest.fixture()
def changed_snapshot(base_snapshot):
    snap = dict(base_snapshot)
    snap["body"] = {"version": "2.0", "healthy": True}
    snap["timestamp"] = "2024-01-02T00:00:00"
    return snap


# --- export_snapshot_json ---

def test_export_snapshot_json_is_valid_json(base_snapshot):
    result = export_snapshot_json(base_snapshot)
    parsed = json.loads(result)
    assert parsed["status"] == 200
    assert parsed["url"] == base_snapshot["url"]


def test_export_snapshot_json_respects_indent(base_snapshot):
    compact = export_snapshot_json(base_snapshot, indent=0)
    pretty = export_snapshot_json(base_snapshot, indent=4)
    assert len(pretty) > len(compact)


def test_export_snapshot_json_preserves_all_fields(base_snapshot):
    """Ensure no fields are dropped or added during serialisation."""
    result = export_snapshot_json(base_snapshot)
    parsed = json.loads(result)
    assert set(parsed.keys()) == set(base_snapshot.keys())


# --- export_diff_markdown ---

def test_export_diff_markdown_no_old_returns_baseline_note(base_snapshot):
    result = export_diff_markdown(None, base_snapshot, endpoint="/status")
    assert "baseline" in result.lower()
    assert "/status" in result


def test_export_diff_markdown_no_changes(base_snapshot):
    result = export_diff_markdown(base_snapshot, base_snapshot, endpoint="/status")
    assert "No changes" in result
    assert "✅" in result


def test_export_diff_markdown_with_changes(base_snapshot, changed_snapshot):
    result = export_diff_markdown(base_snapshot, changed_snapshot, endpoint="/status")
    assert "Changes detected" in result
    assert "```diff" in result
    assert "version" in result


def test_export_diff_markdown_no_endpoint_omits_dash(base_snapshot):
    result = export_diff_markdown(base_snapshot, base_snapshot)
    assert "—" not in result


def test_export_diff_markdown_returns_string(base_snapshot, changed_snapshot):
    """Return type should always be a plain string."""
    for old, new in [
        (None, base_snapshot),
        (base_snapshot, base_snapshot),
        (base_snapshot, changed_snapshot),
    ]:
        result = export_diff_markdown(old, new, endpoint="/status")
        assert isinstance(result, str)


# --- export_snapshots_csv ---

def test_export_snapshots_csv_header(base_snapshot):
    csv_text = export_snapshots_csv([base_snapshot])
    first_line = csv_text.splitlines()[0]
    assert "timestamp" in first_line
    assert "status" in first_line


def test_export_snapshots_csv_row_count(base_snapshot, changed_snapshot):
    csv_text = export_snapshots_csv([base_snapshot, changed_snapshot])
    rows = [l for l in csv_text.splitlines() if l.strip()]
    assert len(rows) == 3  # header + 2 data rows


def test_export_snapshots_csv_empty():
    csv_text = export_snapshots_csv([])
    rows = [l for l in csv_text.splitlines() if l.strip()]
    assert len(rows) == 1  # header only


def test_export_snapshots_csv_error_field():
    snap = {
        "timestamp": "2024-01-01T00:00:00",
        "url": "https://api.example.com",
        "status": None,
        "error": "Connection refused",
    }
    csv_text = export_snapshots_csv([snap])
    assert "Connection refused" in csv_text
