#!/usr/bin/env python3
"""Read-only public DK1/DK2 surplus-risk input preview for backtest v1."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import public_market_backtest_input as market_input  # noqa: E402


DAY_AHEAD_PRICES = "DayAheadPrices"
PRODUCTION_CONSUMPTION_SETTLEMENT = "ProductionConsumptionSettlement"
DATASETS = (DAY_AHEAD_PRICES, PRODUCTION_CONSUMPTION_SETTLEMENT)
SOURCE = "Energi Data Service"
MIN_LIMIT = 1
NOTE = (
    "public market/system-level data only, not customer-specific savings; "
    "input foundation only, full surplus-risk scoring comes next"
)

JsonPayload = Mapping[str, Any]
FetchFn = Callable[[str], JsonPayload]
SleepFn = Callable[[float], None]

WIND_GENERATION_FIELDS = (
    "OnshoreWindGe50kW_MWh",
    "OnshoreWindLt50kW_MWh",
    "OffshoreWindGe100MW_MWh",
    "OffshoreWindLt100MW_MWh",
)
SOLAR_GENERATION_FIELDS = (
    "SolarPowerGe10Lt40kW_MWh",
    "SolarPowerGe40kW_MWh",
    "SolarPowerLt10kW_MWh",
    "SolarPowerSelfConMWh",
)
HYDRO_RENEWABLE_FIELDS = (
    "HydroPowerMWh",
    "HydroPower_MWh",
    "HydroPower",
    "OtherRenewableMWh",
    "OtherRenewable_MWh",
    "OtherRenewable",
)
PRODUCTION_TOTAL_FIELDS = (
    "ProductionTotalMWh",
    "ProductionTotal_MWh",
    "TotalProductionMWh",
    "TotalProduction_MWh",
)
EXCHANGE_FIELD_MAP = {
    "ExchangeGE_MWh": "exchange_ge_mwh",
    "ExchangeNO_MWh": "exchange_no_mwh",
    "ExchangeSE_MWh": "exchange_se_mwh",
    "ExchangeGB_MWh": "exchange_gb_mwh",
    "ExchangeNL_MWh": "exchange_nl_mwh",
    "ExchangeGreatBelt_MWh": "exchange_great_belt_mwh",
}
PRODUCTION_CONSUMPTION_OPTIONAL_FIELDS = (
    "GrossConsumptionMWh",
    *WIND_GENERATION_FIELDS,
    *SOLAR_GENERATION_FIELDS,
    "CentralPowerMWh",
    "LocalPowerMWh",
    *EXCHANGE_FIELD_MAP.keys(),
)


class PublicSurplusRiskInputError(RuntimeError):
    """Expected safe-fail error for public surplus-risk input preparation."""


@dataclass(frozen=True)
class PublicSurplusRiskInputConfig:
    start_date: str
    end_date: str
    resolved_end: str
    price_areas: tuple[str, ...]
    dry_run: bool
    eds_request_delay_seconds: float
    eds_max_retries: int


@dataclass(frozen=True)
class DatasetAreaResult:
    dataset: str
    price_area: str
    request_urls: tuple[str, ...]
    raw_record_count: int
    normalized_record_count: int
    earliest_timestamp_utc: str
    latest_timestamp_utc: str
    normalized_rows: tuple[dict[str, Any], ...]
    missing_field_warnings: tuple[str, ...]


@dataclass(frozen=True)
class PublicSurplusRiskInputSummary:
    period: str
    price_areas: tuple[str, ...]
    datasets_requested: tuple[str, ...]
    record_counts: Mapping[str, int]
    normalized_row_counts: Mapping[str, int]
    dataset_timestamp_ranges: Mapping[str, Mapping[str, str]]
    missing_field_warnings: tuple[str, ...]
    dry_run: bool
    source: str
    note: str
    file_written: bool
    database_write_performed: bool


def load_config(
    env: Mapping[str, str] | None = None,
    *,
    now_fn: Callable[[], Any] | None = None,
) -> PublicSurplusRiskInputConfig:
    input_config = market_input.load_config(
        os.environ if env is None else env,
        now_fn=now_fn,
    )
    return PublicSurplusRiskInputConfig(
        start_date=input_config.start_date,
        end_date=input_config.end_date,
        resolved_end=input_config.resolved_end,
        price_areas=input_config.price_areas,
        dry_run=input_config.dry_run,
        eds_request_delay_seconds=input_config.eds_request_delay_seconds,
        eds_max_retries=input_config.eds_max_retries,
    )


def run_public_surplus_risk_backtest_input(
    config: PublicSurplusRiskInputConfig,
    *,
    fetch: FetchFn,
    sleep_fn: SleepFn = time.sleep,
) -> PublicSurplusRiskInputSummary:
    results: list[DatasetAreaResult] = []
    for dataset in DATASETS:
        for price_area in config.price_areas:
            if results:
                _sleep_if_needed(config.eds_request_delay_seconds, sleep_fn)
            results.append(
                fetch_dataset_area(
                    dataset=dataset,
                    price_area=price_area,
                    start_date=config.start_date,
                    end=config.resolved_end,
                    fetch=fetch,
                    request_delay_seconds=config.eds_request_delay_seconds,
                    sleep_fn=sleep_fn,
                )
            )

    return build_summary(config, results)


def fetch_dataset_area(
    *,
    dataset: str,
    price_area: str,
    start_date: str,
    end: str,
    fetch: FetchFn,
    request_delay_seconds: float = 0.0,
    sleep_fn: SleepFn = time.sleep,
) -> DatasetAreaResult:
    if dataset not in DATASETS:
        raise PublicSurplusRiskInputError(f"Unsupported required dataset: {dataset}")

    all_records: list[Any] = []
    request_urls: list[str] = []
    normalized_by_instant: dict[tuple[str, str, str], dict[str, Any]] = {}
    missing_field_warnings: set[str] = set()

    for chunk_start, chunk_end in market_input.build_request_chunks(
        start_date=start_date,
        end=end,
    ):
        if request_urls:
            _sleep_if_needed(request_delay_seconds, sleep_fn)
        request_url = build_backtest_eds_url(
            dataset=dataset,
            price_area=price_area,
            start=chunk_start,
            end=chunk_end,
        )
        request_urls.append(request_url)
        payload = fetch(request_url)
        records = market_input.extract_records(dict(payload))
        if not records:
            raise PublicSurplusRiskInputError(
                f"Required EDS records missing for {dataset} {price_area}"
            )
        all_records.extend(records)

        normalized_rows, warnings = normalize_records(dataset, records)
        missing_field_warnings.update(warnings)
        for normalized_row in normalized_rows:
            if normalized_row["price_area"] != price_area:
                raise PublicSurplusRiskInputError(
                    "EDS records did not match requested price area for "
                    f"{dataset} {price_area}"
                )
            normalized_by_instant.setdefault(
                (dataset, price_area, str(normalized_row["timestamp_utc"])),
                normalized_row,
            )

    normalized_rows = list(normalized_by_instant.values())
    if not normalized_rows:
        raise PublicSurplusRiskInputError(
            f"Required normalized records missing for {dataset} {price_area}"
        )

    timestamps = sorted(str(row["timestamp_utc"]) for row in normalized_rows)
    return DatasetAreaResult(
        dataset=dataset,
        price_area=price_area,
        request_urls=tuple(request_urls),
        raw_record_count=len(all_records),
        normalized_record_count=len(normalized_rows),
        earliest_timestamp_utc=timestamps[0],
        latest_timestamp_utc=timestamps[-1],
        normalized_rows=tuple(normalized_rows),
        missing_field_warnings=tuple(sorted(missing_field_warnings)),
    )


def build_backtest_eds_url(
    *,
    dataset: str,
    price_area: str,
    start: str,
    end: str,
    limit: int = market_input.MAX_LIMIT,
) -> str:
    if dataset not in DATASETS:
        raise PublicSurplusRiskInputError(f"Unsupported required dataset: {dataset}")
    if price_area not in market_input.ALLOWED_PRICE_AREAS:
        raise PublicSurplusRiskInputError("price_area must be DK1 or DK2")
    if limit < MIN_LIMIT or limit > market_input.MAX_LIMIT:
        raise PublicSurplusRiskInputError(
            f"limit must be between {MIN_LIMIT} and {market_input.MAX_LIMIT}"
        )

    query = {
        "limit": limit,
        "filter": json.dumps({"PriceArea": [price_area]}, separators=(",", ":")),
        "start": start,
        "end": end,
        "sort": _timestamp_sort_field(dataset),
    }
    url = f"{market_input.BASE_URL}/{quote(dataset, safe='')}?{urlencode(query)}"
    _require_eds_url(url)
    return url


def normalize_records(
    dataset: str,
    records: list[Any],
) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    normalized_rows: list[dict[str, Any]] = []
    missing_field_warnings: set[str] = set()

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise PublicSurplusRiskInputError(f"EDS record {index} must be a JSON object")
        try:
            if dataset == DAY_AHEAD_PRICES:
                normalized_rows.append(normalize_day_ahead_price_record(record))
            elif dataset == PRODUCTION_CONSUMPTION_SETTLEMENT:
                normalized_row, warnings = normalize_production_consumption_record(
                    record,
                    index=index,
                )
                normalized_rows.append(normalized_row)
                missing_field_warnings.update(warnings)
            else:
                raise PublicSurplusRiskInputError(
                    f"Unsupported required dataset: {dataset}"
                )
        except ValueError as exc:
            raise PublicSurplusRiskInputError(
                f"EDS record {index} is invalid: {exc}"
            ) from exc

    return normalized_rows, tuple(sorted(missing_field_warnings))


def normalize_day_ahead_price_record(record: Mapping[str, Any]) -> dict[str, Any]:
    normalized = market_input.normalize_day_ahead_price(dict(record))
    timestamp_utc = normalize_source_timestamp(normalized["timestamp_utc"], "TimeUTC")
    return _base_normalized_row(
        timestamp_utc=timestamp_utc,
        price_area=normalized["price_area"],
        source=f"{SOURCE}:{DAY_AHEAD_PRICES}",
        source_record_id=normalized["source_record_id"],
        day_ahead_price_eur_per_mwh=normalized["price_eur_per_mwh"],
    )


def normalize_production_consumption_record(
    record: Mapping[str, Any],
    *,
    index: int = 0,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    price_area = _require_price_area(record)
    source_timestamp = _require_field(record, "HourUTC")
    timestamp_utc = normalize_source_timestamp(source_timestamp, "HourUTC")
    warnings = _missing_optional_field_warnings(
        PRODUCTION_CONSUMPTION_SETTLEMENT,
        record,
        PRODUCTION_CONSUMPTION_OPTIONAL_FIELDS,
    )

    wind_generation_mwh = _sum_present_numeric(
        record,
        WIND_GENERATION_FIELDS,
        index=index,
    )
    solar_generation_mwh = _sum_present_numeric(
        record,
        SOLAR_GENERATION_FIELDS,
        index=index,
    )
    hydro_renewable_mwh = _sum_present_numeric(
        record,
        HYDRO_RENEWABLE_FIELDS,
        index=index,
    )
    renewable_generation_mwh = _sum_optional_values(
        wind_generation_mwh,
        solar_generation_mwh,
        hydro_renewable_mwh,
    )
    production_total_mwh = _production_total_mwh(
        record,
        renewable_generation_mwh=renewable_generation_mwh,
        index=index,
    )
    exchange_values = {
        normalized_name: _numeric_or_none(record.get(source_name), source_name, index)
        for source_name, normalized_name in EXCHANGE_FIELD_MAP.items()
        if source_name in record and record.get(source_name) is not None
    }

    normalized = _base_normalized_row(
        timestamp_utc=timestamp_utc,
        price_area=price_area,
        source=f"{SOURCE}:{PRODUCTION_CONSUMPTION_SETTLEMENT}",
        source_record_id=(
            f"{PRODUCTION_CONSUMPTION_SETTLEMENT}:{price_area}:{source_timestamp}"
        ),
        gross_consumption_mwh=_numeric_or_none(
            record.get("GrossConsumptionMWh"),
            "GrossConsumptionMWh",
            index,
        ),
        renewable_generation_mwh=renewable_generation_mwh,
        wind_generation_mwh=wind_generation_mwh,
        solar_generation_mwh=solar_generation_mwh,
        production_total_mwh=production_total_mwh,
    )
    normalized.update(exchange_values)
    if exchange_values:
        normalized["exchange_net_mwh"] = _sum_optional_values(*exchange_values.values())

    return normalized, tuple(sorted(warnings))


def normalize_source_timestamp(value: Any, field: str) -> str:
    """Normalize the EDS TimeUTC/HourUTC source contract to a UTC instant."""
    if field not in {"TimeUTC", "HourUTC"}:
        raise ValueError(f"No UTC source contract for {field}")
    if not isinstance(value, str) or "T" not in value:
        raise ValueError(f"{field} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(tzinfo=None).isoformat()


def build_summary(
    config: PublicSurplusRiskInputConfig,
    results: list[DatasetAreaResult],
) -> PublicSurplusRiskInputSummary:
    if not results:
        raise PublicSurplusRiskInputError("No EDS dataset results were produced")

    record_counts = {
        f"{result.dataset}:{result.price_area}": result.raw_record_count
        for result in results
    }
    normalized_row_counts = {
        f"{result.dataset}:{result.price_area}": result.normalized_record_count
        for result in results
    }
    dataset_timestamp_ranges: dict[str, dict[str, str]] = {}
    for dataset in DATASETS:
        dataset_results = [result for result in results if result.dataset == dataset]
        if dataset_results:
            timestamps = [
                timestamp
                for result in dataset_results
                for timestamp in (
                    result.earliest_timestamp_utc,
                    result.latest_timestamp_utc,
                )
            ]
            dataset_timestamp_ranges[dataset] = {
                "earliest_timestamp_utc": min(timestamps),
                "latest_timestamp_utc": max(timestamps),
            }

    missing_field_warnings = tuple(
        sorted(
            {
                warning
                for result in results
                for warning in result.missing_field_warnings
            }
        )
    )

    return PublicSurplusRiskInputSummary(
        period=f"{config.start_date} to {config.end_date}",
        price_areas=config.price_areas,
        datasets_requested=DATASETS,
        record_counts=record_counts,
        normalized_row_counts=normalized_row_counts,
        dataset_timestamp_ranges=dataset_timestamp_ranges,
        missing_field_warnings=missing_field_warnings,
        dry_run=config.dry_run,
        source=SOURCE,
        note=NOTE,
        file_written=False,
        database_write_performed=False,
    )


def print_summary(summary: PublicSurplusRiskInputSummary) -> None:
    print("Public surplus-risk backtest input summary")
    print(f"period: {summary.period}")
    print(f"price_areas: {','.join(summary.price_areas)}")
    print(f"datasets_requested: {','.join(summary.datasets_requested)}")
    print("record_counts:")
    for key in sorted(summary.record_counts):
        print(f"  {key}: {summary.record_counts[key]}")
    print("normalized_row_counts:")
    for key in sorted(summary.normalized_row_counts):
        print(f"  {key}: {summary.normalized_row_counts[key]}")
    print("dataset_timestamp_ranges:")
    for dataset in sorted(summary.dataset_timestamp_ranges):
        timestamp_range = summary.dataset_timestamp_ranges[dataset]
        print(f"  {dataset}:")
        print(
            "    earliest_timestamp_utc: "
            f"{timestamp_range['earliest_timestamp_utc']}"
        )
        print(
            "    latest_timestamp_utc: "
            f"{timestamp_range['latest_timestamp_utc']}"
        )
    print("missing_field_warnings:")
    if summary.missing_field_warnings:
        for warning in summary.missing_field_warnings:
            print(f"  - {warning}")
    else:
        print("  - none")
    print(f"dry_run: {str(summary.dry_run).lower()}")
    print(f"source: {summary.source}")
    print(f"note: {summary.note}")
    print(f"file_written: {str(summary.file_written).lower()}")
    print(
        "database_write_performed: "
        f"{str(summary.database_write_performed).lower()}"
    )


def main() -> int:
    try:
        config = load_config()

        def fetch(url: str) -> JsonPayload:
            return market_input.fetch_json(url, max_retries=config.eds_max_retries)

        summary = run_public_surplus_risk_backtest_input(config, fetch=fetch)
    except (PublicSurplusRiskInputError, market_input.BacktestInputError) as exc:
        print(f"Public surplus-risk backtest input failed: {exc}", file=sys.stderr)
        return 1
    except urllib.error.HTTPError as exc:
        print(
            "Public surplus-risk backtest input failed: "
            f"EDS HTTP {exc.code} {exc.reason}",
            file=sys.stderr,
        )
        return 1
    except urllib.error.URLError as exc:
        print(
            "Public surplus-risk backtest input failed: "
            f"EDS API unreachable: {exc.reason}",
            file=sys.stderr,
        )
        return 1
    except TimeoutError:
        print(
            "Public surplus-risk backtest input failed: "
            "EDS API unreachable: request timed out",
            file=sys.stderr,
        )
        return 1
    except json.JSONDecodeError as exc:
        print(
            "Public surplus-risk backtest input failed: "
            f"invalid JSON from EDS: {exc}",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(f"Public surplus-risk backtest input failed: {exc}", file=sys.stderr)
        return 1

    print_summary(summary)
    return 0


def _base_normalized_row(
    *,
    timestamp_utc: Any,
    price_area: str,
    source: str,
    source_record_id: str,
    day_ahead_price_eur_per_mwh: Any = None,
    gross_consumption_mwh: Any = None,
    renewable_generation_mwh: Any = None,
    wind_generation_mwh: Any = None,
    solar_generation_mwh: Any = None,
    production_total_mwh: Any = None,
) -> dict[str, Any]:
    return {
        "timestamp_utc": timestamp_utc,
        "price_area": price_area,
        "day_ahead_price_eur_per_mwh": day_ahead_price_eur_per_mwh,
        "gross_consumption_mwh": gross_consumption_mwh,
        "renewable_generation_mwh": renewable_generation_mwh,
        "wind_generation_mwh": wind_generation_mwh,
        "solar_generation_mwh": solar_generation_mwh,
        "production_total_mwh": production_total_mwh,
        "source": source,
        "source_record_id": source_record_id,
    }


def _production_total_mwh(
    record: Mapping[str, Any],
    *,
    renewable_generation_mwh: float | None,
    index: int,
) -> float | None:
    explicit_total = _first_present_numeric(record, PRODUCTION_TOTAL_FIELDS, index=index)
    if explicit_total is not None:
        return explicit_total

    central_power = _numeric_or_none(
        record.get("CentralPowerMWh"),
        "CentralPowerMWh",
        index,
    )
    local_power = _numeric_or_none(record.get("LocalPowerMWh"), "LocalPowerMWh", index)
    if central_power is None and local_power is None:
        return None

    return _sum_optional_values(central_power, local_power, renewable_generation_mwh)


def _sum_present_numeric(
    record: Mapping[str, Any],
    fields: tuple[str, ...],
    *,
    index: int,
) -> float | None:
    values = [
        _numeric_or_none(record[field], field, index)
        for field in fields
        if field in record and record[field] is not None
    ]
    return _sum_optional_values(*values)


def _sum_optional_values(*values: Any) -> float | None:
    present = [float(value) for value in values if value is not None]
    if not present:
        return None
    return sum(present)


def _first_present_numeric(
    record: Mapping[str, Any],
    fields: tuple[str, ...],
    *,
    index: int,
) -> float | None:
    for field in fields:
        if field in record and record[field] is not None:
            return _numeric_or_none(record[field], field, index)
    return None


def _numeric_or_none(value: Any, field_name: str, index: int) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"record {index} field {field_name} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"record {index} field {field_name} must be numeric") from exc


def _missing_optional_field_warnings(
    dataset: str,
    record: Mapping[str, Any],
    optional_fields: tuple[str, ...],
) -> set[str]:
    return {
        f"{dataset} optional field missing: {field}"
        for field in optional_fields
        if field not in record or record[field] is None
    }


def _require_price_area(record: Mapping[str, Any]) -> str:
    price_area = _require_field(record, "PriceArea")
    if price_area not in market_input.ALLOWED_PRICE_AREAS:
        raise ValueError(f"Unsupported Energi Data Service price area: {price_area}")
    return str(price_area)


def _require_field(record: Mapping[str, Any], field_name: str) -> Any:
    if field_name not in record:
        raise ValueError(f"Missing required Energi Data Service field: {field_name}")
    return record[field_name]


def _timestamp_sort_field(dataset: str) -> str:
    if dataset == DAY_AHEAD_PRICES:
        return "TimeUTC ASC"
    if dataset == PRODUCTION_CONSUMPTION_SETTLEMENT:
        return "HourUTC ASC"
    raise PublicSurplusRiskInputError(f"Unsupported required dataset: {dataset}")


def _require_eds_url(url: str) -> None:
    market_input._require_eds_url(url)


def _sleep_if_needed(seconds: float, sleep_fn: SleepFn) -> None:
    if seconds > 0:
        sleep_fn(seconds)


if __name__ == "__main__":
    raise SystemExit(main())
