"""CLI subcommand for managing snapshot groups."""

from __future__ import annotations

import json
import sys

from reqwatch.snapshot_group import (
    GroupError,
    add_to_group,
    get_group_members,
    latest_snapshots_for_group,
    list_groups,
    remove_from_group,
)


def cmd_group(args) -> None:
    store = args.store

    if args.group_action == "add":
        try:
            add_to_group(store, args.group, args.endpoint)
            print(f"Added '{args.endpoint}' to group '{args.group}'.")
        except GroupError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.group_action == "remove":
        removed = remove_from_group(store, args.group, args.endpoint)
        if removed:
            print(f"Removed '{args.endpoint}' from group '{args.group}'.")
        else:
            print(f"'{args.endpoint}' was not in group '{args.group}'.")

    elif args.group_action == "list":
        groups = list_groups(store)
        if not groups:
            print("No groups defined.")
        else:
            print(json.dumps(groups, indent=2))

    elif args.group_action == "members":
        try:
            members = get_group_members(store, args.group)
            print(json.dumps(members, indent=2))
        except GroupError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.group_action == "latest":
        try:
            snapshots = latest_snapshots_for_group(store, args.group)
            print(json.dumps(snapshots, indent=2))
        except GroupError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)


def register_group_subcommand(subparsers, common) -> None:
    p = subparsers.add_parser("group", parents=[common], help="Manage endpoint groups")
    sub = p.add_subparsers(dest="group_action", required=True)

    add_p = sub.add_parser("add", help="Add endpoint to a group")
    add_p.add_argument("group")
    add_p.add_argument("endpoint")

    rem_p = sub.add_parser("remove", help="Remove endpoint from a group")
    rem_p.add_argument("group")
    rem_p.add_argument("endpoint")

    sub.add_parser("list", help="List all groups")

    mem_p = sub.add_parser("members", help="List members of a group")
    mem_p.add_argument("group")

    lat_p = sub.add_parser("latest", help="Get latest snapshot per group member")
    lat_p.add_argument("group")

    p.set_defaults(func=cmd_group)
