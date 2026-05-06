"""CLI sub-commands for exporting snapshot data.

Registered by build_parser in cli.py via the 'export' sub-command.
Standalone so it can be tested in isolation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from reqwatch.export import (
    export_diff_markdown,
    export_snapshot_json,
    export_snapshots_csv,
)
from reqwatch.storage import list_snapshots, load_snapshot


def _load_two_latest(store_dir: str, endpoint: str) -> tuple[Any | None, Any | None]:
    """Return (previous, latest) snapshots for *endpoint*, or (None, None)."""
    snaps = list_snapshots(store_dir, endpoint)
    if not snaps:
        return None, None
    latest = load_snapshot(store_dir, endpoint, snaps[-1])
    previous = load_snapshot(store_dir, endpoint, snaps[-2]) if len(snaps) >= 2 else None
    return previous, latest


def cmd_export(args: Any) -> int:
    """Entry point for the 'export' CLI sub-command.

    Returns an exit code (0 = success, 1 = error).
    """
    previous, latest = _load_two_latest(args.store, args.endpoint)

    if latest is None:
        print(
            f"No snapshots found for endpoint '{args.endpoint}' in '{args.store}'.",
            file=sys.stderr,
        )
        return 1

    fmt: str = args.format.lower()

    if fmt == "json":
        output = export_snapshot_json(latest)
    elif fmt == "markdown":
        output = export_diff_markdown(previous, latest, endpoint=args.endpoint)
    elif fmt == "csv":
        snaps = list_snapshots(args.store, args.endpoint)
        all_loaded = [
            s
            for ts in snaps
            if (s := load_snapshot(args.store, args.endpoint, ts)) is not None
        ]
        output = export_snapshots_csv(all_loaded)
    else:
        print(f"Unknown format '{fmt}'. Choose json, markdown, or csv.", file=sys.stderr)
        return 1

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Exported to {args.out}")
    else:
        print(output)

    return 0


def register_export_subcommand(subparsers: Any) -> None:  # pragma: no cover
    """Attach the 'export' sub-command to an existing argparse subparsers group."""
    p = subparsers.add_parser("export", help="Export snapshots in various formats")
    p.add_argument("endpoint", help="Endpoint key to export")
    p.add_argument(
        "--format",
        choices=["json", "markdown", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    p.add_argument("--store", default=".reqwatch", help="Snapshot storage directory")
    p.add_argument("--out", default="", help="Write output to this file (default: stdout)")
    p.set_defaults(func=cmd_export)
