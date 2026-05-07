"""CLI sub-command: search snapshots."""

from __future__ import annotations

import json
import sys

from reqwatch.snapshot_search import SearchError, search_snapshots


def cmd_search(args, store_dir: str = ".") -> None:
    """Execute the *search* sub-command."""
    kwargs: dict = {"limit": args.limit}

    if args.text:
        kwargs["text"] = args.text
    if args.status is not None:
        kwargs["status_code"] = args.status
    if args.has_error is not None:
        kwargs["has_error"] = args.has_error

    try:
        results = search_snapshots(store_dir, args.endpoint, **kwargs)
    except SearchError as exc:
        print(f"search error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("No matching snapshots found.")
        return

    print(json.dumps(results, indent=2, default=str))


def register_search_subcommand(subparsers) -> None:
    """Attach the *search* sub-command to *subparsers*."""
    p = subparsers.add_parser(
        "search",
        help="search stored snapshots by body text, status code, or error state",
    )
    p.add_argument("endpoint", help="endpoint key to search")
    p.add_argument("--text", default=None, help="substring to find in response body")
    p.add_argument(
        "--status", type=int, default=None, metavar="CODE",
        help="filter by exact HTTP status code",
    )
    error_group = p.add_mutually_exclusive_group()
    error_group.add_argument(
        "--errors-only", dest="has_error", action="store_true", default=None,
        help="only show snapshots that recorded an error",
    )
    error_group.add_argument(
        "--no-errors", dest="has_error", action="store_false",
        help="only show snapshots without errors",
    )
    p.add_argument(
        "--limit", type=int, default=50,
        help="maximum number of results (default: 50)",
    )
    p.set_defaults(func=cmd_search)
