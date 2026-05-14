"""CLI subcommand: reqwatch trend — show response-time and status trends."""

from __future__ import annotations

import json
import argparse
from typing import Any

from reqwatch.snapshot_trend import build_trend, TrendError


def cmd_trend(args: argparse.Namespace) -> None:
    store_dir: str = args.store
    endpoint: str = args.endpoint
    limit: int = args.limit
    summarize: bool = args.summarize

    try:
        trend = build_trend(store_dir, endpoint, limit=limit)
    except TrendError as exc:
        print(f"[trend] error: {exc}")
        return

    if summarize:
        out: Any = {
            "endpoint": trend.endpoint,
            "points_analysed": len(trend.points),
            "avg_response_time": trend.avg_response_time,
            "p95_response_time": trend.p95_response_time,
            "error_rate": trend.error_rate,
            "dominant_status": trend.dominant_status,
        }
    else:
        out = {
            "endpoint": trend.endpoint,
            "summary": {
                "avg_response_time": trend.avg_response_time,
                "p95_response_time": trend.p95_response_time,
                "error_rate": trend.error_rate,
                "dominant_status": trend.dominant_status,
            },
            "points": [
                {
                    "timestamp": p.timestamp,
                    "status": p.status,
                    "response_time": p.response_time,
                    "has_error": p.has_error,
                }
                for p in trend.points
            ],
        }

    print(json.dumps(out, indent=2))


def register_trend_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "trend",
        help="Show response-time and status-code trends for an endpoint",
    )
    parser.add_argument("endpoint", help="Endpoint key to analyse")
    parser.add_argument(
        "--store", default=".reqwatch", help="Storage directory (default: .reqwatch)"
    )
    parser.add_argument(
        "--limit", type=int, default=50, help="Max snapshots to include (default: 50)"
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Print summary only, omit per-point data",
    )
    parser.set_defaults(func=cmd_trend)
