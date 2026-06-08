from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from app.integrations.energi_data_service import build_eds_url, extract_records
from app.integrations.energi_data_service_normalizers import (
    normalize_day_ahead_price,
    normalize_electricity_prodex_5min_realtime,
)


SUPPORTED_DATASETS = {
    "DayAheadPrices",
    "ElectricityProdex5MinRealtime",
}
SUPPORTED_PRICE_AREAS = {"DK1", "DK2"}

JsonPayload = Mapping[str, Any]
FetchFn = Callable[[str], JsonPayload]
NormalizeFn = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class EdsDryRunSummary:
    dataset: str
    price_area: str
    limit: int
    request_url: str
    raw_record_count: int
    normalized_record_count: int
    rejected_record_count: int
    normalized_records: list[dict[str, Any]]


def run_eds_dry_run(
    *,
    dataset: str,
    price_area: str,
    limit: int,
    fetch: FetchFn,
) -> EdsDryRunSummary:
    """Fetch and normalize EDS records without persistence or side effects."""
    _validate_inputs(dataset=dataset, price_area=price_area, limit=limit)

    request_url = build_eds_url(dataset, price_area=price_area, limit=limit)
    payload = fetch(request_url)
    records = extract_records(dict(payload))
    normalized_records = _normalize_records(dataset, records)

    return EdsDryRunSummary(
        dataset=dataset,
        price_area=price_area,
        limit=limit,
        request_url=request_url,
        raw_record_count=len(records),
        normalized_record_count=len(normalized_records),
        rejected_record_count=len(records) - len(normalized_records),
        normalized_records=normalized_records,
    )


def _validate_inputs(*, dataset: str, price_area: str, limit: int) -> None:
    if dataset not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported Energi Data Service dataset: {dataset}")

    if price_area not in SUPPORTED_PRICE_AREAS:
        raise ValueError(f"Unsupported Energi Data Service price area: {price_area}")

    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("Limit must be a positive integer")


def _normalize_records(dataset: str, records: list[Any]) -> list[dict[str, Any]]:
    normalizer = _normalizer_for_dataset(dataset)
    normalized_records: list[dict[str, Any]] = []

    for record in records:
        if not isinstance(record, dict):
            continue

        try:
            normalized_records.append(normalizer(record))
        except ValueError:
            continue

    return normalized_records


def _normalizer_for_dataset(dataset: str) -> NormalizeFn:
    if dataset == "DayAheadPrices":
        return normalize_day_ahead_price

    if dataset == "ElectricityProdex5MinRealtime":
        return normalize_electricity_prodex_5min_realtime

    raise ValueError(f"Unsupported Energi Data Service dataset: {dataset}")
