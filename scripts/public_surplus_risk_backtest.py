#!/usr/bin/env python3
"""Read-only public DK1/DK2 surplus-risk backtest engine v1."""

from __future__ import annotations

import json
import math
import os
import sys
import urllib.error
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import public_surplus_risk_backtest_input as input_foundation  # noqa: E402


DEFAULT_LOW_PRICE_THRESHOLD_EUR_PER_MWH = "25"
DEFAULT_RENEWABLE_SHARE_MEDIUM_THRESHOLD = "0.65"
DEFAULT_RENEWABLE_SHARE_HIGH_THRESHOLD = "0.80"
DEFAULT_TOP_RISK_WINDOWS = "10"
DEFAULT_WINDOW_SNAPSHOT_ONLY = "false"
PRICE_CONTEXT_STATUS_AVAILABLE = "available"
PRICE_CONTEXT_STATUS_NOT_AVAILABLE = "not_available"

NEGATIVE_PRICE_REASON = "negative_price"
LOW_PRICE_REASON = "low_price"
MEDIUM_RENEWABLE_SHARE_REASON = "medium_renewable_share"
HIGH_RENEWABLE_SHARE_REASON = "high_renewable_share"
RENEWABLE_ABOVE_CONSUMPTION_REASON = "renewable_generation_above_consumption"

NOTES = (
    "public market/system-level backtest only",
    "not customer-specific savings",
    (
        "customer-specific results require customer load, asset, tariff, and "
        "operational data"
    ),
    "read-only decision support",
    "no automatic control, dispatch, or activation",
)

JsonPayload = Mapping[str, Any]
FetchFn = Callable[[str], JsonPayload]
SleepFn = Callable[[float], None]


class PublicSurplusRiskBacktestError(RuntimeError):
    """Expected safe-fail error for public surplus-risk backtests."""


@dataclass(frozen=True)
class PublicSurplusRiskBacktestConfig:
    start_date: str
    end_date: str
    resolved_end: str
    price_areas: tuple[str, ...]
    dry_run: bool
    eds_request_delay_seconds: float
    eds_max_retries: int
    low_price_threshold_eur_per_mwh: float
    renewable_share_medium_threshold: float
    renewable_share_high_threshold: float
    top_risk_windows: int
    window_snapshot_only: bool


@dataclass(frozen=True)
class JoinedHourlyRiskRow:
    price_area: str
    timestamp_utc: str
    price_eur_per_mwh: float
    gross_consumption_mwh: float
    renewable_generation_mwh: float
    renewable_share: float
    risk_score: int
    risk_level: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class RiskWindow:
    price_area: str
    start_timestamp_utc: str
    end_timestamp_utc: str
    hour_count: int
    highest_risk_score: int
    highest_risk_level: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class RiskWindowSnapshot:
    price_area: str
    start_timestamp_utc: str
    end_timestamp_utc: str
    duration_hours: int
    highest_risk_score: int
    average_risk_score: float | None
    risk_level: str
    min_price_eur_per_mwh: float | None
    average_price_eur_per_mwh: float | None
    max_price_eur_per_mwh: float | None
    negative_price_hour_count: int | None
    low_price_hour_count: int | None
    price_context_status: str
    opportunity_signal_eur_per_mwh: float | None
    opportunity_signal_note: str
    average_renewable_share: float | None
    max_renewable_share: float | None
    top_reason_codes: Mapping[str, int] | None
    recommended_human_action: str


@dataclass(frozen=True)
class PriceAreaRiskSummary:
    price_area: str
    joined_hour_count: int
    skipped_row_count: int
    medium_risk_hour_count: int
    high_risk_hour_count: int
    risk_window_count: int
    highest_risk_score: int
    average_risk_score: float
    negative_price_hour_count: int
    low_price_hour_count: int
    average_renewable_share: float
    max_renewable_share: float
    top_reason_codes: Mapping[str, int]


@dataclass(frozen=True)
class PublicSurplusRiskBacktestSummary:
    period: str
    price_areas: tuple[str, ...]
    source: str
    datasets: tuple[str, ...]
    low_price_threshold_eur_per_mwh: float
    renewable_share_medium_threshold: float
    renewable_share_high_threshold: float
    dry_run: bool
    joined_rows: tuple[JoinedHourlyRiskRow, ...]
    risk_windows: tuple[RiskWindow, ...]
    area_summaries: tuple[PriceAreaRiskSummary, ...]
    notes: tuple[str, ...]
    file_written: bool
    database_write_performed: bool


