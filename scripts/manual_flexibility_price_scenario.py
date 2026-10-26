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


def _timestamp(value: str, name: str, *, quarter_hour_start: bool = True) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+00:00)", value
    ):
        raise ScenarioError(f"{name} must be an explicit UTC ISO 8601 timestamp")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ScenarioError(f"{name} is invalid") from exc
    if quarter_hour_start and (stamp.minute % 15 or stamp.second or stamp.microsecond):
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


def _check(passed: bool, pass_code: str, fail_code: str) -> dict[str, str]:
    return {"status": "PASS" if passed else "FAIL", "reason_code": pass_code if passed else fail_code}


def _operating_constraints_assessment(
    *,
    enabled: bool,
    original: datetime,
    alternative: datetime,
    energy: Decimal,
    required_power: Decimal,
    maximum_power: Decimal,
    max_shiftable_energy_mwh: str | None,
    max_absolute_shift_minutes: str | None,
    allowed_destination_start_utc: str | None,
    allowed_destination_end_utc_exclusive: str | None,
) -> dict:
    declared = (
        max_shiftable_energy_mwh,
        max_absolute_shift_minutes,
        allowed_destination_start_utc,
        allowed_destination_end_utc_exclusive,
    )
    if not isinstance(enabled, bool):
        raise ScenarioError("assess_operating_constraints must be a boolean")
    if not enabled:
        if any(value is not None for value in declared):
            raise ScenarioError("operating constraint inputs require --assess-operating-constraints")
        return {
            "status": "NOT_ASSESSED",
            "reason_code": "ASSESSMENT_NOT_ENABLED",
            "scope": "Customer-declared limits only; no operational feasibility determination.",
            "checks": {name: {"status": "NOT_ASSESSED", "reason_code": "ASSESSMENT_NOT_ENABLED"}
                       for name in ("energy_limit", "absolute_shift_limit", "destination_window")},
        }

    if any(value is None for value in declared):
        raise ScenarioError("assessment requires max_shiftable_energy_mwh, max_absolute_shift_minutes, "
                            "allowed_destination_start_utc and allowed_destination_end_utc_exclusive")
    max_energy = _positive_decimal(max_shiftable_energy_mwh, "max_shiftable_energy_mwh")
    max_shift = _positive_decimal(max_absolute_shift_minutes, "max_absolute_shift_minutes")
    window_start = _timestamp(allowed_destination_start_utc, "allowed_destination_start_utc",
                              quarter_hour_start=False)
    window_end = _timestamp(allowed_destination_end_utc_exclusive, "allowed_destination_end_utc_exclusive",
                            quarter_hour_start=False)
    if window_start >= window_end:
        raise ScenarioError("allowed destination window start must precede end")

    shift = abs(alternative - original)
    shift_minutes = Decimal(shift.days * 1440 + shift.seconds // 60)
    checks = {
        "energy_limit": _check(energy <= max_energy, "ENERGY_WITHIN_MAXIMUM", "ENERGY_EXCEEDS_MAXIMUM"),
        "absolute_shift_limit": _check(shift_minutes <= max_shift, "SHIFT_WITHIN_MAXIMUM", "SHIFT_EXCEEDS_MAXIMUM"),
        "destination_window": _check(
            window_start <= alternative and alternative + baseline.INTERVAL <= window_end,
            "DESTINATION_FULLY_WITHIN_WINDOW", "DESTINATION_OUTSIDE_WINDOW",
        ),
        "flexible_power_limit": _check(required_power <= maximum_power,
                                       "POWER_WITHIN_MAXIMUM", "POWER_EXCEEDS_MAXIMUM"),
    }
    passed = all(check["status"] == "PASS" for check in checks.values())
    return {
        "status": "PASS" if passed else "FAIL",
        "reason_code": "ALL_DECLARED_CHECKS_PASS" if passed else "DECLARED_CHECKS_FAILED",
        "scope": "Customer-declared limits only; no operational feasibility determination.",
        "declared": {
            "max_shiftable_energy_mwh": format(max_energy, "f"),
            "max_absolute_shift_minutes": format(max_shift, "f"),
            "allowed_destination_start_utc": baseline._utc_text(window_start),
            "allowed_destination_end_utc_exclusive": baseline._utc_text(window_end),
        },
        "observed_absolute_shift_minutes": format(shift_minutes, "f"),
        "checks": checks,
    }


def evaluate_scenario(
    *,
    archive_root: Path,
    price_area: str,
    original_utc: str,
    alternative_utc: str,
    energy_mwh: str,
    max_flexible_power_mw: str,
    alternative_price_area: str | None = None,
    assess_operating_constraints: bool = False,
    max_shiftable_energy_mwh: str | None = None,
    max_absolute_shift_minutes: str | None = None,
    allowed_destination_start_utc: str | None = None,
    allowed_destination_end_utc_exclusive: str | None = None,
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

    assessment = _operating_constraints_assessment(
        enabled=assess_operating_constraints,
        original=original,
        alternative=alternative,
        energy=energy,
        required_power=required_power,
        maximum_power=maximum_power,
        max_shiftable_energy_mwh=max_shiftable_energy_mwh,
        max_absolute_shift_minutes=max_absolute_shift_minutes,
        allowed_destination_start_utc=allowed_destination_start_utc,
        allowed_destination_end_utc_exclusive=allowed_destination_end_utc_exclusive,
    )

    limitations = [
        "Illustrative retrospective comparison of observed spot prices only; prices are not assumed known before delivery.",
        "The declared power check is one limited constraint and does not establish operational feasibility.",
        "Actual flexibility, alternative operating schedule, power limitations, market arrangements and financial outcome require customer validation.",
        "No tariffs, taxes, operating costs, realized savings, forecast, optimization or operational recommendation are included.",
    ]
    if assess_operating_constraints:
        limitations.append(
            "Customer-declared operating limits are unverified and their checks do not establish operational feasibility."
        )

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
        "operating_constraints_assessment": assessment,
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
        "limitations": limitations,
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
    parser.add_argument("--assess-operating-constraints", action="store_true")
    parser.add_argument("--max-shiftable-energy-mwh")
    parser.add_argument("--max-absolute-shift-minutes")
    parser.add_argument("--allowed-destination-start-utc")
    parser.add_argument("--allowed-destination-end-utc-exclusive")
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
            assess_operating_constraints=args.assess_operating_constraints,
            max_shiftable_energy_mwh=args.max_shiftable_energy_mwh,
            max_absolute_shift_minutes=args.max_absolute_shift_minutes,
            allowed_destination_start_utc=args.allowed_destination_start_utc,
            allowed_destination_end_utc_exclusive=args.allowed_destination_end_utc_exclusive,
        )
    except ScenarioError as exc:
        print(f"FAIL manual flexibility price scenario: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
