"""Formats and outputs diff reports to console or file."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from reqwatch.diff import format_diff, has_changes


ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def _colorize(text: str, color: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def format_report(
    endpoint: str,
    diff: dict,
    timestamp: Optional[str] = None,
    use_color: bool = True,
) -> str:
    """Build a human-readable report string from a diff result."""
    ts = timestamp or datetime.utcnow().isoformat()
    lines = []

    header = f"[{ts}] {endpoint}"
    if has_changes(diff):
        header += _colorize(" — changes detected", ANSI_YELLOW, use_color)
    else:
        header += _colorize(" — no changes", ANSI_GREEN, use_color)

    lines.append(_colorize(header, ANSI_BOLD, use_color))

    if has_changes(diff):
        for line in format_diff(diff):
            if line.startswith("+"):
                lines.append(_colorize(line, ANSI_GREEN, use_color))
            elif line.startswith("-"):
                lines.append(_colorize(line, ANSI_RED, use_color))
            else:
                lines.append(line)

    return "\n".join(lines)


def print_report(
    endpoint: str,
    diff: dict,
    timestamp: Optional[str] = None,
    use_color: bool = True,
    file=None,
) -> None:
    """Print a formatted report to stdout or a given file handle."""
    out = file or sys.stdout
    report = format_report(endpoint, diff, timestamp=timestamp, use_color=use_color)
    print(report, file=out)


def write_report_json(
    endpoint: str,
    diff: dict,
    output_path: str | Path,
    timestamp: Optional[str] = None,
) -> None:
    """Append a JSON report entry to a newline-delimited JSON log file."""
    ts = timestamp or datetime.utcnow().isoformat()
    entry = {
        "timestamp": ts,
        "endpoint": endpoint,
        "has_changes": has_changes(diff),
        "diff": diff,
    }
    with open(output_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
