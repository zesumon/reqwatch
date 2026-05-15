"""cli_chain.py — CLI subcommand for snapshot chain inspection."""

from __future__ import annotations

import json
import sys

from reqwatch.snapshot_chain import ChainError, build_chain, summarize_chain


def cmd_chain(args) -> None:
    store_dir: str = args.store
    endpoint: str = args.endpoint
    summarize: bool = getattr(args, "summarize", False)
    output_format: str = getattr(args, "format", "json")

    try:
        chain = build_chain(store_dir, endpoint)
    except ChainError as exc:
        print(f"chain error: {exc}", file=sys.stderr)
        sys.exit(1)

    data = summarize_chain(chain)

    if summarize:
        summary = {
            "endpoint": data["endpoint"],
            "total_snapshots": data["total_snapshots"],
            "total_changes": data["total_changes"],
            "stability_pct": data["stability_pct"],
        }
        print(json.dumps(summary, indent=2))
        return

    if output_format == "text":
        print(f"Chain for: {data['endpoint']}")  
        print(f"  Snapshots : {data['total_snapshots']}")
        print(f"  Changes   : {data['total_changes']}")
        print(f"  Stability : {data['stability_pct']}%")
        print()
        for lk in data["links"]:
            marker = "*" if lk["has_change"] else " "
            print(f"  [{marker}] {lk['id']}  {lk['timestamp']}  {lk['summary']}")
    else:
        print(json.dumps(data, indent=2))


def register_chain_subcommand(subparsers, common_args) -> None:
    p = subparsers.add_parser("chain", help="Show snapshot chain for an endpoint")
    common_args(p)
    p.add_argument("endpoint", help="Endpoint name / URL key")
    p.add_argument(
        "--summarize",
        action="store_true",
        default=False,
        help="Print only the summary (no per-link detail)",
    )
    p.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    p.set_defaults(func=cmd_chain)
