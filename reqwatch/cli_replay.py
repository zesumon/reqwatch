"""CLI subcommand: replay — walk snapshot history and show change events."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.snapshot_replay import replay_endpoint, summarize_replay, ReplayError
from reqwatch.diff import format_diff


def cmd_replay(args: argparse.Namespace) -> None:
    try:
        events = replay_endpoint(
            args.store,
            args.endpoint,
            limit=args.limit,
        )
    except ReplayError as exc:
        print(f"replay error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.summarize:
        summary = summarize_replay(events)
        print(json.dumps(summary, indent=2))
        return

    if args.json:
        output = [
            {
                "index": e.index,
                "timestamp": e.timestamp,
                "changed": e.changed,
                "diff": e.diff,
            }
            for e in events
        ]
        print(json.dumps(output, indent=2))
        return

    for event in events:
        marker = "CHANGED" if event.changed else "stable"
        print(f"[{event.index:>3}] {event.timestamp}  {marker}")
        if event.changed and event.diff:
            for line in format_diff(event.diff).splitlines():
                print(f"       {line}")


def register_replay_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "replay",
        help="Walk snapshot history and show per-transition diffs",
    )
    p.add_argument("endpoint", help="Endpoint key to replay")
    p.add_argument("--store", default=".reqwatch", help="Storage directory")
    p.add_argument("--limit", type=int, default=None, help="Max snapshots to process")
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument("--summarize", action="store_true", help="Print summary stats only")
    p.set_defaults(func=cmd_replay)
