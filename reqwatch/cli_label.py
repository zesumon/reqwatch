"""CLI sub-commands for snapshot label management."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.snapshot_label import (
    LabelError,
    add_label,
    clear_labels,
    find_by_label,
    get_labels,
    remove_label,
)


def cmd_label(args: argparse.Namespace) -> None:  # noqa: C901
    store = args.store
    action = args.label_action

    try:
        if action == "add":
            add_label(store, args.snapshot_id, args.label)
            print(f"Label '{args.label}' added to {args.snapshot_id}.")

        elif action == "remove":
            removed = remove_label(store, args.snapshot_id, args.label)
            if removed:
                print(f"Label '{args.label}' removed from {args.snapshot_id}.")
            else:
                print(f"Label '{args.label}' not found on {args.snapshot_id}.")

        elif action == "list":
            labels = get_labels(store, args.snapshot_id)
            if labels:
                print(json.dumps(labels, indent=2))
            else:
                print(f"No labels on {args.snapshot_id}.")

        elif action == "find":
            ids = find_by_label(store, args.label)
            if ids:
                print(json.dumps(ids, indent=2))
            else:
                print(f"No snapshots carry label '{args.label}'.")

        elif action == "clear":
            clear_labels(store, args.snapshot_id)
            print(f"All labels cleared from {args.snapshot_id}.")

    except LabelError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def register_label_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("label", help="manage snapshot labels")
    p.add_argument("--store", default=".reqwatch", help="storage directory")
    sub = p.add_subparsers(dest="label_action", required=True)

    for name in ("add", "remove", "list", "clear"):
        s = sub.add_parser(name)
        s.add_argument("snapshot_id")
        if name in ("add", "remove"):
            s.add_argument("label")

    find_p = sub.add_parser("find")
    find_p.add_argument("label")

    p.set_defaults(func=cmd_label)
