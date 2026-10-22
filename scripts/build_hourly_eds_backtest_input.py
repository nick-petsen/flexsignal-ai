#!/usr/bin/env python3
"""Build deterministic hourly historical input from the four frozen EDS archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

import verify_public_eds_alignment as alignment


class HourlyInputError(ValueError):
    """An archive cannot supply the required hourly historical input."""


def _utc_text(stamp: datetime) -> str:
    return stamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _json_value(value: object) -> object:
    """Keep observed JSON values, rendering decimal numbers as exact strings."""
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    return value


def _price(value: object, area: str, stamp: datetime) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise HourlyInputError(f"missing or invalid DayAheadPriceEUR for {area} {_utc_text(stamp)}")
    try:
        price = Decimal(value)
    except InvalidOperation as exc:
        raise HourlyInputError(f"invalid DayAheadPriceEUR for {area} {_utc_text(stamp)}") from exc
    if not price.is_finite():
        raise HourlyInputError(f"invalid DayAheadPriceEUR for {area} {_utc_text(stamp)}")
    return price


def build_hourly_input(archive_root: Path) -> dict:
    """Return 336 sorted observed rows after P0.8 integrity and alignment checks."""
    results, sources = alignment.verify_with_records(archive_root)
    failures = [f"{archive_id}: {'; '.join(errors)}" for archive_id, _, errors in results if errors]
    if failures:
        raise HourlyInputError("archive verification failed: " + " | ".join(failures))

    hourly_rows = []
    for area in ("DK1", "DK2"):
        quarters: dict[datetime, list[Decimal]] = defaultdict(list)
        for record in sources["DayAheadPrices", area]:
            assert isinstance(record, dict)  # Established by the verifier.
            stamp = alignment._utc(record["TimeUTC"], "TimeUTC")
            hour = stamp.replace(minute=0, second=0, microsecond=0)
            quarters[hour].append(_price(record.get("DayAheadPriceEUR"), area, stamp))

        settlements = {}
        for record in sources["ProductionConsumptionSettlement", area]:
            assert isinstance(record, dict)  # Established by the verifier.
            hour = alignment._utc(record["HourUTC"], "HourUTC")
            settlements[hour] = record

        if len(settlements) != 168:
            raise HourlyInputError(f"expected 168 settlement hours for {area}, got {len(settlements)}")
        for hour in sorted(settlements):
            values = quarters.get(hour, [])
            if len(values) != 4:
                raise HourlyInputError(f"expected four price quarters for {area} {_utc_text(hour)}")
            with localcontext() as context:
                integer_digits = max(max(value.adjusted() + 1, 0) for value in values)
                fractional_digits = max(max(-value.as_tuple().exponent, 0) for value in values)
                context.prec = max(28, integer_digits + fractional_digits + 4)
                mean = sum(values, Decimal(0)) / Decimal(4)
            settlement = settlements[hour]
            hourly_rows.append({
                "price_area": area,
                "hour_utc": _utc_text(hour),
                "price_eur_per_mwh": format(mean, "f"),
                "settlement_observed": _json_value({
                    key: value for key, value in settlement.items()
                    if key not in ("PriceArea", "HourUTC")
                }),
            })

    if len(hourly_rows) != 336:
        raise HourlyInputError(f"expected 336 hourly rows, got {len(hourly_rows)}")
    return {
        "schema_version": "hourly_public_eds_backtest_input.v0",
        "start_utc": _utc_text(alignment.START),
        "end_utc_exclusive": _utc_text(alignment.END),
        "records": hourly_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Optional JSON output file outside the archive root")
    args = parser.parse_args(argv)
    try:
        if args.output and args.output.resolve().is_relative_to(args.archive_root.resolve()):
            raise HourlyInputError("output must be outside the read-only archive root")
        if args.output and args.output.is_symlink():
            raise HourlyInputError("output must not be a symlink")
        payload = build_hourly_input(args.archive_root)
        encoded = (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
        if args.output:
            args.output.write_bytes(encoded)
        digest = hashlib.sha256(encoded).hexdigest()
        destination = str(args.output) if args.output else "not written"
        print(
            f"PASS hourly EDS input: DK1=168 DK2=168 total=336; "
            f"UTC=[{payload['start_utc']}, {payload['end_utc_exclusive']}); "
            f"sha256={digest}; output={destination}"
        )
        return 0
    except (HourlyInputError, OSError, ValueError) as exc:
        print(f"FAIL hourly EDS input: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
