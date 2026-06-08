from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.integrations.energi_data_service_normalizers import (
    DAY_AHEAD_PRICES_SOURCE,
    ELECTRICITY_PRODEX_5MIN_REALTIME_SOURCE,
)


DAY_AHEAD_PRICES_DATASET = "DayAheadPrices"
ELECTRICITY_PRODEX_5MIN_REALTIME_DATASET = "ElectricityProdex5MinRealtime"
SPOT_PRICES_TABLE = "spot_prices"
POWER_BALANCE_TABLE = "power_balance"
SUPPORTED_PRICE_AREAS = {"DK1", "DK2"}

SPOT_PRICE_REQUIRED_FIELDS = (
    "price_area",
    "timestamp_utc",
    "price_eur_per_mwh",
    "price_dkk_per_mwh",
    "source",
    "source_record_id",
)
POWER_BALANCE_REQUIRED_FIELDS = (
    "price_area",
    "timestamp_utc",
    "production_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "exchange_net_mw",
    "source",
    "source_record_id",
)


def build_eds_record_insert_payload(
    *,
    dataset: str,
    table: str,
    normalized_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Map a supported normalized Energi Data Service record to a DB payload."""
    if dataset == DAY_AHEAD_PRICES_DATASET and table == SPOT_PRICES_TABLE:
        return day_ahead_price_to_spot_price_payload(normalized_record)

    if (
        dataset == ELECTRICITY_PRODEX_5MIN_REALTIME_DATASET
        and table == POWER_BALANCE_TABLE
    ):
        return electricity_prodex_5min_realtime_to_power_balance_payload(
            normalized_record
        )

    raise ValueError(f"Unsupported EDS dataset/table target: {dataset} -> {table}")


def day_ahead_price_to_spot_price_payload(
    normalized_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Map a normalized DayAheadPrices record to a spot_prices insert payload."""
    _validate_required_fields(normalized_record, SPOT_PRICE_REQUIRED_FIELDS)
    _validate_price_area(normalized_record["price_area"])
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
        "source_record_id": normalized_record["source_record_id"],
    }


def electricity_prodex_5min_realtime_to_power_balance_payload(
    normalized_record: Mapping[str, Any],
) -> dict[str, Any]:
    """Map a normalized ElectricityProdex5MinRealtime record to power_balance."""
    _validate_required_fields(normalized_record, POWER_BALANCE_REQUIRED_FIELDS)
    _validate_price_area(normalized_record["price_area"])
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
        "source_record_id": normalized_record["source_record_id"],
    }


def _validate_required_fields(
    normalized_record: Mapping[str, Any],
    required_fields: tuple[str, ...],
) -> None:
    for field_name in required_fields:
        if field_name not in normalized_record or normalized_record[field_name] is None:
            raise ValueError(f"Missing required normalized EDS field: {field_name}")


def _validate_price_area(price_area: Any) -> None:
    if price_area not in SUPPORTED_PRICE_AREAS:
        raise ValueError(f"Unsupported normalized EDS price area: {price_area}")


def _validate_source(source: Any, *, expected_source: str) -> None:
    if source != expected_source:
        raise ValueError(f"Unsupported normalized EDS source: {source}")
