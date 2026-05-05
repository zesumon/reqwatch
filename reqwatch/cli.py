"""Command-line interface for reqwatch."""

import argparse
import json
import sys
from typing import Optional

from reqwatch.fetcher import fetch_response
from reqwatch.storage import load_snapshot, list_snapshots
from reqwatch.watcher import watch_endpoint
from reqwatch.diff import format_diff


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reqwatch",
        description="Monitor HTTP endpoints and detect breaking changes.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- fetch (one-shot) ---
    fetch_p = subparsers.add_parser("fetch", help="Fetch an endpoint and print the response.")
    fetch_p.add_argument("url", help="URL to fetch")
    fetch_p.add_argument("-X", "--method", default="GET", help="HTTP method (default: GET)")
    fetch_p.add_argument("-H", "--header", action="append", dest="headers", metavar="KEY:VALUE")
    fetch_p.add_argument("--body", default=None, help="Request body (JSON string)")

    # --- watch (fetch + diff + store) ---
    watch_p = subparsers.add_parser("watch", help="Watch an endpoint and report changes.")
    watch_p.add_argument("url", help="URL to watch")
    watch_p.add_argument("--store-dir", default=".reqwatch", help="Directory for snapshots")
    watch_p.add_argument("-X", "--method", default="GET")
    watch_p.add_argument("-H", "--header", action="append", dest="headers", metavar="KEY:VALUE")
    watch_p.add_argument("--body", default=None)

    # --- list snapshots ---
    list_p = subparsers.add_parser("list", help="List stored snapshots for an endpoint.")
    list_p.add_argument("url", help="URL whose snapshots to list")
    list_p.add_argument("--store-dir", default=".reqwatch")

    return parser


def _parse_headers(raw: Optional[list]) -> dict:
    headers = {}
    for item in (raw or []):
        if ":" not in item:
            print(f"[warn] ignoring malformed header (expected KEY:VALUE): {item}", file=sys.stderr)
            continue
        k, v = item.split(":", 1)
        headers[k.strip()] = v.strip()
    return headers


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    headers = _parse_headers(getattr(args, "headers", None))
    body = json.loads(args.body) if getattr(args, "body", None) else None

    if args.command == "fetch":
        snap = fetch_response(args.url, method=args.method, headers=headers, body=body)
        print(json.dumps(snap, indent=2))

    elif args.command == "watch":
        diff = watch_endpoint(
            args.url,
            store_dir=args.store_dir,
            method=args.method,
            headers=headers,
            body=body,
        )
        if diff is None:
            print("[reqwatch] first snapshot saved — nothing to compare yet.")
        elif not diff:
            print("[reqwatch] no changes detected.")
        else:
            print("[reqwatch] changes detected:")
            print(format_diff(diff))
            return 1

    elif args.command == "list":
        snaps = list_snapshots(args.url, store_dir=args.store_dir)
        if not snaps:
            print("No snapshots found.")
        else:
            for ts in snaps:
                print(ts)

    return 0


if __name__ == "__main__":
    sys.exit(main())
