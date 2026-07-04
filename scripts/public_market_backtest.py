#!/usr/bin/env python3
"""Read-only public DK1/DK2 market price-opportunity backtest v0."""

from __future__ import annotations

import json
import math
import os
import sys
import urllib.error
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import public_market_backtest_input as backtest_input  # noqa: E402


DEFAULT_LOW_PRICE_THRESHOLD_EUR_PER_MWH = "25"

JsonPayload = Mapping[str, Any]
FetchFn = Callable[[str], JsonPayload]
SleepFn = Callable[[float], None]

NOTES = (
    "public market/system-level backtest only",
    "not customer-specific savings",
    (
        "customer-specific results require customer load, asset, tariff, and "
        "operational data"
    ),
    (
        "v0 uses spot/day-ahead prices only from Energi Data Service "
        "DayAheadPrices, not full surplus-production data"
    ),
)


class PublicMarketBacktestError(RuntimeError):
    """Expected safe-fail error for public market price-opportunity backtests."""


@dataclass(frozen=True)
class PublicMarketBacktestConfig:
    start_date: str
    end_date: str
    resolved_end: str
    price_areas: tuple[str, ...]
    dry_run: bool
    eds_request_delay_seconds: float
    eds_max_retries: int
    low_price_threshold_eur_per_mwh: float


@dataclass(frozen=True)
class PriceAreaBacktestResult:
    price_area: str
    record_count: int
    earliest_timestamp_utc: str
    latest_timestamp_utc: str
    average_price_eur_per_mwh: float
    minimum_price_eur_per_mwh: float
    maximum_price_eur_per_mwh: float
    negative_price_record_count: int
    low_price_record_count: int
    low_price_share: float
    opportunity_eur_per_mwh_signal: float
    scenario_value_per_1_mwh: float
    scenario_label: str


@dataclass(frozen=True)
class PublicMarketBacktestSummary:
    period: str
    price_areas: tuple[str, ...]
    source: str
    dataset: str
    low_price_threshold_eur_per_mwh: float
    dry_run: bool
    area_results: tuple[PriceAreaBacktestResult, ...]
    notes: tuple[str, ...]
    file_written: bool
    database_write_performed: bool


def load_config(
    env: Mapping[str, str] | None = None,
    *,
    now_fn: Callable[[], datetime] | None = None,
) -> PublicMarketBacktestConfig:
    safe_env = os.environ if env is None else env
    input_config = backtest_input.load_config(safe_env, now_fn=now_fn)
    threshold = _parse_nonnegative_float(
        safe_env.get(
            "BACKTEST_LOW_PRICE_THRESHOLD_EUR_PER_MWH",
            DEFAULT_LOW_PRICE_THRESHOLD_EUR_PER_MWH,
        ),
        "BACKTEST_LOW_PRICE_THRESHOLD_EUR_PER_MWH",
    )

    return PublicMarketBacktestConfig(
        start_date=input_config.start_date,
        end_date=input_config.end_date,
        resolved_end=input_config.resolved_end,
        price_areas=input_config.price_areas,
        dry_run=input_config.dry_run,
        eds_request_delay_seconds=input_config.eds_request_delay_seconds,
        eds_max_retries=input_config.eds_max_retries,
        low_price_threshold_eur_per_mwh=threshold,
    )


def run_public_market_backtest(
    config: PublicMarketBacktestConfig,
    *,
    fetch: FetchFn,
    sleep_fn: SleepFn = backtest_input.time.sleep,
) -> PublicMarketBacktestSummary:
    input_config = backtest_input.BacktestInputConfig(
        start_date=config.start_date,
        end_date=config.end_date,
        resolved_end=config.resolved_end,
        price_areas=config.price_areas,
        dry_run=config.dry_run,
        eds_request_delay_seconds=config.eds_request_delay_seconds,
        eds_max_retries=config.eds_max_retries,
    )
    input_results = _fetch_results_from_input(
        input_config,
        fetch=fetch,
        sleep_fn=sleep_fn,
    )
    input_summary = backtest_input.build_summary(input_config, list(input_results))

    area_results = tuple(
        calculate_price_area_backtest(
            result.price_area,
            result.normalized_rows,
            low_price_threshold_eur_per_mwh=config.low_price_threshold_eur_per_mwh,
        )
        for result in input_results
    )
    if not area_results:
        raise PublicMarketBacktestError(
            "No public market backtest results were produced"
        )

    return PublicMarketBacktestSummary(
        period=input_summary.period,
        price_areas=config.price_areas,
        source="Energi Data Service",
        dataset=backtest_input.DAY_AHEAD_PRICES,
        low_price_threshold_eur_per_mwh=config.low_price_threshold_eur_per_mwh,
        dry_run=config.dry_run,
        area_results=area_results,
        notes=NOTES,
        file_written=False,
        database_write_performed=False,
    )


