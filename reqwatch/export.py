"""Export snapshots and diff reports to various formats (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from reqwatch.diff import diff_snapshots, format_diff, has_changes


def export_snapshot_json(snapshot: dict[str, Any], indent: int = 2) -> str:
    """Serialise a raw snapshot dict to a JSON string."""
    return json.dumps(snapshot, indent=indent, default=str)


def export_diff_markdown(
    old: dict[str, Any] | None,
    new: dict[str, Any],
    endpoint: str = "",
) -> str:
    """Return a Markdown-formatted diff report for two snapshots."""
    lines: list[str] = []
    title = "## ReqWatch diff report"
    if endpoint:
        title += f" — `{endpoint}`"
    lines.append(title)
    lines.append("")

    if old is None:
        lines.append("_No previous snapshot — this is the baseline._")
        return "\n".join(lines)

    diff = diff_snapshots(old, new)
    if not has_changes(diff):
        lines.append("✅ No changes detected.")
    else:
        lines.append("⚠️ Changes detected:")
        lines.append("")
        lines.append("```diff")
        for line in format_diff(diff):
            lines.append(line)
        lines.append("```")
    return "\n".join(lines)


def export_snapshots_csv(snapshots: list[dict[str, Any]]) -> str:
    """Flatten a list of snapshots into a CSV string with key columns."""
    fieldnames = ["timestamp", "url", "status", "error"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for snap in snapshots:
        writer.writerow(
            {
                "timestamp": snap.get("timestamp", ""),
                "url": snap.get("url", ""),
                "status": snap.get("status", ""),
                "error": snap.get("error") or "",
            }
        )
    return buf.getvalue()