def load_config(
    env: Mapping[str, str] | None = None,
    *,
    now_fn: Callable[[], Any] | None = None,
) -> PublicSurplusRiskBacktestConfig:
    safe_env = os.environ if env is None else env
    input_config = input_foundation.load_config(safe_env, now_fn=now_fn)
    low_price_threshold = _parse_nonnegative_float(
        safe_env.get(
            "BACKTEST_LOW_PRICE_THRESHOLD_EUR_PER_MWH",
            DEFAULT_LOW_PRICE_THRESHOLD_EUR_PER_MWH,
        ),
        "BACKTEST_LOW_PRICE_THRESHOLD_EUR_PER_MWH",
    )
    medium_threshold = _parse_share_threshold(
        safe_env.get(
            "BACKTEST_RENEWABLE_SHARE_MEDIUM_THRESHOLD",
            DEFAULT_RENEWABLE_SHARE_MEDIUM_THRESHOLD,
        ),
        "BACKTEST_RENEWABLE_SHARE_MEDIUM_THRESHOLD",
    )
    high_threshold = _parse_share_threshold(
        safe_env.get(
            "BACKTEST_RENEWABLE_SHARE_HIGH_THRESHOLD",
            DEFAULT_RENEWABLE_SHARE_HIGH_THRESHOLD,
        ),
        "BACKTEST_RENEWABLE_SHARE_HIGH_THRESHOLD",
    )
    if medium_threshold > high_threshold:
        raise PublicSurplusRiskBacktestError(
            "BACKTEST_RENEWABLE_SHARE_MEDIUM_THRESHOLD must be less than or "
            "equal to BACKTEST_RENEWABLE_SHARE_HIGH_THRESHOLD"
        )
    top_risk_windows = _parse_nonnegative_int(
        safe_env.get("BACKTEST_TOP_RISK_WINDOWS", DEFAULT_TOP_RISK_WINDOWS),
        "BACKTEST_TOP_RISK_WINDOWS",
    )
    window_snapshot_only = _parse_bool(
        safe_env.get(
            "BACKTEST_WINDOW_SNAPSHOT_ONLY",
            DEFAULT_WINDOW_SNAPSHOT_ONLY,
        ),
        "BACKTEST_WINDOW_SNAPSHOT_ONLY",
    )

    return PublicSurplusRiskBacktestConfig(
        start_date=input_config.start_date,
        end_date=input_config.end_date,
        resolved_end=input_config.resolved_end,
        price_areas=input_config.price_areas,
        dry_run=input_config.dry_run,
        eds_request_delay_seconds=input_config.eds_request_delay_seconds,
        eds_max_retries=input_config.eds_max_retries,
        low_price_threshold_eur_per_mwh=low_price_threshold,
        renewable_share_medium_threshold=medium_threshold,
        renewable_share_high_threshold=high_threshold,
        top_risk_windows=top_risk_windows,
        window_snapshot_only=window_snapshot_only,
    )


def run_public_surplus_risk_backtest(
    config: PublicSurplusRiskBacktestConfig,
    *,
    fetch: FetchFn,
    sleep_fn: SleepFn = input_foundation.time.sleep,
) -> PublicSurplusRiskBacktestSummary:
    input_config = input_foundation.PublicSurplusRiskInputConfig(
        start_date=config.start_date,
        end_date=config.end_date,
        resolved_end=config.resolved_end,
        price_areas=config.price_areas,
        dry_run=config.dry_run,
        eds_request_delay_seconds=config.eds_request_delay_seconds,
        eds_max_retries=config.eds_max_retries,
    )
    dataset_results = fetch_public_surplus_risk_rows(
        input_config,
        fetch=fetch,
        sleep_fn=sleep_fn,
    )

    return calculate_public_surplus_risk_backtest(
        period=f"{config.start_date} to {config.end_date}",
        price_areas=config.price_areas,
        dataset_results=dataset_results,
        low_price_threshold_eur_per_mwh=config.low_price_threshold_eur_per_mwh,
        renewable_share_medium_threshold=config.renewable_share_medium_threshold,
        renewable_share_high_threshold=config.renewable_share_high_threshold,
        dry_run=config.dry_run,
    )


def fetch_public_surplus_risk_rows(
    config: input_foundation.PublicSurplusRiskInputConfig,
    *,
    fetch: FetchFn,
    sleep_fn: SleepFn = input_foundation.time.sleep,
) -> tuple[input_foundation.DatasetAreaResult, ...]:
    results: list[input_foundation.DatasetAreaResult] = []
    for dataset in input_foundation.DATASETS:
        for price_area in config.price_areas:
            if results and config.eds_request_delay_seconds > 0:
                sleep_fn(config.eds_request_delay_seconds)
            results.append(
                input_foundation.fetch_dataset_area(
                    dataset=dataset,
                    price_area=price_area,
                    start_date=config.start_date,
                    end=config.resolved_end,
                    fetch=fetch,
                    request_delay_seconds=config.eds_request_delay_seconds,
                    sleep_fn=sleep_fn,
                )
            )

    return tuple(results)