def fetch_public_market_backtest_rows(
    config: PublicMarketBacktestConfig,
    *,
    fetch: FetchFn,
    sleep_fn: SleepFn = backtest_input.time.sleep,
) -> tuple[backtest_input.DatasetAreaResult, ...]:
    input_config = backtest_input.BacktestInputConfig(
        start_date=config.start_date,
        end_date=config.end_date,
        resolved_end=config.resolved_end,
        price_areas=config.price_areas,
        dry_run=config.dry_run,
        eds_request_delay_seconds=config.eds_request_delay_seconds,
        eds_max_retries=config.eds_max_retries,
    )
    return _fetch_results_from_input(input_config, fetch=fetch, sleep_fn=sleep_fn)


def calculate_price_area_backtest(
    price_area: str,
    normalized_rows: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    *,
    low_price_threshold_eur_per_mwh: float,
) -> PriceAreaBacktestResult:
    if price_area not in backtest_input.ALLOWED_PRICE_AREAS:
        raise PublicMarketBacktestError("price_area must be DK1 or DK2")
    if not normalized_rows:
        raise PublicMarketBacktestError(f"Required records missing for {price_area}")

    prices: list[float] = []
    timestamps: list[str] = []
    for index, row in enumerate(normalized_rows):
        if row.get("price_area") != price_area:
            raise PublicMarketBacktestError(
                f"Record {index} did not match requested price area {price_area}"
            )
        timestamps.append(_require_timestamp(row, index))
        prices.append(_require_price_eur(row, index))

    record_count = len(prices)
    average_price = sum(prices) / record_count
    minimum_price = min(prices)
    maximum_price = max(prices)
    negative_count = sum(1 for price in prices if price < 0)
    low_prices = [
        price for price in prices if price <= low_price_threshold_eur_per_mwh
    ]
    low_count = len(low_prices)
    low_price_share = low_count / record_count
    low_price_average = sum(low_prices) / low_count if low_prices else average_price
    opportunity_signal = max(0.0, average_price - low_price_average)

    return PriceAreaBacktestResult(
        price_area=price_area,
        record_count=record_count,
        earliest_timestamp_utc=min(timestamps),
        latest_timestamp_utc=max(timestamps),
        average_price_eur_per_mwh=average_price,
        minimum_price_eur_per_mwh=minimum_price,
        maximum_price_eur_per_mwh=maximum_price,
        negative_price_record_count=negative_count,
        low_price_record_count=low_count,
        low_price_share=low_price_share,
        opportunity_eur_per_mwh_signal=opportunity_signal,
        scenario_value_per_1_mwh=opportunity_signal,
        scenario_label=(
            "scenario only: EUR value for 1 MWh using observed market price "
            "spread; not revenue, profit, savings, tariff, tax, fee, load, MW, "
            "or asset behavior"
        ),
    )


def print_summary(summary: PublicMarketBacktestSummary) -> None:
    print("Public market price-opportunity backtest summary")
    print(f"period: {summary.period}")
    print(f"price_areas: {','.join(summary.price_areas)}")
    print(f"dataset: {summary.dataset}")
    print(f"source: {summary.source}")
    print(
        "low_price_threshold_eur_per_mwh: "
        f"{_format_float(summary.low_price_threshold_eur_per_mwh)}"
    )
    print(f"dry_run: {str(summary.dry_run).lower()}")
    print(f"file_written: {str(summary.file_written).lower()}")
    print(
        "database_write_performed: "
        f"{str(summary.database_write_performed).lower()}"
    )
    print("area_results:")
    for result in summary.area_results:
        print(f"  {result.price_area}:")
        print(f"    record_count: {result.record_count}")
        print(f"    earliest_timestamp_utc: {result.earliest_timestamp_utc}")
        print(f"    latest_timestamp_utc: {result.latest_timestamp_utc}")
        print(
            "    average_price_eur_per_mwh: "
            f"{_format_float(result.average_price_eur_per_mwh)}"
        )
        print(
            "    minimum_price_eur_per_mwh: "
            f"{_format_float(result.minimum_price_eur_per_mwh)}"
        )
        print(
            "    maximum_price_eur_per_mwh: "
            f"{_format_float(result.maximum_price_eur_per_mwh)}"
        )
        print(
            "    negative_price_record_count: "
            f"{result.negative_price_record_count}"
        )
        print(f"    low_price_record_count: {result.low_price_record_count}")
        print(f"    low_price_share: {_format_float(result.low_price_share)}")
        print(
            "    opportunity_eur_per_mwh_signal: "
            f"{_format_float(result.opportunity_eur_per_mwh_signal)}"
        )
        print(
            "    scenario_value_per_1_mwh: "
            f"{_format_float(result.scenario_value_per_1_mwh)}"
        )
        print(f"    scenario_label: {result.scenario_label}")
    print("notes:")
    for note in summary.notes:
        print(f"  - {note}")


