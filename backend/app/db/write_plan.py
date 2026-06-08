from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from app.db.repositories.eds_records import (
    DAY_AHEAD_PRICES_DATASET,
    ELECTRICITY_PRODEX_5MIN_REALTIME_DATASET,
    POWER_BALANCE_TABLE,
    SPOT_PRICES_TABLE,
)
from app.integrations.energi_data_service_normalizers import (
    DAY_AHEAD_PRICES_SOURCE,
    ELECTRICITY_PRODEX_5MIN_REALTIME_SOURCE,
)


UPSERT_PREVIEW_OPERATION = "upsert_preview"

SPOT_PRICE_WRITE_PLAN_REQUIRED_FIELDS = (
    "price_area",
    "timestamp_utc",
    "price_eur_per_mwh",
    "price_dkk_per_mwh",
    "source",
)
POWER_BALANCE_WRITE_PLAN_REQUIRED_FIELDS = (
    "price_area",
    "timestamp_utc",
    "production_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "exchange_net_mw",
    "source",
)


def build_eds_write_plan(
    *,
    dataset: str,
    normalized_records: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build database write-plan entries for normalized EDS dry-run records.

    The returned plan is a preview only. It does not generate SQL, open database
    connections, or perform writes.
    """
    table = _table_for_dataset(dataset)

    return [
        {
            "table": table,
            "operation": UPSERT_PREVIEW_OPERATION,
            "conflict_key": _build_conflict_key(normalized_record),
            "payload": _build_payload(
                dataset=dataset,
                normalized_record=normalized_record,
            ),
        }
        for normalized_record in normalized_records
    ]


def _table_for_dataset(dataset: str) -> str:
    if dataset == DAY_AHEAD_PRICES_DATASET:
        return SPOT_PRICES_TABLE

    if dataset == ELECTRICITY_PRODEX_5MIN_REALTIME_DATASET:
        return POWER_BALANCE_TABLE

    raise ValueError(f"Unsupported Energi Data Service dataset: {dataset}")


def _build_payload(
    *,
    dataset: str,
    normalized_record: Mapping[str, Any],
) -> dict[str, Any]:
    if dataset == DAY_AHEAD_PRICES_DATASET:
        _validate_required_fields(
            normalized_record,
            SPOT_PRICE_WRITE_PLAN_REQUIRED_FIELDS,
        )
        _validate_source(
            normalized_record["source"],
            expected_source=DAY_AHEAD_PRICES_SOURCE,
        )
        return {
            "price_area": normalized_record["price_area"],
            "timestamp_utc": normalized_record["timestamp_utc"],
            "price_eur_per_mwh": normalized_record["price_eur_per_mwh"],
            "price_dkk_per_mwh": normalized_record["price_dkk_per_mwh"],
            "source": normalized_record["source"],
            "source_record_id": normalized_record.get("source_record_id"),
        }

    if dataset == ELECTRICITY_PRODEX_5MIN_REALTIME_DATASET:
        _validate_required_fields(
            normalized_record,
            POWER_BALANCE_WRITE_PLAN_REQUIRED_FIELDS,
        )
        _validate_source(
            normalized_record["source"],
            expected_source=ELECTRICITY_PRODEX_5MIN_REALTIME_SOURCE,
        )
        return {
            "price_area": normalized_record["price_area"],
            "timestamp_utc": normalized_record["timestamp_utc"],
            "production_mw": normalized_record["production_mw"],
            "consumption_mw": normalized_record.get("consumption_mw"),
            "wind_onshore_mw": normalized_record["wind_onshore_mw"],
            "wind_offshore_mw": normalized_record["wind_offshore_mw"],
            "solar_mw": normalized_record["solar_mw"],
            "exchange_net_mw": normalized_record["exchange_net_mw"],
            "source": normalized_record["source"],
            "source_record_id": normalized_record.get("source_record_id"),
        }

    raise ValueError(f"Unsupported Energi Data Service dataset: {dataset}")


def _build_conflict_key(normalized_record: Mapping[str, Any]) -> dict[str, Any]:
    _validate_required_fields(
        normalized_record,
        ("price_area", "timestamp_utc", "source"),
    )

    if normalized_record.get("source_record_id"):
        return {
            "source": normalized_record["source"],
            "source_record_id": normalized_record["source_record_id"],
        }

    return {
        "price_area": normalized_record["price_area"],
        "timestamp_utc": normalized_record["timestamp_utc"],
        "source": normalized_record["source"],
    }


def _validate_required_fields(
    normalized_record: Mapping[str, Any],
    required_fields: tuple[str, ...],
) -> None:
    for field_name in required_fields:
        if field_name not in normalized_record or normalized_record[field_name] is None:
            raise ValueError(f"Missing required normalized EDS field: {field_name}")


def _validate_source(source: Any, *, expected_source: str) -> None:
    if source != expected_source:
        raise ValueError(f"Unsupported normalized EDS source: {source}")
