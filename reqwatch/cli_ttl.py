"""CLI subcommand for managing snapshot TTLs."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.snapshot_ttl import TTLError, clear_ttl, find_stale, get_ttl, set_ttl


def cmd_ttl(args: argparse.Namespace) -> None:
    store = args.store
    action = args.ttl_action

    if action == "set":
        try:
            set_ttl(store, args.endpoint, float(args.seconds))
            print(f"TTL for '{args.endpoint}' set to {args.seconds}s.")
        except TTLError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif action == "get":
        ttl = get_ttl(store, args.endpoint)
        if ttl is None:
            print(f"No TTL configured for '{args.endpoint}'.")
        else:
            print(f"{ttl}")

    elif action == "clear":
        removed = clear_ttl(store, args.endpoint)
        if removed:
            print(f"TTL for '{args.endpoint}' cleared.")
        else:
            print(f"No TTL found for '{args.endpoint}'.")

    elif action == "stale":
        stale = find_stale(store, args.endpoint)
        if not stale:
            print("No stale snapshots found.")
        else:
            out = [
                {
                    "snapshot_id": s.snapshot_id,
                    "age_seconds": round(s.age_seconds, 2),
                    "ttl_seconds": s.ttl_seconds,
                }
                for s in stale
            ]
            print(json.dumps(out, indent=2))


def register_ttl_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("ttl", help="Manage snapshot TTLs")
    p.add_argument("--store", default=".reqwatch", help="Storage directory")
    p.add_argument("endpoint", help="Endpoint name")
    sub = p.add_subparsers(dest="ttl_action", required=True)

    s = sub.add_parser("set", help="Set TTL in seconds")
    s.add_argument("seconds", type=float, help="TTL in seconds")

    sub.add_parser("get", help="Show current TTL")
    sub.add_parser("clear", help="Remove TTL")
    sub.add_parser("stale", help="List stale snapshots")

    p.set_defaults(func=cmd_ttl)