def calculate_public_surplus_risk_backtest(
    *,
    period: str,
    price_areas: tuple[str, ...],
    dataset_results: Sequence[input_foundation.DatasetAreaResult],
    low_price_threshold_eur_per_mwh: float,
    renewable_share_medium_threshold: float,
    renewable_share_high_threshold: float,
    dry_run: bool,
) -> PublicSurplusRiskBacktestSummary:
    rows_by_dataset_area = {
        (result.dataset, result.price_area): tuple(result.normalized_rows)
        for result in dataset_results
    }

    joined_rows: list[JoinedHourlyRiskRow] = []
    skipped_by_area: dict[str, int] = defaultdict(int)
    for price_area in price_areas:
        price_rows = rows_by_dataset_area.get(
            (input_foundation.DAY_AHEAD_PRICES, price_area),
            (),
        )
        settlement_rows = rows_by_dataset_area.get(
            (input_foundation.PRODUCTION_CONSUMPTION_SETTLEMENT, price_area),
            (),
        )
        area_joined, area_skipped = join_and_score_hourly_rows(
            price_area=price_area,
            price_rows=price_rows,
            settlement_rows=settlement_rows,
            low_price_threshold_eur_per_mwh=low_price_threshold_eur_per_mwh,
            renewable_share_medium_threshold=renewable_share_medium_threshold,
            renewable_share_high_threshold=renewable_share_high_threshold,
        )
        joined_rows.extend(area_joined)
        skipped_by_area[price_area] += area_skipped

    joined_rows_tuple = tuple(
        sorted(joined_rows, key=lambda row: (row.price_area, row.timestamp_utc))
    )
    risk_windows = group_risk_windows(joined_rows_tuple)
    area_summaries = tuple(
        summarize_price_area(
            price_area=price_area,
            joined_rows=[
                row for row in joined_rows_tuple if row.price_area == price_area
            ],
            risk_windows=[
                window for window in risk_windows if window.price_area == price_area
            ],
            skipped_row_count=skipped_by_area[price_area],
            low_price_threshold_eur_per_mwh=low_price_threshold_eur_per_mwh,
        )
        for price_area in price_areas
    )

    return PublicSurplusRiskBacktestSummary(
        period=period,
        price_areas=price_areas,
        source=input_foundation.SOURCE,
        datasets=input_foundation.DATASETS,
        low_price_threshold_eur_per_mwh=low_price_threshold_eur_per_mwh,
        renewable_share_medium_threshold=renewable_share_medium_threshold,
        renewable_share_high_threshold=renewable_share_high_threshold,
        dry_run=dry_run,
        joined_rows=joined_rows_tuple,
        risk_windows=risk_windows,
        area_summaries=area_summaries,
        notes=NOTES,
        file_written=False,
        database_write_performed=False,
    )


def join_and_score_hourly_rows(
    *,
    price_area: str,
    price_rows: Sequence[Mapping[str, Any]],
    settlement_rows: Sequence[Mapping[str, Any]],
    low_price_threshold_eur_per_mwh: float,
    renewable_share_medium_threshold: float,
    renewable_share_high_threshold: float,
) -> tuple[tuple[JoinedHourlyRiskRow, ...], int]:
    hourly_prices, skipped_price_rows = aggregate_hourly_prices(
        price_rows,
        price_area=price_area,
    )
    settlement_by_hour: dict[str, Mapping[str, Any]] = {}
    skipped_rows = skipped_price_rows
    for row in settlement_rows:
        if row.get("price_area") != price_area:
            skipped_rows += 1
            continue
        timestamp = _hourly_timestamp_or_none(
            row.get("timestamp_utc"), source=row.get("source")
        )
        if timestamp is None:
            skipped_rows += 1
            continue
        settlement_by_hour.setdefault(timestamp, row)

    joined_rows: list[JoinedHourlyRiskRow] = []
    for timestamp in sorted(set(hourly_prices) | set(settlement_by_hour)):
        price = hourly_prices.get(timestamp)
        settlement = settlement_by_hour.get(timestamp)
        if price is None or settlement is None:
            skipped_rows += 1
            continue
        gross_consumption = _finite_float_or_none(
            settlement.get("gross_consumption_mwh")
        )
        renewable_generation = _finite_float_or_none(
            settlement.get("renewable_generation_mwh")
        )
        if (
            gross_consumption is None
            or renewable_generation is None
            or gross_consumption <= 0
        ):
            skipped_rows += 1
            continue

        renewable_share = renewable_generation / gross_consumption
        score, risk_level, reason_codes = score_joined_row(
            price_eur_per_mwh=price,
            gross_consumption_mwh=gross_consumption,
            renewable_generation_mwh=renewable_generation,
            renewable_share=renewable_share,
            low_price_threshold_eur_per_mwh=low_price_threshold_eur_per_mwh,
            renewable_share_medium_threshold=renewable_share_medium_threshold,
            renewable_share_high_threshold=renewable_share_high_threshold,
        )
        joined_rows.append(
            JoinedHourlyRiskRow(
                price_area=price_area,
                timestamp_utc=timestamp,
                price_eur_per_mwh=price,
                gross_consumption_mwh=gross_consumption,
                renewable_generation_mwh=renewable_generation,
                renewable_share=renewable_share,
                risk_score=score,
                risk_level=risk_level,
                reason_codes=reason_codes,
            )
        )

    return tuple(joined_rows), skipped_rows


