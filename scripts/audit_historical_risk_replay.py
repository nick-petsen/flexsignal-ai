#!/usr/bin/env python3
"""Read-only compatibility audit for the frozen P0.9a hourly EDS input."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from math import isfinite
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.risk import rule_engine  # noqa: E402

import build_hourly_eds_backtest_input as hourly
import public_surplus_risk_backtest_input as historical


AREAS = ("DK1", "DK2")
RENEWABLE_FIELDS = (
    *historical.WIND_GENERATION_FIELDS,
    *historical.SOLAR_GENERATION_FIELDS,
)
HYDRO_FIELDS = historical.HYDRO_RENEWABLE_FIELDS
SOURCE_FIELDS = ("GrossConsumptionMWh", *RENEWABLE_FIELDS, *HYDRO_FIELDS)
EXPECTED_SCHEMA = "hourly_public_eds_backtest_input.v0"
CURRENT_SCORING_FIELDS = (
    "price_dkk_per_mwh", "production_mw", *rule_engine.RENEWABLE_FIELDS,
)


def _rule_contract_errors(area: str) -> list[str]:
    """Check the existing validator and scoring field contract without scoring."""
    errors = []
    if area not in rule_engine.VALID_PRICE_AREAS:
        errors.append(f"{area} is not accepted by rule-engine-v0")
    validator = getattr(rule_engine, "_validate_input", None)
    minimum = {
        "price_area": area,
        "timestamp_utc": hourly._utc_text(hourly.alignment.START),
    }
    if not callable(validator):
        errors.append("rule-engine-v0 input validator is unavailable")
    else:
        try:
            validator(minimum)
        except (TypeError, ValueError) as exc:
            errors.append(f"rule-engine-v0 minimum input contract changed: {exc}")
        for field in minimum:
            try:
                validator({key: value for key, value in minimum.items() if key != field})
            except (TypeError, ValueError):
                continue
            errors.append(f"rule-engine-v0 no longer requires {field}")
    if (
        not set(CURRENT_SCORING_FIELDS) <= rule_engine.NUMERIC_FIELDS
        or tuple(rule_engine.RENEWABLE_FIELDS)
        != ("wind_onshore_mw", "wind_offshore_mw", "solar_mw")
    ):
        errors.append("rule-engine-v0 price, production, or renewable scoring fields changed")
    return errors


def _finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        return False
    try:
        return Decimal(str(value)).is_finite()
    except InvalidOperation:
        return False


def _valid_dkk_price(value: object) -> bool:
    """Require the builder's text type and a finite rule-engine numeric value."""
    if not isinstance(value, str) or not _finite_number(value):
        return False
    try:
        numeric = float(value)
        return isfinite(numeric) and (numeric != 0 or Decimal(value) == 0)
    except (OverflowError, ValueError):
        return False


def _coverage(rows: list[dict], field: str) -> dict[str, int]:
    settlements = [row.get("settlement_observed") for row in rows]
    return {
        "absent": sum(isinstance(s, dict) and field not in s for s in settlements),
        "null": sum(isinstance(s, dict) and s.get(field) is None and field in s for s in settlements),
    }


