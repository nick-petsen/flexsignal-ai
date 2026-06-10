#!/usr/bin/env python3
"""Manual synthetic local preview for forecast-window-v0."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.forecast.window_forecast import build_forecast_window_forecast  # noqa: E402


GENERATED_AT_UTC = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
SCENARIOS = ("balanced", "high-risk", "empty-window")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a manual synthetic local preview of forecast-window-v0 using "
            "caller-provided sample rows."
        )
    )
    parser.add_argument(
        "--price-area",
        choices=("DK1", "DK2"),
        default="DK1",
        help="Danish price area to include in the preview. Default: DK1.",
    )
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS,
        default="balanced",
        help="Synthetic local row scenario to preview. Default: balanced.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print indented JSON instead of compact JSON.",
    )
    return parser


def build_synthetic_rows(price_area: str, scenario: str) -> list[dict[str, Any]]:
    if scenario == "balanced":
        return _balanced_rows(price_area)
    if scenario == "high-risk":
        return _high_risk_rows(price_area)
    if scenario == "empty-window":
        return _empty_window_rows(price_area)
    raise ValueError(f"Unsupported scenario: {scenario}")


def _balanced_rows(price_area: str) -> list[dict[str, Any]]:
    return [
        _row(price_area, hours=3, price=300, production=1000, renewable=250),
        _row(price_area, hours=12, price=80, production=1000, renewable=600),
        _row(price_area, hours=30, price=180, production=1000, renewable=650),
        _row(price_area, hours=42, price=260, production=1000, renewable=420),
        _row(price_area, hours=54, price=450, production=1000, renewable=250),
        _row(price_area, hours=66, price=95, production=1000, renewable=420),
    ]


def _high_risk_rows(price_area: str) -> list[dict[str, Any]]:
    return [
        _row(price_area, hours=6, price=320, production=1000, renewable=250),
        _row(price_area, hours=28, price=90, production=1000, renewable=600),
        _row(price_area, hours=36, price=-25, production=1000, renewable=850),
        _row(price_area, hours=60, price=400, production=1000, renewable=300),
    ]


def _empty_window_rows(price_area: str) -> list[dict[str, Any]]:
    other_area = "DK2" if price_area == "DK1" else "DK1"
    return [
        _row(price_area, hours=4, price=280, production=1000, renewable=300),
        _row(price_area, hours=18, price=70, production=1000, renewable=620),
        _row(other_area, hours=30, price=-10, production=1000, renewable=850),
        _row(price_area, hours=52, price=450, production=1000, renewable=220),
    ]


def _row(
    price_area: str,
    *,
    hours: int,
    price: float,
    production: float,
    renewable: float,
) -> dict[str, Any]:
    timestamp = GENERATED_AT_UTC + timedelta(hours=hours)
    wind_onshore = round(renewable * 0.45, 4)
    wind_offshore = round(renewable * 0.35, 4)
    solar = round(renewable - wind_onshore - wind_offshore, 4)

    return {
        "price_area": price_area,
        "timestamp_utc": _format_utc_timestamp(timestamp),
        "price_dkk_per_mwh": price,
        "production_mw": production,
        "consumption_mw": production * 0.9,
        "wind_onshore_mw": wind_onshore,
        "wind_offshore_mw": wind_offshore,
        "solar_mw": solar,
        "exchange_net_mw": 0,
    }


def print_scope_warning() -> None:
    print(
        "WARNING: synthetic local preview only. Uses in-script caller-provided "
        "sample rows; does not require DATABASE_URL; does not access databases, "
        "run SQL, fetch Energi Data Service data, call DMI/weather APIs, start "
        "servers, add API endpoints, run frontend code, schedule jobs, use "
        "Azure, add secrets, add auth, train ML models, use LLMs, control "
        "assets, dispatch, activate, or perform operational functionality.",
        file=sys.stderr,
    )


def serialize_for_json(value: Any) -> Any:
    if isinstance(value, datetime):
        return _format_utc_timestamp(value)
    if isinstance(value, dict):
        return {key: serialize_for_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_for_json(item) for item in value]
    return value


def _format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    args = build_parser().parse_args()
    print_scope_warning()

    rows = build_synthetic_rows(args.price_area, args.scenario)
    forecast = build_forecast_window_forecast(
        price_area=args.price_area,
        generated_at_utc=GENERATED_AT_UTC,
        rows=rows,
    )
    forecast["preview_note"] = (
        "Synthetic local preview only. Must not be used for automatic control, "
        "dispatch, activation, or operational decisions."
    )
    output = serialize_for_json(forecast)

    if args.pretty:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(json.dumps(output, separators=(",", ":"), sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