def aggregate_hourly_prices(
    price_rows: Sequence[Mapping[str, Any]],
    *,
    price_area: str,
) -> tuple[dict[str, float], int]:
    prices_by_hour: dict[str, list[float]] = defaultdict(list)
    skipped_rows = 0
    for row in price_rows:
        if row.get("price_area") != price_area:
            skipped_rows += 1
            continue
        timestamp = _hourly_timestamp_or_none(
            row.get("timestamp_utc"), source=row.get("source")
        )
        price = _finite_float_or_none(row.get("day_ahead_price_eur_per_mwh"))
        if price is None:
            price = _finite_float_or_none(row.get("price_eur_per_mwh"))
        if timestamp is None or price is None:
            skipped_rows += 1
            continue
        prices_by_hour[timestamp].append(price)

    hourly_prices = {
        timestamp: sum(prices) / len(prices)
        for timestamp, prices in prices_by_hour.items()
        if prices
    }
    return hourly_prices, skipped_rows


def score_joined_row(
    *,
    price_eur_per_mwh: float,
    gross_consumption_mwh: float,
    renewable_generation_mwh: float,
    renewable_share: float,
    low_price_threshold_eur_per_mwh: float,
    renewable_share_medium_threshold: float,
    renewable_share_high_threshold: float,
) -> tuple[int, str, tuple[str, ...]]:
    score = 0
    reason_codes: list[str] = []

    if price_eur_per_mwh < 0:
        score += 35
        reason_codes.append(NEGATIVE_PRICE_REASON)
    if price_eur_per_mwh <= low_price_threshold_eur_per_mwh:
        score += 20
        reason_codes.append(LOW_PRICE_REASON)
    if renewable_share >= renewable_share_high_threshold:
        score += 40
        reason_codes.append(HIGH_RENEWABLE_SHARE_REASON)
    elif renewable_share >= renewable_share_medium_threshold:
        score += 25
        reason_codes.append(MEDIUM_RENEWABLE_SHARE_REASON)
    if renewable_generation_mwh > gross_consumption_mwh:
        score += 25
        reason_codes.append(RENEWABLE_ABOVE_CONSUMPTION_REASON)

    capped_score = min(100, score)
    return capped_score, _risk_level(capped_score), tuple(reason_codes)


def group_risk_windows(
    joined_rows: Sequence[JoinedHourlyRiskRow],
) -> tuple[RiskWindow, ...]:
    windows: list[RiskWindow] = []
    for price_area in sorted({row.price_area for row in joined_rows}):
        risk_rows = [
            row
            for row in joined_rows
            if row.price_area == price_area and row.risk_level in {"medium", "high"}
        ]
        current: list[JoinedHourlyRiskRow] = []
        previous_timestamp: datetime | None = None
        for row in sorted(risk_rows, key=lambda item: item.timestamp_utc):
            timestamp = _parse_utc_hour(row.timestamp_utc, allow_naive_utc=True)
            if (
                current
                and previous_timestamp is not None
                and timestamp != previous_timestamp + timedelta(hours=1)
            ):
                windows.append(_build_window(price_area, current))
                current = []
            current.append(row)
            previous_timestamp = timestamp
        if current:
            windows.append(_build_window(price_area, current))

    return tuple(windows)


