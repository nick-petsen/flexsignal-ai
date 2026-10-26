#!/usr/bin/env python3
"""Compare two manually selected historical price quarters, offline and read-only."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

import historical_negative_price_baseline as baseline


class ScenarioError(ValueError):
    """A manual scenario input or required archive observation is invalid."""


def _timestamp(value: str, name: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+00:00)", value
    ):
        raise ScenarioError(f"{name} must be an explicit UTC ISO 8601 timestamp")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ScenarioError(f"{name} is invalid") from exc
    if stamp.minute % 15 or stamp.second or stamp.microsecond:
        raise ScenarioError(f"{name} must start on a 15-minute boundary")
    return stamp.astimezone(timezone.utc)


def _positive_decimal(value: str, name: str) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"\+?(?:\d+(?:\.\d*)?|\.\d+)", value):
        raise ScenarioError(f"{name} must be a positive finite decimal")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ScenarioError(f"{name} must be a positive finite decimal") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise ScenarioError(f"{name} must be a positive finite decimal")
    return parsed


def evaluate_scenario(
    *,
    archive_root: Path,
    price_area: str,
    original_utc: str,
    alternative_utc: str,
    energy_mwh: str,
    max_flexible_power_mw: str,
    alternative_price_area: str | None = None,
) -> dict:
    """Evaluate a caller-selected shift using verified observed DKK/MWh prices."""
    if price_area not in ("DK1", "DK2"):
        raise ScenarioError("price_area must be DK1 or DK2")
    if alternative_price_area is not None and alternative_price_area != price_area:
        raise ScenarioError("original and alternative price areas must match")
    original = _timestamp(original_utc, "original_utc")
    alternative = _timestamp(alternative_utc, "alternative_utc")
    if original == alternative:
        raise ScenarioError("original_utc and alternative_utc must be distinct")
    energy = _positive_decimal(energy_mwh, "energy_mwh")
    maximum_power = _positive_decimal(max_flexible_power_mw, "max_flexible_power_mw")

    try:
        archive_ids, observations_by_area = baseline.load_verified_prices(archive_root)
    except (baseline.PriceBaselineError, OSError, ValueError) as exc:
        raise ScenarioError(str(exc)) from exc
    prices = dict(observations_by_area[price_area])
    if original not in prices:
        raise ScenarioError("original_utc is missing from the verified price archive")
    if alternative not in prices:
        raise ScenarioError("alternative_utc is missing from the verified price archive")

    original_price, alternative_price = prices[original], prices[alternative]
    with localcontext() as context:
        context.prec = max(
            28,
            sum(len(value.as_tuple().digits) for value in (energy, original_price, alternative_price)) + 4,
        )
        gross_difference = energy * (original_price - alternative_price)
        required_power = energy * Decimal(4)

    return {
        "schema_version": "manual_flexibility_price_scenario.v0",
        "price_area": price_area,
        "original_utc": baseline._utc_text(original),
        "alternative_utc": baseline._utc_text(alternative),
        "original_price_dkk_per_mwh": format(original_price, "f"),
        "alternative_price_dkk_per_mwh": format(alternative_price, "f"),
        "energy_mwh": format(energy, "f"),
        "max_flexible_power_mw": format(maximum_power, "f"),
        "required_average_power_mw": format(required_power, "f"),
        "power_check": {
            "within_declared_maximum": required_power <= maximum_power,
            "interval_minutes": 15,
        },
        "indicative_spot_price_gross_difference_dkk": format(gross_difference, "f"),
        "method": {
            "selection": "original and alternative intervals manually selected by caller",
            "source_dataset": "DayAheadPrices",
            "source_field": "DayAheadPriceDKK",
            "input_archive_ids": archive_ids,
            "calculation": "energy_mwh * (original_price_dkk_per_mwh - alternative_price_dkk_per_mwh)",
        },
        "assumptions": [
            "The stated energy is shifted from the original quarter-hour to the alternative quarter-hour in the same price area.",
            "Required average destination power equals energy_mwh divided by 0.25 hours.",
        ],
        "limitations": [
            "Illustrative retrospective comparison of observed spot prices only; prices are not assumed known before delivery.",
            "The declared power check is one limited constraint and does not establish operational feasibility.",
            "Actual flexibility, alternative operating schedule, power limitations, market arrangements and financial outcome require customer validation.",
            "No tariffs, taxes, operating costs, realized savings, forecast, optimization or operational recommendation are included.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--price-area", required=True)
    parser.add_argument("--alternative-price-area", help="Optional explicit area; must match --price-area")
    parser.add_argument("--original-utc", required=True)
    parser.add_argument("--alternative-utc", required=True)
    parser.add_argument("--energy-mwh", required=True)
    parser.add_argument("--max-flexible-power-mw", required=True)
    args = parser.parse_args(argv)
    try:
        result = evaluate_scenario(
            archive_root=args.archive_root,
            price_area=args.price_area,
            alternative_price_area=args.alternative_price_area,
            original_utc=args.original_utc,
            alternative_utc=args.alternative_utc,
            energy_mwh=args.energy_mwh,
            max_flexible_power_mw=args.max_flexible_power_mw,
        )
    except ScenarioError as exc:
        print(f"FAIL manual flexibility price scenario: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
