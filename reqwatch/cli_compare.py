"""CLI sub-command: compare two snapshots for an endpoint."""

from __future__ import annotations

import argparse
import json
import sys

from reqwatch.snapshot_compare import compare_snapshots, CompareError


def cmd_compare(args: argparse.Namespace) -> None:
    try:
        result = compare_snapshots(
            store_dir=args.store,
            endpoint=args.endpoint,
            ref_a=args.a,
            ref_b=args.b,
        )
    except CompareError as exc:
        print(f"[compare] error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        output = {
            "endpoint": result["endpoint"],
            "ref_a": result["ref_a"],
            "ref_b": result["ref_b"],
            "changed": result["changed"],
            "diff": result["diff"],
        }
        print(json.dumps(output, indent=2))
        return

    changed_label = "CHANGED" if result["changed"] else "no changes"
    print(f"compare  {result['ref_a']}  →  {result['ref_b']}  [{changed_label}]")
    if result["diff_lines"]:
        for line in result["diff_lines"]:
            print(line)
    else:
        print("  (responses are identical)")


def register_compare_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "compare",
        help="Compare two snapshots for an endpoint",
    )
    p.add_argument("endpoint", help="Endpoint URL or label")
    p.add_argument(
        "--a",
        default="-2",
        metavar="REF_A",
        help="First snapshot ref (index or timestamp key, default: -2)",
    )
    p.add_argument(
        "--b",
        default="-1",
        metavar="REF_B",
        help="Second snapshot ref (index or timestamp key, default: -1)",
    )
    p.add_argument(
        "--store",
        default=".reqwatch",
        help="Storage directory (default: .reqwatch)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )
    p.set_defaults(func=cmd_compare)