def summarize_price_area(
    *,
    price_area: str,
    joined_rows: Sequence[JoinedHourlyRiskRow],
    risk_windows: Sequence[RiskWindow],
    skipped_row_count: int,
    low_price_threshold_eur_per_mwh: float,
) -> PriceAreaRiskSummary:
    if not joined_rows:
        return PriceAreaRiskSummary(
            price_area=price_area,
            joined_hour_count=0,
            skipped_row_count=skipped_row_count,
            medium_risk_hour_count=0,
            high_risk_hour_count=0,
            risk_window_count=0,
            highest_risk_score=0,
            average_risk_score=0.0,
            negative_price_hour_count=0,
            low_price_hour_count=0,
            average_renewable_share=0.0,
            max_renewable_share=0.0,
            top_reason_codes={},
        )

    reason_counter = Counter(
        reason_code
        for row in joined_rows
        for reason_code in row.reason_codes
    )
    top_reason_codes = dict(
        sorted(reason_counter.items(), key=lambda item: (-item[1], item[0]))[:5]
    )
    return PriceAreaRiskSummary(
        price_area=price_area,
        joined_hour_count=len(joined_rows),
        skipped_row_count=skipped_row_count,
        medium_risk_hour_count=sum(
            1 for row in joined_rows if row.risk_level == "medium"
        ),
        high_risk_hour_count=sum(1 for row in joined_rows if row.risk_level == "high"),
        risk_window_count=len(risk_windows),
        highest_risk_score=max(row.risk_score for row in joined_rows),
        average_risk_score=(
            sum(row.risk_score for row in joined_rows) / len(joined_rows)
        ),
        negative_price_hour_count=sum(
            1 for row in joined_rows if row.price_eur_per_mwh < 0
        ),
        low_price_hour_count=sum(
            1
            for row in joined_rows
            if row.price_eur_per_mwh <= low_price_threshold_eur_per_mwh
        ),
        average_renewable_share=(
            sum(row.renewable_share for row in joined_rows) / len(joined_rows)
        ),
        max_renewable_share=max(row.renewable_share for row in joined_rows),
        top_reason_codes=top_reason_codes,
    )


def print_summary(summary: PublicSurplusRiskBacktestSummary) -> None:
    print("Public surplus-risk backtest summary v1")
    print(f"period: {summary.period}")
    print(f"price_areas: {','.join(summary.price_areas)}")
    print(f"datasets: {','.join(summary.datasets)}")
    print(f"source: {summary.source}")
    print(
        "low_price_threshold_eur_per_mwh: "
        f"{_format_float(summary.low_price_threshold_eur_per_mwh)}"
    )
    print(
        "renewable_share_medium_threshold: "
        f"{_format_float(summary.renewable_share_medium_threshold)}"
    )
    print(
        "renewable_share_high_threshold: "
        f"{_format_float(summary.renewable_share_high_threshold)}"
    )
    print(f"dry_run: {str(summary.dry_run).lower()}")
    print(f"file_written: {str(summary.file_written).lower()}")
    print(
        "database_write_performed: "
        f"{str(summary.database_write_performed).lower()}"
    )
    print("area_summaries:")
    for area_summary in summary.area_summaries:
        print(f"  {area_summary.price_area}:")
        print(f"    joined_hour_count: {area_summary.joined_hour_count}")
        print(f"    skipped_row_count: {area_summary.skipped_row_count}")
        print(
            "    medium_risk_hour_count: "
            f"{area_summary.medium_risk_hour_count}"
        )
        print(f"    high_risk_hour_count: {area_summary.high_risk_hour_count}")
        print(f"    risk_window_count: {area_summary.risk_window_count}")
        print(f"    highest_risk_score: {area_summary.highest_risk_score}")
        print(
            "    average_risk_score: "
            f"{_format_float(area_summary.average_risk_score)}"
        )
        print(
            "    negative_price_hour_count: "
            f"{area_summary.negative_price_hour_count}"
        )
        print(f"    low_price_hour_count: {area_summary.low_price_hour_count}")
        print(
            "    average_renewable_share: "
            f"{_format_float(area_summary.average_renewable_share)}"
        )
        print(
            "    max_renewable_share: "
            f"{_format_float(area_summary.max_renewable_share)}"
        )
        print("    top_reason_codes:")
        if area_summary.top_reason_codes:
            for reason_code, count in area_summary.top_reason_codes.items():
                print(f"      {reason_code}: {count}")
        else:
            print("      none: 0")
    print("risk_windows:")
    if summary.risk_windows:
        for window in summary.risk_windows:
            print(f"  - price_area: {window.price_area}")
            print(f"    start_timestamp_utc: {window.start_timestamp_utc}")
            print(f"    end_timestamp_utc: {window.end_timestamp_utc}")
            print(f"    hour_count: {window.hour_count}")
            print(f"    highest_risk_score: {window.highest_risk_score}")
            print(f"    highest_risk_level: {window.highest_risk_level}")
            print(f"    reason_codes: {','.join(window.reason_codes)}")
    else:
        print("  - none")
    print("notes:")
    for note in summary.notes:
        print(f"  - {note}")


