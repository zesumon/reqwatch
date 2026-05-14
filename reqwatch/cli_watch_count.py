"""CLI subcommand: watch-count — view or reset endpoint watch counters."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.snapshot_watch_count import (
    WatchCountError,
    all_counts,
    get_count,
    reset,
)


def cmd_watch_count(args: argparse.Namespace) -> None:
    store_dir: str = args.store

    if args.wc_action == "list":
        counts = all_counts(store_dir)
        if not counts:
            print("No watch counts recorded yet.")
            return
        print(json.dumps(counts, indent=2))

    elif args.wc_action == "get":
        try:
            count = get_count(store_dir, args.endpoint)
        except WatchCountError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"{args.endpoint}: {count}")

    elif args.wc_action == "reset":
        try:
            reset(store_dir, args.endpoint)
        except WatchCountError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"Watch count for '{args.endpoint}' has been reset.")

    else:
        print(f"Unknown action: {args.wc_action}", file=sys.stderr)
        sys.exit(1)


def register_watch_count_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "watch-count",
        help="View or reset how many times an endpoint has been watched.",
    )
    parser.add_argument(
        "--store",
        default=".reqwatch",
        help="Path to the snapshot store directory.",
    )

    wc_sub = parser.add_subparsers(dest="wc_action", required=True)

    wc_sub.add_parser("list", help="List all endpoint watch counts.")

    get_p = wc_sub.add_parser("get", help="Get watch count for a specific endpoint.")
    get_p.add_argument("endpoint", help="Endpoint name or URL.")

    reset_p = wc_sub.add_parser("reset", help="Reset watch count for a specific endpoint.")
    reset_p.add_argument("endpoint", help="Endpoint name or URL.")

    parser.set_defaults(func=cmd_watch_count)
