#!/usr/bin/env python3
"""Manual synthetic preview for the rule-engine-v0 backtest evaluator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.risk import evaluate_risk_backtest  # noqa: E402


SYNTHETIC_ROWS: list[dict[str, Any]] = [
    {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00Z",
        "price_dkk_per_mwh": 500,
        "production_mw": 100,
        "consumption_mw": 95,
        "wind_onshore_mw": 10,
        "wind_offshore_mw": 5,
        "solar_mw": 5,
        "exchange_net_mw": 0,
    },
    {
        "price_area": "DK2",
        "timestamp_utc": "2026-01-01T01:00:00Z",
        "price_dkk_per_mwh": 50,
        "production_mw": 100,
        "consumption_mw": 90,
        "wind_onshore_mw": 30,
        "wind_offshore_mw": 25,
        "solar_mw": 5,
    },
    {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T02:00:00Z",
        "price_dkk_per_mwh": -25,
        "production_mw": 100,
        "consumption_mw": 80,
        "wind_onshore_mw": 50,
        "wind_offshore_mw": 30,
        "solar_mw": 5,
    },
    {
        "price_area": "DK2",
        "timestamp_utc": "2026-01-01T03:00:00Z",
        "production_mw": 100,
        "consumption_mw": 92,
        "wind_onshore_mw": 20,
        "wind_offshore_mw": 10,
        "solar_mw": 5,
    },
    {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T04:00:00Z",
        "price_dkk_per_mwh": 300,
        "consumption_mw": 92,
        "wind_onshore_mw": 20,
        "wind_offshore_mw": 10,
        "solar_mw": 5,
    },
    {
        "price_area": "SE3",
        "timestamp_utc": "2026-01-01T05:00:00Z",
        "price_dkk_per_mwh": 100,
        "production_mw": 100,
        "consumption_mw": 90,
        "wind_onshore_mw": 10,
        "wind_offshore_mw": 10,
        "solar_mw": 10,
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a manual synthetic local preview of the existing "
            "rule-engine-v0 backtest evaluator."
        )
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print indented JSON instead of compact JSON.",
    )
    return parser


def print_scope_warning() -> None:
    print(
        "WARNING: synthetic/local preview only. Uses hardcoded sample rows; "
        "does not require DATABASE_URL; does not call databases, SQL, HTTP, "
        "live Energi Data Service APIs, Azure, frontend code, ingestion jobs, "
        "ML training, LLMs, control, dispatch, activation, or operational "
        "systems.",
        file=sys.stderr,
    )


def main() -> int:
    args = build_parser().parse_args()
    print_scope_warning()

    summary = evaluate_risk_backtest(SYNTHETIC_ROWS)
    if args.pretty:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps(summary, separators=(",", ":"), sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
