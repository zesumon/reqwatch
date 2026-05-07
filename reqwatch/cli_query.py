"""CLI subcommands for querying stored snapshots."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.snapshots_query import query_snapshots, summarize_snapshots


def cmd_query(args: argparse.Namespace) -> None:
    store_dir = args.store or "reqwatch_data"
    endpoint = args.endpoint

    snapshots = query_snapshots(
        store_dir=store_dir,
        endpoint=endpoint,
        limit=args.limit,
        since=args.since,
        until=args.until,
        status_code=args.status_code,
        has_error=args.has_error,
    )

    if not snapshots:
        print("No snapshots matched the query.", file=sys.stderr)
        return

    if args.summarize:
        summary = summarize_snapshots(snapshots)
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps(snapshots, indent=2))


def register_query_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("query", help="Query stored snapshots")
    p.add_argument("endpoint", help="Endpoint name to query")
    p.add_argument("--store", default=None, help="Storage directory")
    p.add_argument("--limit", type=int, default=None, help="Max results to return")
    p.add_argument("--since", default=None, help="ISO timestamp lower bound")
    p.add_argument("--until", default=None, help="ISO timestamp upper bound")
    p.add_argument(
        "--status-code", type=int, default=None, dest="status_code",
        help="Filter by HTTP status code"
    )
    p.add_argument(
        "--has-error", action="store_true", default=None, dest="has_error",
        help="Only return snapshots that have an error field"
    )
    p.add_argument(
        "--summarize", action="store_true",
        help="Print aggregate stats instead of full snapshots"
    )
    p.set_defaults(func=cmd_query)
