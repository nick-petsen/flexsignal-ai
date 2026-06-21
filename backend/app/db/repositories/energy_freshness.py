from __future__ import annotations

from typing import Any

from app.db.repositories.eds_records import (
    POWER_BALANCE_TABLE,
    SPOT_PRICES_TABLE,
    SUPPORTED_PRICE_AREAS,
)


DATA_FRESHNESS_READ_MODEL_VERSION = "eds-data-freshness-read-model-v0"
SELECT_OPERATION = "select"
SPOT_PRICE_FRESHNESS_PART = "spot_price"
POWER_BALANCE_FRESHNESS_PART = "power_balance"
SPOT_PRICE_SOURCE_LABEL = "Energi Data Service:DayAheadPrices"
POWER_BALANCE_SOURCE_LABEL = "Energi Data Service:ElectricityProdex5MinRealtime"


def build_spot_price_freshness_query(price_area: str) -> dict[str, Any]:
    return _build_freshness_query(
        price_area=price_area,
        table=SPOT_PRICES_TABLE,
        part=SPOT_PRICE_FRESHNESS_PART,
        source_label=SPOT_PRICE_SOURCE_LABEL,
        empty_warning="No spot price rows are available for this price area.",
    )


def build_power_balance_freshness_query(price_area: str) -> dict[str, Any]:
    return _build_freshness_query(
        price_area=price_area,
        table=POWER_BALANCE_TABLE,
        part=POWER_BALANCE_FRESHNESS_PART,
        source_label=POWER_BALANCE_SOURCE_LABEL,
        empty_warning="No power balance rows are available for this price area.",
    )


def build_energy_freshness_summary_plan(price_area: str) -> dict[str, Any]:
    _validate_price_area(price_area)

    return {
        "read_model": DATA_FRESHNESS_READ_MODEL_VERSION,
        "price_area": price_area,
        "operation": SELECT_OPERATION,
        "queries": {
            SPOT_PRICE_FRESHNESS_PART: build_spot_price_freshness_query(price_area),
            POWER_BALANCE_FRESHNESS_PART: build_power_balance_freshness_query(
                price_area
            ),
        },
    }


def _build_freshness_query(
    *,
    price_area: str,
    table: str,
    part: str,
    source_label: str,
    empty_warning: str,
) -> dict[str, Any]:
    _validate_price_area(price_area)

    return {
        "read_model": DATA_FRESHNESS_READ_MODEL_VERSION,
        "part": part,
        "price_area": price_area,
        "table": table,
        "operation": SELECT_OPERATION,
        "sql": (
            "SELECT "
            "%(price_area)s AS price_area, "
            "MIN(timestamp_utc) AS earliest_timestamp_utc, "
            "MAX(timestamp_utc) AS latest_timestamp_utc, "
            "COUNT(*) AS row_count, "
            "%(source_label)s AS data_source_label, "
            "CASE WHEN COUNT(*) = 0 THEN %(empty_warning)s ELSE NULL END AS warning "
            f"FROM {table} "
            "WHERE price_area = %(price_area)s"
        ),
        "params": {
            "price_area": price_area,
            "source_label": source_label,
            "empty_warning": empty_warning,
        },
        "expected_result_fields": (
            "price_area",
            "earliest_timestamp_utc",
            "latest_timestamp_utc",
            "row_count",
            "data_source_label",
            "warning",
        ),
    }


def _validate_price_area(price_area: Any) -> None:
    if price_area not in SUPPORTED_PRICE_AREAS:
        raise ValueError(f"Unsupported energy freshness price area: {price_area}")
