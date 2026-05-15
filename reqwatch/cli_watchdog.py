"""CLI subcommand: watchdog — check for stale / silent endpoints."""
from __future__ import annotations

import argparse
import json
import sys

from reqwatch.snapshot_watchdog import WatchdogError, run_watchdog


def cmd_watchdog(args: argparse.Namespace) -> None:
    endpoints: list[str] = args.endpoints
    if not endpoints:
        print("watchdog: no endpoints specified", file=sys.stderr)
        sys.exit(1)

    try:
        report = run_watchdog(
            store_dir=args.store,
            endpoints=endpoints,
            threshold_seconds=args.threshold,
        )
    except WatchdogError as exc:
        print(f"watchdog error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.summarize:
        print(f"Checked {len(report.results)} endpoint(s) at {report.checked_at:.0f}")
        print(f"  Stale  : {len(report.stale)}")
        print(f"  Silent : {len(report.silent)}")
        for r in report.results:
            age_str = f"{r.age_seconds:.1f}s" if r.age_seconds is not None else "N/A"
            flags = []
            if r.is_silent:
                flags.append("SILENT")
            elif r.is_stale:
                flags.append("STALE")
            else:
                flags.append("ok")
            print(f"  {r.endpoint}  age={age_str}  [{', '.join(flags)}]")
    else:
        print(json.dumps(report.to_dict(), indent=2))

    if report.stale or report.silent:
        sys.exit(2)  # non-zero so CI pipelines can react


def register_watchdog_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "watchdog",
        help="detect stale or silent endpoints",
    )
    p.add_argument(
        "endpoints",
        nargs="+",
        metavar="ENDPOINT",
        help="endpoint name(s) to check",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=3600.0,
        metavar="SECONDS",
        help="age threshold in seconds (default: 3600)",
    )
    p.add_argument(
        "--summarize",
        action="store_true",
        help="print a human-readable summary instead of JSON",
    )
    p.set_defaults(func=cmd_watchdog)
