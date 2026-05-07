"""CLI subcommands for snapshot tag management."""

from __future__ import annotations

import argparse
import sys

from reqwatch.tags import (
    TagError,
    add_tag,
    clear_tags,
    find_by_tag,
    get_tags,
    remove_tag,
)


def cmd_tags(args: argparse.Namespace) -> None:
    store_dir: str = args.store

    if args.tag_action == "add":
        try:
            add_tag(store_dir, args.snapshot_id, args.tag)
            print(f"Tag '{args.tag}' added to snapshot '{args.snapshot_id}'.")
        except TagError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.tag_action == "remove":
        remove_tag(store_dir, args.snapshot_id, args.tag)
        print(f"Tag '{args.tag}' removed from snapshot '{args.snapshot_id}'.")

    elif args.tag_action == "list":
        tags = get_tags(store_dir, args.snapshot_id)
        if tags:
            print("\n".join(tags))
        else:
            print(f"No tags for snapshot '{args.snapshot_id}'.")

    elif args.tag_action == "find":
        ids = find_by_tag(store_dir, args.tag)
        if ids:
            print("\n".join(ids))
        else:
            print(f"No snapshots found with tag '{args.tag}'.")

    elif args.tag_action == "clear":
        clear_tags(store_dir, args.snapshot_id)
        print(f"All tags cleared for snapshot '{args.snapshot_id}'.")


def register_tags_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("tags", help="Manage snapshot tags")
    parser.add_argument(
        "--store", default=".reqwatch", help="Storage directory (default: .reqwatch)"
    )
    tag_sub = parser.add_subparsers(dest="tag_action", required=True)

    for action in ("add", "remove", "list", "clear"):
        p = tag_sub.add_parser(action)
        p.add_argument("snapshot_id", help="Snapshot identifier")
        if action in ("add", "remove"):
            p.add_argument("tag", help="Tag string")

    p_find = tag_sub.add_parser("find")
    p_find.add_argument("tag", help="Tag to search for")

    parser.set_defaults(func=cmd_tags)