def _area_report(area: str, rows: list[dict], structural_errors: list[str]) -> dict:
    reasons = list(structural_errors)
    if len(rows) != 168:
        reasons.append(f"expected 168 hourly rows; found {len(rows)}")

    for row in rows:
        stamp = row.get("hour_utc")
        if not isinstance(stamp, str):
            reasons.append("hour_utc is absent or invalid")
            break
        try:
            parsed = hourly.alignment._utc(stamp, "hour_utc")
        except ValueError:
            reasons.append("hour_utc is absent or invalid")
            break
        if (
            stamp != hourly._utc_text(parsed)
            or parsed.minute or parsed.second or parsed.microsecond
        ):
            reasons.append("hour_utc is not a canonical UTC hour")
            break
    expected_hours = {
        hourly._utc_text(hourly.alignment.START + timedelta(hours=index))
        for index in range(168)
    }
    actual_hours = {
        row.get("hour_utc") for row in rows
        if isinstance(row.get("hour_utc"), str)
    }
    if actual_hours != expected_hours:
        reasons.append("UTC hours are missing, duplicated, or outside the frozen period")

    bad_prices = sum(
        not isinstance(row.get("price_eur_per_mwh"), str)
        or not _finite_number(row.get("price_eur_per_mwh"))
        for row in rows
    )
    if bad_prices:
        reasons.append(f"price_eur_per_mwh is absent or invalid in {bad_prices} rows")
    bad_dkk_prices = sum(not _valid_dkk_price(row.get("price_dkk_per_mwh")) for row in rows)
    if bad_dkk_prices:
        reasons.append(
            f"price_dkk_per_mwh is absent, invalid, or outside the rule-engine numeric range "
            f"in {bad_dkk_prices} rows"
        )

    coverage = {field: _coverage(rows, field) for field in SOURCE_FIELDS}
    bad_settlements = sum(
        not isinstance(row.get("settlement_observed"), dict) for row in rows
    )
    if bad_settlements:
        reasons.append(f"settlement_observed is absent or invalid in {bad_settlements} rows")

    required = ("GrossConsumptionMWh", *RENEWABLE_FIELDS)
    for field in required:
        missing = coverage[field]["absent"] + coverage[field]["null"]
        if missing:
            reasons.append(f"{field} is absent or null in {missing} rows")
    hydro_missing = sum(
        isinstance(row.get("settlement_observed"), dict)
        and all(row["settlement_observed"].get(field) is None for field in HYDRO_FIELDS)
        for row in rows
    )
    if hydro_missing:
        reasons.append(
            "all hydro/other-renewable alternatives are absent or null "
            f"in {hydro_missing} rows"
        )

    invalid = 0
    for index, row in enumerate(rows):
        settlement = row.get("settlement_observed")
        if not isinstance(settlement, dict):
            continue
        present = [field for field in SOURCE_FIELDS if settlement.get(field) is not None]
        if any(not _finite_number(settlement[field]) for field in present):
            invalid += 1
            continue
        if any(
            Decimal(str(settlement[field])) < 0
            for field in present if field != "GrossConsumptionMWh"
        ):
            invalid += 1
            continue
        if not _finite_number(settlement.get("GrossConsumptionMWh")):
            continue
        if Decimal(str(settlement["GrossConsumptionMWh"])) <= 0:
            invalid += 1
            continue
        try:
            normalized, _ = historical.normalize_production_consumption_record(
                {**settlement, "PriceArea": area, "HourUTC": row["hour_utc"]},
                index=index,
            )
            renewable = normalized["renewable_generation_mwh"]
            gross = normalized["gross_consumption_mwh"]
            if (
                renewable is None or not _finite_number(renewable) or renewable < 0
                or not _finite_number(gross) or gross <= 0
            ):
                invalid += 1
        except (KeyError, TypeError, ValueError):
            invalid += 1
    if invalid:
        reasons.append(
            "historical settlement normalization fails or has invalid values "
            f"in {invalid} rows"
        )

    historical_status = "PASS" if not reasons else "BLOCKED"
    price_contract_ok = "price_dkk_per_mwh" in rule_engine.NUMERIC_FIELDS
    price_reasons = []
    if bad_dkk_prices:
        price_reasons.append(f"price_dkk_per_mwh is absent or invalid in {bad_dkk_prices} rows")
    if not price_contract_ok:
        price_reasons.append("rule-engine-v0 no longer accepts price_dkk_per_mwh as a numeric field")
    if not price_reasons:
        price_reasons.append(
            "P0.9a provides the native observed DKK/MWh hourly mean of four "
            "day-ahead quarters; all values satisfy the rule-engine-v0 numeric price contract"
        )
    current_reasons = [
        *(price_reasons if bad_dkk_prices or not price_contract_ok else []),
        "rule-engine-v0 renewable share divides onshore wind, offshore wind, and solar MW by production_mw; P0.9a has no direct validated production MW denominator",
        "wind_onshore_mw, wind_offshore_mw, and solar_mw have only observed hourly MWh components, not issuance-time forecasts",
    ]
    current_reasons = _rule_contract_errors(area) + current_reasons
    forecast_reasons = [
        "no generated_at_utc or source publication/revision times establish what was visible at issuance",
        "settlement_observed gross consumption and wind/solar/hydro generation are realized values; using them before publication introduces look-ahead bias",
        "the archived day-ahead price is observed/revised data with no proven issuance-time vintage; using it as known at issuance may introduce look-ahead bias",
    ]
    return {
        "price_area": area,
        "row_count": len(rows),
        "source_field_coverage": coverage,
        "observed_historical_input": {
            "status": historical_status,
            "reasons": reasons or [
                "EUR/MWh price and complete observed settlement fields map to the "
                "historical public engine; native observed DKK/MWh price is present"
            ],
        },
        "current_rule_engine": {
            "status": "BLOCKED",
            "contract_required_inputs": ["price_area", "timestamp_utc"],
            "price_input": {
                "status": "BLOCKED" if bad_dkk_prices or not price_contract_ok else "PASS",
                "source_field": "price_dkk_per_mwh",
                "reasons": price_reasons,
            },
            "unresolved_scoring_inputs": (
                list(CURRENT_SCORING_FIELDS) if bad_dkk_prices or not price_contract_ok
                else list(CURRENT_SCORING_FIELDS[1:])
            ),
            "reasons": current_reasons,
        },
        "forecast_issuance": {
            "status": "BLOCKED",
            "reasons": forecast_reasons,
            "look_ahead_inputs": [
                "settlement_observed.GrossConsumptionMWh",
                "settlement_observed.wind/solar/hydro generation",
            ],
            "unverified_at_issuance": ["price_eur_per_mwh", "price_dkk_per_mwh"],
        },
        "status": "BLOCKED",
    }


