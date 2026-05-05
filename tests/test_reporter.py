"""Tests for reqwatch.reporter."""

import json
from pathlib import Path

import pytest

from reqwatch.reporter import (
    format_report,
    print_report,
    write_report_json,
)


EMPTY_DIFF = {}
SAMPLE_DIFF = {
    "status_code": {"old": 200, "new": 404},
    "body.message": {"old": "ok", "new": "not found"},
}


def test_format_report_no_changes_contains_endpoint():
    report = format_report("https://api.example.com/v1", EMPTY_DIFF, use_color=False)
    assert "https://api.example.com/v1" in report
    assert "no changes" in report


def test_format_report_with_changes_shows_changes_detected():
    report = format_report("https://api.example.com/v1", SAMPLE_DIFF, use_color=False)
    assert "changes detected" in report


def test_format_report_with_changes_includes_diff_lines():
    report = format_report("https://api.example.com/v1", SAMPLE_DIFF, use_color=False)
    assert "status_code" in report
    assert "body.message" in report


def test_format_report_custom_timestamp():
    report = format_report(
        "https://api.example.com",
        EMPTY_DIFF,
        timestamp="2024-01-01T00:00:00",
        use_color=False,
    )
    assert "2024-01-01T00:00:00" in report


def test_format_report_with_color_contains_ansi():
    report = format_report("https://api.example.com", SAMPLE_DIFF, use_color=True)
    assert "\033[" in report


def test_print_report_writes_to_file(tmp_path):
    out_file = tmp_path / "report.txt"
    with open(out_file, "w") as fh:
        print_report(
            "https://api.example.com",
            SAMPLE_DIFF,
            timestamp="2024-06-01T12:00:00",
            use_color=False,
            file=fh,
        )
    content = out_file.read_text()
    assert "changes detected" in content
    assert "https://api.example.com" in content


def test_write_report_json_creates_file(tmp_path):
    log_file = tmp_path / "log.jsonl"
    write_report_json(
        "https://api.example.com",
        SAMPLE_DIFF,
        log_file,
        timestamp="2024-06-01T12:00:00",
    )
    assert log_file.exists()


def test_write_report_json_valid_json_entry(tmp_path):
    log_file = tmp_path / "log.jsonl"
    write_report_json("https://api.example.com", SAMPLE_DIFF, log_file)
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["endpoint"] == "https://api.example.com"
    assert entry["has_changes"] is True
    assert "diff" in entry
    assert "timestamp" in entry


def test_write_report_json_appends_multiple_entries(tmp_path):
    log_file = tmp_path / "log.jsonl"
    write_report_json("https://api.example.com", EMPTY_DIFF, log_file)
    write_report_json("https://api.example.com", SAMPLE_DIFF, log_file)
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["has_changes"] is False
    assert second["has_changes"] is True