def main() -> int:
    try:
        config = load_config()

        def fetch(url: str) -> JsonPayload:
            return backtest_input.fetch_json(url, max_retries=config.eds_max_retries)

        summary = run_public_market_backtest(config, fetch=fetch)
    except (PublicMarketBacktestError, backtest_input.BacktestInputError) as exc:
        print(f"Public market backtest failed: {exc}", file=sys.stderr)
        return 1
    except urllib.error.HTTPError as exc:
        print(
            f"Public market backtest failed: EDS HTTP {exc.code} {exc.reason}",
            file=sys.stderr,
        )
        return 1
    except urllib.error.URLError as exc:
        print(
            f"Public market backtest failed: EDS API unreachable: {exc.reason}",
            file=sys.stderr,
        )
        return 1
    except TimeoutError:
        print(
            "Public market backtest failed: EDS API unreachable: request timed out",
            file=sys.stderr,
        )
        return 1
    except json.JSONDecodeError as exc:
        print(
            f"Public market backtest failed: invalid JSON from EDS: {exc}",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(f"Public market backtest failed: {exc}", file=sys.stderr)
        return 1

    print_summary(summary)
    return 0


def _fetch_results_from_input(
    config: backtest_input.BacktestInputConfig,
    *,
    fetch: FetchFn,
    sleep_fn: SleepFn,
) -> tuple[backtest_input.DatasetAreaResult, ...]:
    results: list[backtest_input.DatasetAreaResult] = []
    for price_area in config.price_areas:
        if results and config.eds_request_delay_seconds > 0:
            sleep_fn(config.eds_request_delay_seconds)
        results.append(
            backtest_input.fetch_dataset_area(
                dataset=backtest_input.DAY_AHEAD_PRICES,
                price_area=price_area,
                start_date=config.start_date,
                end=config.resolved_end,
                fetch=fetch,
                request_delay_seconds=config.eds_request_delay_seconds,
                sleep_fn=sleep_fn,
            )
        )

    return tuple(results)


def _parse_nonnegative_float(raw_value: str | None, env_name: str) -> float:
    try:
        parsed = float((raw_value or "").strip())
    except ValueError as exc:
        raise PublicMarketBacktestError(
            f"{env_name} must be a non-negative number"
        ) from exc

    if parsed < 0 or not math.isfinite(parsed):
        raise PublicMarketBacktestError(f"{env_name} must be a non-negative number")

    return parsed


def _require_timestamp(row: Mapping[str, Any], index: int) -> str:
    timestamp = row.get("timestamp_utc")
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise PublicMarketBacktestError(f"Record {index} has invalid timestamp_utc")

    return timestamp


def _require_price_eur(row: Mapping[str, Any], index: int) -> float:
    value = row.get("price_eur_per_mwh")
    if isinstance(value, bool) or value is None:
        raise PublicMarketBacktestError(
            f"Record {index} has invalid price_eur_per_mwh"
        )
    try:
        price = float(value)
    except (TypeError, ValueError) as exc:
        raise PublicMarketBacktestError(
            f"Record {index} has invalid price_eur_per_mwh"
        ) from exc
    if not math.isfinite(price):
        raise PublicMarketBacktestError(
            f"Record {index} has invalid price_eur_per_mwh"
        )

    return price


def _format_float(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


if __name__ == "__main__":
    raise SystemExit(main())
