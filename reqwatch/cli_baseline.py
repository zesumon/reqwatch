"""CLI sub-commands for baseline management: pin, show, clear."""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, _SubParsersAction

from reqwatch.baseline import (
    BaselineError,
    baseline_exists,
    clear_baseline,
    load_baseline,
    save_baseline,
)
from reqwatch.storage import list_snapshots, load_snapshot


def cmd_baseline(args) -> int:  # noqa: ANN001
    store_dir: str = args.store_dir
    key: str = args.endpoint_key

    if args.baseline_action == "pin":
        snapshots = list_snapshots(store_dir, key)
        if not snapshots:
            print(f"[baseline] No snapshots found for '{key}'.", file=sys.stderr)
            return 1
        latest_ts = sorted(snapshots)[-1]
        snapshot = load_snapshot(store_dir, key, latest_ts)
        if snapshot is None:
            print("[baseline] Could not load latest snapshot.", file=sys.stderr)
            return 1
        try:
            path = save_baseline(store_dir, key, snapshot)
            print(f"[baseline] Pinned snapshot {latest_ts} as baseline → {path}")
        except BaselineError as exc:
            print(f"[baseline] Error: {exc}", file=sys.stderr)
            return 1

    elif args.baseline_action == "show":
        try:
            bl = load_baseline(store_dir, key)
        except BaselineError as exc:
            print(f"[baseline] Error: {exc}", file=sys.stderr)
            return 1
        if bl is None:
            print(f"[baseline] No baseline set for '{key}'.")
            return 0
        print(json.dumps(bl, indent=2))

    elif args.baseline_action == "clear":
        removed = clear_baseline(store_dir, key)
        if removed:
            print(f"[baseline] Baseline cleared for '{key}'.")
        else:
            print(f"[baseline] No baseline found for '{key}'.")

    return 0


def register_baseline_subcommand(subparsers: _SubParsersAction) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "baseline", help="Manage pinned baselines for an endpoint"
    )
    p.add_argument("endpoint_key", help="Endpoint key (URL or label)")
    p.add_argument(
        "baseline_action",
        choices=["pin", "show", "clear"],
        help="Action to perform on the baseline",
    )
    p.add_argument(
        "--store-dir",
        dest="store_dir",
        default=".reqwatch",
        help="Directory where snapshots are stored",
    )
    p.set_defaults(func=cmd_baseline)