def audit_hourly_input(payload: object) -> dict:
    """Inspect input contracts and availability; never calculate a risk score."""
    errors = []
    if not isinstance(payload, dict):
        payload = {}
        errors.append("P0.9a payload must be an object")
    if payload.get("schema_version") != EXPECTED_SCHEMA:
        errors.append("P0.9a schema_version is absent or unexpected")
    if (
        payload.get("start_utc") != hourly._utc_text(hourly.alignment.START)
        or payload.get("end_utc_exclusive") != hourly._utc_text(hourly.alignment.END)
    ):
        errors.append("P0.9a UTC period is absent or unexpected")
    records = payload.get("records")
    if not isinstance(records, list):
        records = []
        errors.append("P0.9a records must be a list")
    if len(records) != 336:
        errors.append(f"expected 336 total rows; found {len(records)}")
    if any(not isinstance(row, dict) or row.get("price_area") not in AREAS for row in records):
        errors.append("records contain invalid price_area or non-object rows")
    area_reports = [
        _area_report(
            area,
            [
                row for row in records
                if isinstance(row, dict) and row.get("price_area") == area
            ],
            errors,
        )
        for area in AREAS
    ]
    overall_reasons = [
        f"{area['price_area']} {check}: {area[check]['reasons'][0]}"
        for area in area_reports
        for check in ("observed_historical_input", "current_rule_engine", "forecast_issuance")
        if area[check]["status"] == "BLOCKED"
    ]
    return {
        "audit_version": "historical-risk-replay-readiness.v0",
        "input_schema": EXPECTED_SCHEMA,
        "areas": area_reports,
        "overall_status": "BLOCKED" if overall_reasons else "PASS",
        "overall_reasons": overall_reasons,
    }


def _execution_error_report(message: str) -> dict:
    areas = [
        {
            "price_area": area,
            "status": "BLOCKED",
            "observed_historical_input": {"status": "BLOCKED", "reasons": [message]},
            "current_rule_engine": {"status": "BLOCKED", "reasons": [message]},
            "forecast_issuance": {"status": "BLOCKED", "reasons": [message]},
        }
        for area in AREAS
    ]
    return {
        "audit_version": "historical-risk-replay-readiness.v0",
        "input_schema": EXPECTED_SCHEMA,
        "areas": areas,
        "overall_status": "BLOCKED",
        "overall_reasons": [message],
        "execution_error": message,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", type=Path, required=True)
    args = parser.parse_args(argv)
    stage = "archive verification/build"
    try:
        payload = hourly.build_hourly_input(args.archive_root)
        stage = "readiness audit"
        report = audit_hourly_input(payload)
    except Exception as exc:  # An incomplete audit must never look ready.
        report = _execution_error_report(f"{stage} failed: {type(exc).__name__}: {exc}")
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    if "execution_error" in report:
        return 2
    return 0 if report["overall_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
