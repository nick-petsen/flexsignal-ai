#!/usr/bin/env python3
"""Identify observed negative DK1/DK2 price quarters in frozen EDS archives."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from pathlib import Path

import verify_public_eds_alignment as alignment


INTERVAL = timedelta(minutes=15)
MEAN_PRECISION = Decimal("0.000001")


class PriceBaselineError(ValueError):
    """Required observed price input is invalid."""


def _utc_text(stamp: datetime) -> str:
    return stamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _price(value: object, area: str, stamp: datetime) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise PriceBaselineError(f"missing or invalid DayAheadPriceDKK for {area} {_utc_text(stamp)}")
    try:
        price = Decimal(value)
    except InvalidOperation as exc:
        raise PriceBaselineError(f"invalid DayAheadPriceDKK for {area} {_utc_text(stamp)}") from exc
    if not price.is_finite():
        raise PriceBaselineError(f"invalid DayAheadPriceDKK for {area} {_utc_text(stamp)}")
    return price


def _stats(prices: list[Decimal]) -> dict[str, str] | None:
    if not prices:
        return None
    with localcontext() as context:
        context.prec = max(28, max(len(price.as_tuple().digits) for price in prices) + 12)
        context.rounding = ROUND_HALF_EVEN
        mean = (sum(prices, Decimal(0)) / len(prices)).quantize(MEAN_PRECISION)
    return {
        "minimum": format(min(prices), "f"),
        "maximum": format(max(prices), "f"),
        "mean": format(mean, "f"),
    }


def group_negative_windows(observations: list[tuple[datetime, Decimal]]) -> list[dict]:
    """Group sorted negative quarters; a missing quarter always ends a window."""
    windows = []
    active_start: datetime | None = None
    active_prices: list[Decimal] = []
    previous: datetime | None = None

    def close() -> None:
        nonlocal active_start, active_prices
        if active_start is not None:
            assert previous is not None
            windows.append({
                "start_utc": _utc_text(active_start),
                "end_utc_exclusive": _utc_text(previous + INTERVAL),
                "interval_count": len(active_prices),
                "duration_minutes": len(active_prices) * 15,
                "observed_price_dkk_per_mwh": _stats(active_prices),
            })
            active_start = None
            active_prices = []

    for stamp, price in observations:
        if previous is not None and stamp <= previous:
            raise PriceBaselineError("duplicate or unordered price interval")
        if active_start is not None and (price >= 0 or stamp - previous != INTERVAL):
            close()
        if price < 0:
            if active_start is None:
                active_start = stamp
            active_prices.append(price)
        previous = stamp
    close()
    return windows


def build_baseline(archive_root: Path) -> dict:
    """Verify frozen price archives and return a deterministic retrospective summary."""
    results, records_by_area = alignment.verify_price_records(archive_root)
    failures = [f"{archive_id}: {'; '.join(errors)}" for archive_id, _, errors in results if errors]
    if failures:
        raise PriceBaselineError("archive verification failed: " + " | ".join(failures))

    areas = []
    for area in ("DK1", "DK2"):
        observations = []
        for record in records_by_area[area]:
            assert isinstance(record, dict)  # Established by the archive verifier.
            stamp = alignment._utc(record["TimeUTC"], "TimeUTC")
            observations.append((stamp, _price(record.get("DayAheadPriceDKK"), area, stamp)))
        observations.sort(key=lambda item: item[0])
        windows = group_negative_windows(observations)
        prices = [price for _, price in observations]
        negative_prices = [price for price in prices if price < 0]
        areas.append({
            "price_area": area,
            "interval_count": len(prices),
            "negative_interval_count": len(negative_prices),
            "zero_interval_count": sum(price == 0 for price in prices),
            "positive_interval_count": sum(price > 0 for price in prices),
            "negative_window_count": len(windows),
            "negative_duration_minutes": len(negative_prices) * 15,
            "observed_price_dkk_per_mwh": _stats(prices),
            "negative_observed_price_dkk_per_mwh": _stats(negative_prices),
            "windows": windows,
        })

    return {
        "schema_version": "historical_negative_price_baseline.v0",
        "data_period": {
            "start_utc": _utc_text(alignment.START),
            "end_utc_exclusive": _utc_text(alignment.END),
            "interval_minutes": 15,
        },
        "method": {
            "kind": "retrospective_observed_price_identification",
            "source_dataset": "DayAheadPrices",
            "source_field": "DayAheadPriceDKK",
            "price_unit": "DKK/MWh",
            "negative_rule": "observed_price_dkk_per_mwh < 0",
            "window_rule": "consecutive negative 15-minute intervals within one price area",
            "timestamps": "UTC start-inclusive/end-exclusive",
            "mean_rounding": "six decimal places, half even",
            "input_archive_ids": [archive_id for archive_id, _, _ in results],
        },
        "areas": areas,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        payload = build_baseline(args.archive_root)
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))
        return 0
    except (PriceBaselineError, OSError, ValueError) as exc:
        print(f"FAIL historical negative-price baseline: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
