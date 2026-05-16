"""CLI subcommand for snapshot lifecycle state management."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.snapshot_lifecycle import (
    LifecycleError,
    delete_state,
    get_state,
    list_by_state,
    set_state,
    transition,
    VALID_STATES,
)


def cmd_lifecycle(args: argparse.Namespace) -> None:
    store = args.store

    if args.lifecycle_cmd == "set":
        try:
            state = set_state(store, args.snapshot_id, args.state)
            print(f"Set lifecycle state of '{args.snapshot_id}' to '{state}'")
        except LifecycleError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.lifecycle_cmd == "get":
        state = get_state(store, args.snapshot_id)
        if state is None:
            print(f"No lifecycle state set for '{args.snapshot_id}'")
        else:
            print(state)

    elif args.lifecycle_cmd == "list":
        try:
            ids = list_by_state(store, args.state)
        except LifecycleError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if not ids:
            print(f"No snapshots in state '{args.state}'")
        else:
            print(json.dumps(ids, indent=2))

    elif args.lifecycle_cmd == "delete":
        removed = delete_state(store, args.snapshot_id)
        if removed:
            print(f"Removed lifecycle state for '{args.snapshot_id}'")
        else:
            print(f"No lifecycle state found for '{args.snapshot_id}'")

    elif args.lifecycle_cmd == "transition":
        try:
            new_state = transition(store, args.snapshot_id, args.from_state, args.to_state)
            print(f"Transitioned '{args.snapshot_id}' to '{new_state}'")
        except LifecycleError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


def register_lifecycle_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("lifecycle", help="Manage snapshot lifecycle states")
    p.add_argument("--store", default=".reqwatch", help="Storage directory")
    lc_sub = p.add_subparsers(dest="lifecycle_cmd", required=True)

    s = lc_sub.add_parser("set", help="Set lifecycle state")
    s.add_argument("snapshot_id")
    s.add_argument("state", choices=sorted(VALID_STATES))

    g = lc_sub.add_parser("get", help="Get lifecycle state")
    g.add_argument("snapshot_id")

    ls = lc_sub.add_parser("list", help="List snapshots by state")
    ls.add_argument("state", choices=sorted(VALID_STATES))

    d = lc_sub.add_parser("delete", help="Remove lifecycle state")
    d.add_argument("snapshot_id")

    t = lc_sub.add_parser("transition", help="Transition between states")
    t.add_argument("snapshot_id")
    t.add_argument("from_state", choices=sorted(VALID_STATES))
    t.add_argument("to_state", choices=sorted(VALID_STATES))

    p.set_defaults(func=cmd_lifecycle)
