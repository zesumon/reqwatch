"""CLI subcommand for pinning/unpinning snapshots."""

from __future__ import annotations

import argparse
import sys

from reqwatch.snapshot_pin import (
    PinError,
    is_pinned,
    list_pinned,
    pin_snapshot,
    unpin_snapshot,
)


def cmd_pin(args: argparse.Namespace) -> None:
    store = args.store
    endpoint = args.endpoint

    if args.pin_action == "add":
        try:
            pin_snapshot(store, endpoint, args.timestamp)
            print(f"Pinned {args.timestamp}")
        except PinError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.pin_action == "remove":
        try:
            unpin_snapshot(store, endpoint, args.timestamp)
            print(f"Unpinned {args.timestamp}")
        except PinError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.pin_action == "list":
        pins = list_pinned(store, endpoint)
        if not pins:
            print("No pinned snapshots.")
        else:
            for ts in pins:
                print(ts)

    elif args.pin_action == "check":
        result = is_pinned(store, endpoint, args.timestamp)
        print("pinned" if result else "not pinned")


def register_pin_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("pin", help="pin or unpin snapshots")
    parser.add_argument("--store", default=".reqwatch", help="storage directory")
    parser.add_argument("--endpoint", required=True, help="endpoint name")

    sub = parser.add_subparsers(dest="pin_action", required=True)

    p_add = sub.add_parser("add", help="pin a snapshot")
    p_add.add_argument("timestamp", help="snapshot timestamp to pin")

    p_remove = sub.add_parser("remove", help="unpin a snapshot")
    p_remove.add_argument("timestamp", help="snapshot timestamp to unpin")

    sub.add_parser("list", help="list pinned snapshots")

    p_check = sub.add_parser("check", help="check if a snapshot is pinned")
    p_check.add_argument("timestamp", help="snapshot timestamp to check")

    parser.set_defaults(func=cmd_pin)
