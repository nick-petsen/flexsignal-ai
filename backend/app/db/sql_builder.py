from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.db.repositories.eds_records import POWER_BALANCE_TABLE, SPOT_PRICES_TABLE
from app.db.write_plan import UPSERT_PREVIEW_OPERATION


SPOT_PRICE_COLUMNS = (
    "price_area",
    "timestamp_utc",
    "price_eur_per_mwh",
    "price_dkk_per_mwh",
    "source",
    "source_record_id",
)
SPOT_PRICE_REQUIRED_PAYLOAD_FIELDS = (
    "price_area",
    "timestamp_utc",
    "price_eur_per_mwh",
    "price_dkk_per_mwh",
    "source",
)
POWER_BALANCE_COLUMNS = (
    "price_area",
    "timestamp_utc",
    "production_mw",
    "consumption_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "exchange_net_mw",
    "source",
    "source_record_id",
)
POWER_BALANCE_REQUIRED_PAYLOAD_FIELDS = (
    "price_area",
    "timestamp_utc",
    "production_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "exchange_net_mw",
    "source",
)
SUPPORTED_TABLES = {
    SPOT_PRICES_TABLE: {
        "columns": SPOT_PRICE_COLUMNS,
        "required_payload_fields": SPOT_PRICE_REQUIRED_PAYLOAD_FIELDS,
    },
    POWER_BALANCE_TABLE: {
        "columns": POWER_BALANCE_COLUMNS,
        "required_payload_fields": POWER_BALANCE_REQUIRED_PAYLOAD_FIELDS,
    },
}


def build_eds_write_plan_entry_upsert_sql(
    write_plan_entry: Mapping[str, Any],
) -> dict[str, Any]:
    """Build parameterized PostgreSQL upsert SQL for one EDS write-plan entry.

    This is a pure formatting helper. It does not connect to PostgreSQL and does
    not execute SQL.
    """
    table = write_plan_entry.get("table")
    operation = write_plan_entry.get("operation")
    payload = write_plan_entry.get("payload")

    if table not in SUPPORTED_TABLES:
        raise ValueError(f"Unsupported EDS write-plan table: {table}")

    if operation != UPSERT_PREVIEW_OPERATION:
        raise ValueError(f"Unsupported EDS write-plan operation: {operation}")

    if not isinstance(payload, Mapping):
        raise ValueError("Missing EDS write-plan payload")

    table_config = SUPPORTED_TABLES[table]
    columns = table_config["columns"]
    required_payload_fields = table_config["required_payload_fields"]
    _validate_required_payload_fields(payload, required_payload_fields)

    params = _build_params(payload, columns)
    conflict_columns = _build_conflict_columns(payload)
    update_columns = tuple(
        column for column in columns if column not in conflict_columns
    )

    return {
        "sql": _build_upsert_sql(
            table=table,
            columns=columns,
            conflict_columns=conflict_columns,
            update_columns=update_columns,
        ),
        "params": params,
        "table": table,
        "operation": operation,
    }


def _build_params(
    payload: Mapping[str, Any],
    columns: tuple[str, ...],
) -> dict[str, Any]:
    return {column: payload.get(column) for column in columns}


def _build_conflict_columns(payload: Mapping[str, Any]) -> tuple[str, ...]:
    if payload.get("source_record_id"):
        return ("source", "source_record_id")

    return ("price_area", "timestamp_utc", "source")


def _build_upsert_sql(
    *,
    table: str,
    columns: tuple[str, ...],
    conflict_columns: tuple[str, ...],
    update_columns: tuple[str, ...],
) -> str:
    column_sql = ", ".join(columns)
    placeholder_sql = ", ".join(f"%({column})s" for column in columns)
    conflict_sql = ", ".join(conflict_columns)
    update_sql = ", ".join(
        f"{column} = EXCLUDED.{column}" for column in update_columns
    )

    return (
        f"INSERT INTO {table} ({column_sql}) "
        f"VALUES ({placeholder_sql}) "
        f"ON CONFLICT ({conflict_sql}) "
        f"DO UPDATE SET {update_sql}"
    )


def _validate_required_payload_fields(
    payload: Mapping[str, Any],
    required_payload_fields: tuple[str, ...],
) -> None:
    for field_name in required_payload_fields:
        if field_name not in payload or payload[field_name] is None:
            raise ValueError(
                f"Missing required EDS write-plan payload field: {field_name}"
            )
