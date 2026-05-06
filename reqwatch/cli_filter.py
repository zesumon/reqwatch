"""CLI subcommand: filter — preview a filtered view of the latest snapshot for an endpoint."""

import argparse
import json
import sys

from reqwatch.storage import load_snapshot, list_snapshots
from reqwatch.filter import filter_body, FilterError


def cmd_filter(args: argparse.Namespace) -> None:
    snapshots = list_snapshots(args.store_dir, args.endpoint)
    if not snapshots:
        print(f"No snapshots found for endpoint: {args.endpoint}", file=sys.stderr)
        sys.exit(1)

    latest_ts = sorted(snapshots)[-1]
    snapshot = load_snapshot(args.store_dir, args.endpoint, latest_ts)
    if snapshot is None:
        print("Failed to load snapshot.", file=sys.stderr)
        sys.exit(1)

    body = snapshot.get("body")
    include_keys = args.include.split(",") if args.include else None
    exclude_keys = args.exclude.split(",") if args.exclude else None

    try:
        filtered = filter_body(body, include_keys=include_keys, exclude_keys=exclude_keys)
    except FilterError as exc:
        print(f"Filter error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(filtered, indent=2))


def register_filter_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "filter",
        help="Preview a filtered view of the latest snapshot for an endpoint",
    )
    parser.add_argument("endpoint", help="Endpoint label used when the snapshot was saved")
    parser.add_argument(
        "--include",
        default="",
        metavar="KEY1,KEY2",
        help="Comma-separated dot-notation keys to include (others dropped)",
    )
    parser.add_argument(
        "--exclude",
        default="",
        metavar="KEY1,KEY2",
        help="Comma-separated dot-notation keys to exclude",
    )
    parser.add_argument(
        "--store-dir",
        default=".reqwatch",
        help="Directory where snapshots are stored (default: .reqwatch)",
    )
    parser.set_defaults(func=cmd_filter)