def build_risk_window_snapshots(
    summary: PublicSurplusRiskBacktestSummary,
    *,
    top_per_price_area: int,
) -> tuple[RiskWindowSnapshot, ...]:
    snapshots: list[RiskWindowSnapshot] = []
    for price_area in summary.price_areas:
        sorted_windows = sorted(
            (
                window
                for window in summary.risk_windows
                if window.price_area == price_area
            ),
            key=lambda window: (
                -window.highest_risk_score,
                -window.hour_count,
                window.start_timestamp_utc,
            ),
        )
        for window in sorted_windows[:top_per_price_area]:
            snapshots.append(_build_window_snapshot(summary, window))

    return tuple(snapshots)


def print_window_snapshot(
    summary: PublicSurplusRiskBacktestSummary,
    *,
    top_per_price_area: int,
) -> None:
    snapshots = build_risk_window_snapshots(
        summary,
        top_per_price_area=top_per_price_area,
    )
    print("Public surplus-risk window snapshot v1")
    print(f"period: {summary.period}")
    print(f"price_areas: {','.join(summary.price_areas)}")
    print(f"datasets: {','.join(summary.datasets)}")
    print(f"source: {summary.source}")
    print(f"dry_run: {str(summary.dry_run).lower()}")
    print(f"file_written: {str(summary.file_written).lower()}")
    print(
        "database_write_performed: "
        f"{str(summary.database_write_performed).lower()}"
    )
    print(f"top_risk_windows_per_price_area: {top_per_price_area}")
    print("top_risk_windows:")
    if not snapshots:
        print("  - none")
    for price_area in summary.price_areas:
        area_snapshots = [
            snapshot
            for snapshot in snapshots
            if snapshot.price_area == price_area
        ]
        if not area_snapshots:
            print(f"  {price_area}: none")
            continue
        print(f"  {price_area}:")
        for snapshot in area_snapshots:
            print(f"    - price_area: {snapshot.price_area}")
            print(
                "      start_timestamp_utc: "
                f"{snapshot.start_timestamp_utc}"
            )
            print(f"      end_timestamp_utc: {snapshot.end_timestamp_utc}")
            print(f"      duration_hours: {snapshot.duration_hours}")
            print(
                "      highest_risk_score: "
                f"{snapshot.highest_risk_score}"
            )
            print(
                "      average_risk_score: "
                f"{_format_optional_float(snapshot.average_risk_score)}"
            )
            print(f"      risk_level: {snapshot.risk_level}")
            print(
                "      min_price_eur_per_mwh: "
                f"{_format_optional_float(snapshot.min_price_eur_per_mwh)}"
            )
            print(
                "      average_price_eur_per_mwh: "
                f"{_format_optional_float(snapshot.average_price_eur_per_mwh)}"
            )
            print(
                "      max_price_eur_per_mwh: "
                f"{_format_optional_float(snapshot.max_price_eur_per_mwh)}"
            )
            print(
                "      negative_price_hour_count: "
                f"{_format_optional_int(snapshot.negative_price_hour_count)}"
            )
            print(
                "      low_price_hour_count: "
                f"{_format_optional_int(snapshot.low_price_hour_count)}"
            )
            print(
                "      price_context_status: "
                f"{snapshot.price_context_status}"
            )
            print(
                "      opportunity_signal_eur_per_mwh: "
                f"{_format_optional_float(snapshot.opportunity_signal_eur_per_mwh)}"
            )
            print(
                "      opportunity_signal_note: "
                f"{snapshot.opportunity_signal_note}"
            )
            print(
                "      average_renewable_share: "
                f"{_format_optional_float(snapshot.average_renewable_share)}"
            )
            print(
                "      max_renewable_share: "
                f"{_format_optional_float(snapshot.max_renewable_share)}"
            )
            print(
                "      top_reason_codes: "
                f"{_format_reason_codes(snapshot.top_reason_codes)}"
            )
            print(
                "      recommended_human_action: "
                f"{snapshot.recommended_human_action}"
            )
    print("notes:")
    for note in summary.notes:
        print(f"  - {note}")


