"""CLI sub-command: prune old snapshots."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.snapshot_prune import prune_snapshots, prune_all_endpoints, PruneError


def cmd_prune(args: argparse.Namespace) -> None:
    """Entry point for the *prune* sub-command."""
    try:
        if args.endpoint:
            deleted = prune_snapshots(
                args.store,
                args.endpoint,
                keep=args.keep,
            )
            result = {args.endpoint: deleted}
        else:
            result = prune_all_endpoints(args.store, keep=args.keep)
    except PruneError as exc:
        print(f"prune error: {exc}", file=sys.stderr)
        sys.exit(1)

    total = sum(len(v) for v in result.values())

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if total == 0:
            print("Nothing to prune.")
        else:
            for endpoint_id, timestamps in result.items():
                for ts in timestamps:
                    print(f"deleted  {endpoint_id}  {ts}")
            print(f"\n{total} snapshot(s) removed.")


def register_prune_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "prune",
        help="Remove old snapshots, keeping only the N most recent per endpoint.",
    )
    parser.add_argument(
        "--store",
        default=".reqwatch",
        help="Path to the snapshot store directory (default: .reqwatch).",
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help="Endpoint ID to prune. Omit to prune all endpoints.",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=10,
        help="Number of snapshots to keep per endpoint (default: 10).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON.",
    )
    parser.set_defaults(func=cmd_prune)