def main() -> int:
    try:
        config = load_config()

        def fetch(url: str) -> JsonPayload:
            return input_foundation.market_input.fetch_json(
                url,
                max_retries=config.eds_max_retries,
            )

        summary = run_public_surplus_risk_backtest(config, fetch=fetch)
    except (
        PublicSurplusRiskBacktestError,
        input_foundation.PublicSurplusRiskInputError,
        input_foundation.market_input.BacktestInputError,
    ) as exc:
        print(f"Public surplus-risk backtest failed: {exc}", file=sys.stderr)
        return 1
    except urllib.error.HTTPError as exc:
        print(
            "Public surplus-risk backtest failed: "
            f"EDS HTTP {exc.code} {exc.reason}",
            file=sys.stderr,
        )
        return 1
    except urllib.error.URLError as exc:
        print(
            "Public surplus-risk backtest failed: "
            f"EDS API unreachable: {exc.reason}",
            file=sys.stderr,
        )
        return 1
    except TimeoutError:
        print(
            "Public surplus-risk backtest failed: "
            "EDS API unreachable: request timed out",
            file=sys.stderr,
        )
        return 1
    except json.JSONDecodeError as exc:
        print(
            "Public surplus-risk backtest failed: "
            f"invalid JSON from EDS: {exc}",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(f"Public surplus-risk backtest failed: {exc}", file=sys.stderr)
        return 1

    if config.window_snapshot_only:
        print_window_snapshot(
            summary,
            top_per_price_area=config.top_risk_windows,
        )
    else:
        print_summary(summary)
    return 0


def _build_window_snapshot(
    summary: PublicSurplusRiskBacktestSummary,
    window: RiskWindow,
) -> RiskWindowSnapshot:
    rows = _joined_rows_for_window(summary.joined_rows, window)
    average_risk_score: float | None = None
    min_price_eur_per_mwh: float | None = None
    average_price_eur_per_mwh: float | None = None
    max_price_eur_per_mwh: float | None = None
    negative_price_hour_count: int | None = None
    low_price_hour_count: int | None = None
    price_context_status = PRICE_CONTEXT_STATUS_NOT_AVAILABLE
    opportunity_signal_eur_per_mwh: float | None = None
    opportunity_signal_note = (
        "Public DayAheadPrices rows were unavailable or insufficient for this "
        "window."
    )
    average_renewable_share: float | None = None
    max_renewable_share: float | None = None
    top_reason_codes: Mapping[str, int] | None = None

    if rows:
        window_prices = [row.price_eur_per_mwh for row in rows]
        min_price_eur_per_mwh = min(window_prices)
        average_price_eur_per_mwh = sum(window_prices) / len(window_prices)
        max_price_eur_per_mwh = max(window_prices)
        average_risk_score = sum(row.risk_score for row in rows) / len(rows)
        negative_price_hour_count = sum(
            1 for price in window_prices if price < 0
        )
        low_price_hour_count = sum(
            1
            for price in window_prices
            if price <= summary.low_price_threshold_eur_per_mwh
        )
        price_context_status = PRICE_CONTEXT_STATUS_AVAILABLE
        opportunity_signal_eur_per_mwh = max(
            0.0,
            summary.low_price_threshold_eur_per_mwh
            - average_price_eur_per_mwh,
        )
        opportunity_signal_note = (
            "Public market signal only: max(0, public low-price threshold "
            f"{_format_float(summary.low_price_threshold_eur_per_mwh)} "
            "EUR/MWh - average window DayAheadPrices EUR/MWh). Customer "
            "load, flexibility, tariff, and constraints are excluded."
        )
        average_renewable_share = (
            sum(row.renewable_share for row in rows) / len(rows)
        )
        max_renewable_share = max(row.renewable_share for row in rows)
        reason_counter = Counter(
            reason_code for row in rows for reason_code in row.reason_codes
        )
        top_reason_codes = dict(
            sorted(reason_counter.items(), key=lambda item: (-item[1], item[0]))[
                :5
            ]
        )

    return RiskWindowSnapshot(
        price_area=window.price_area,
        start_timestamp_utc=window.start_timestamp_utc,
        end_timestamp_utc=window.end_timestamp_utc,
        duration_hours=window.hour_count,
        highest_risk_score=window.highest_risk_score,
        average_risk_score=average_risk_score,
        risk_level=window.highest_risk_level,
        min_price_eur_per_mwh=min_price_eur_per_mwh,
        average_price_eur_per_mwh=average_price_eur_per_mwh,
        max_price_eur_per_mwh=max_price_eur_per_mwh,
        negative_price_hour_count=negative_price_hour_count,
        low_price_hour_count=low_price_hour_count,
        price_context_status=price_context_status,
        opportunity_signal_eur_per_mwh=opportunity_signal_eur_per_mwh,
        opportunity_signal_note=opportunity_signal_note,
        average_renewable_share=average_renewable_share,
        max_renewable_share=max_renewable_share,
        top_reason_codes=top_reason_codes,
        recommended_human_action=_recommended_human_action(
            window.highest_risk_level
        ),
    )


def _joined_rows_for_window(
    joined_rows: Sequence[JoinedHourlyRiskRow],
    window: RiskWindow,
) -> tuple[JoinedHourlyRiskRow, ...]:
    start = _parse_utc_hour(window.start_timestamp_utc, allow_naive_utc=True)
    end = _parse_utc_hour(window.end_timestamp_utc, allow_naive_utc=True)
    return tuple(
        row
        for row in joined_rows
        if row.price_area == window.price_area
        and start <= _parse_utc_hour(row.timestamp_utc, allow_naive_utc=True) <= end
    )


def _recommended_human_action(risk_level: str) -> str:
    if risk_level == "high":
        return (
            "Human review: prioritize this public system window for comparison "
            "with operations and constraints before any manual decision."
        )
    return (
        "Human review: compare this public system window with operations and "
        "constraints before any manual decision."
    )


def _build_window(price_area: str, rows: Sequence[JoinedHourlyRiskRow]) -> RiskWindow:
    highest_score = max(row.risk_score for row in rows)
    reason_codes = tuple(
        sorted({reason_code for row in rows for reason_code in row.reason_codes})
    )
    return RiskWindow(
        price_area=price_area,
        start_timestamp_utc=rows[0].timestamp_utc,
        end_timestamp_utc=rows[-1].timestamp_utc,
        hour_count=len(rows),
        highest_risk_score=highest_score,
        highest_risk_level=_risk_level(highest_score),
        reason_codes=reason_codes,
    )


def _risk_level(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _hourly_timestamp_or_none(value: Any, *, source: Any = None) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = _parse_utc_hour(
            value,
            allow_naive_utc=source in {
                "Energi Data Service:DayAheadPrices",
                "Energi Data Service:ProductionConsumptionSettlement",
            },
        )
    except ValueError:
        return None
    return parsed.strftime("%Y-%m-%dT%H:00:00")


def _parse_utc_hour(value: str, *, allow_naive_utc: bool = False) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    if "T" not in normalized:
        raise ValueError("Hourly timestamp must include a time")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        if not allow_naive_utc:
            raise PublicSurplusRiskBacktestError(
                "Naive timestamp has no documented UTC source contract"
            )
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(
        minute=0, second=0, microsecond=0, tzinfo=None
    )


def _finite_float_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def _parse_nonnegative_float(raw_value: str | None, env_name: str) -> float:
    parsed = _parse_float(raw_value, env_name)
    if parsed < 0:
        raise PublicSurplusRiskBacktestError(f"{env_name} must be non-negative")
    return parsed


def _parse_share_threshold(raw_value: str | None, env_name: str) -> float:
    parsed = _parse_float(raw_value, env_name)
    if parsed < 0:
        raise PublicSurplusRiskBacktestError(f"{env_name} must be non-negative")
    return parsed


def _parse_float(raw_value: str | None, env_name: str) -> float:
    try:
        parsed = float((raw_value or "").strip())
    except ValueError as exc:
        raise PublicSurplusRiskBacktestError(f"{env_name} must be numeric") from exc
    if not math.isfinite(parsed):
        raise PublicSurplusRiskBacktestError(f"{env_name} must be finite")
    return parsed


def _parse_nonnegative_int(raw_value: str | None, env_name: str) -> int:
    try:
        parsed = int((raw_value or "").strip())
    except ValueError as exc:
        raise PublicSurplusRiskBacktestError(
            f"{env_name} must be a non-negative integer"
        ) from exc
    if parsed < 0:
        raise PublicSurplusRiskBacktestError(
            f"{env_name} must be a non-negative integer"
        )
    return parsed


def _parse_bool(raw_value: str | None, env_name: str) -> bool:
    normalized = (raw_value or "").strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise PublicSurplusRiskBacktestError(f"{env_name} must be true or false")


def _format_float(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _format_optional_float(value: float | None) -> str:
    if value is None:
        return "not_calculated"
    return _format_float(value)


def _format_optional_int(value: int | None) -> str:
    if value is None:
        return "not_calculated"
    return str(value)


def _format_reason_codes(reason_codes: Mapping[str, int] | None) -> str:
    if reason_codes is None:
        return "not_calculated"
    if not reason_codes:
        return "none"
    return ", ".join(
        f"{reason_code}:{count}" for reason_code, count in reason_codes.items()
    )


if __name__ == "__main__":
    raise SystemExit(main())
