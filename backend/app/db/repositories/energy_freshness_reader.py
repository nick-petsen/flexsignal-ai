from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Protocol

from app.db.repositories.eds_records import SUPPORTED_PRICE_AREAS
from app.db.repositories.energy_freshness import (
    POWER_BALANCE_FRESHNESS_PART,
    SPOT_PRICE_FRESHNESS_PART,
    build_energy_freshness_summary_plan,
    build_power_balance_freshness_query,
    build_spot_price_freshness_query,
)


SAFETY_BOUNDARY = {
    "read_only_decision_support": True,
    "no_automatic_control": True,
    "no_dispatch": True,
    "no_activation": True,
    "no_operational_energy_system_integration": True,
    "human_review_required": True,
}

MUTATING_SQL_TOKENS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "UPSERT",
    "CREATE",
    "ALTER",
    "DROP",
    "TRUNCATE",
    "MERGE",
)


class DbCursor(Protocol):
    def execute(self, sql: str, params: Mapping[str, Any]) -> Any: ...

    def fetchone(self) -> Any: ...


class DbConnection(Protocol):
    def cursor(self) -> Any: ...


def read_spot_price_freshness(
    conn: DbConnection,
    price_area: str,
) -> dict[str, Any]:
    _validate_price_area(price_area)
    return _execute_freshness_plan(
        conn=conn,
        plan=build_spot_price_freshness_query(price_area),
    )


def read_power_balance_freshness(
    conn: DbConnection,
    price_area: str,
) -> dict[str, Any]:
    _validate_price_area(price_area)
    return _execute_freshness_plan(
        conn=conn,
        plan=build_power_balance_freshness_query(price_area),
    )


def read_energy_freshness_summary(
    conn: DbConnection,
    price_area: str,
) -> dict[str, Any]:
    _validate_price_area(price_area)
    build_energy_freshness_summary_plan(price_area)

    spot_price_freshness = read_spot_price_freshness(conn, price_area)
    power_balance_freshness = read_power_balance_freshness(conn, price_area)
    warnings = [
        warning
        for warning in (
            spot_price_freshness.get("warning"),
            power_balance_freshness.get("warning"),
        )
        if warning
    ]

    return {
        "price_area": price_area,
        "database_query_executed": True,
        "database_write_performed": False,
        "spot_price_freshness": spot_price_freshness,
        "power_balance_freshness": power_balance_freshness,
        "warnings": warnings,
        "safety_boundary": dict(SAFETY_BOUNDARY),
    }


def _execute_freshness_plan(
    *,
    conn: DbConnection,
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    _validate_query_plan(plan)

    cursor_handle = conn.cursor()
    enter = getattr(cursor_handle, "__enter__", None)
    if callable(enter):
        with cursor_handle as cursor:
            return _execute_with_cursor(cursor=cursor, plan=plan)

    try:
        return _execute_with_cursor(cursor=cursor_handle, plan=plan)
    finally:
        close = getattr(cursor_handle, "close", None)
        if callable(close):
            close()


def _execute_with_cursor(
    *,
    cursor: DbCursor,
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    cursor.execute(plan["sql"], plan["params"])
    row = _row_to_mapping(
        row=cursor.fetchone(),
        cursor=cursor,
        expected_fields=tuple(plan.get("expected_result_fields", ())),
    )

    row_count = _coerce_row_count(row.get("row_count"))
    warning = row.get("warning")
    if row_count == 0 and not warning:
        warning = plan["params"]["empty_warning"]

    return {
        "price_area": plan["price_area"],
        "database_query_executed": True,
        "database_write_performed": False,
        "source_label": row.get("data_source_label") or plan["params"]["source_label"],
        "earliest_timestamp": row.get("earliest_timestamp_utc"),
        "latest_timestamp": row.get("latest_timestamp_utc"),
        "row_count": row_count,
        "warning": warning,
        "safety_boundary": dict(SAFETY_BOUNDARY),
    }


def _validate_query_plan(plan: Mapping[str, Any]) -> None:
    if plan.get("operation") != "select":
        raise ValueError("Energy freshness reader only executes select query plans.")

    _validate_price_area(plan.get("price_area"))

    sql = plan.get("sql")
    params = plan.get("params")
    if not isinstance(sql, str) or not re.match(r"^\s*SELECT\b", sql, re.IGNORECASE):
        raise ValueError("Energy freshness reader only executes SELECT SQL.")

    for token in MUTATING_SQL_TOKENS:
        if re.search(rf"\b{token}\b", sql, re.IGNORECASE):
            raise ValueError("Energy freshness reader rejected unsafe SQL.")

    if not isinstance(params, Mapping) or not params:
        raise ValueError("Energy freshness reader requires SQL parameters.")

    if "%(" not in sql or ")s" not in sql:
        raise ValueError("Energy freshness reader requires parameterized SQL.")

    if params.get("price_area") != plan.get("price_area"):
        raise ValueError("Energy freshness reader rejected mismatched price_area.")


def _validate_price_area(price_area: Any) -> None:
    if price_area not in SUPPORTED_PRICE_AREAS:
        raise ValueError(f"Unsupported energy freshness price area: {price_area}")


def _row_to_mapping(
    *,
    row: Any,
    cursor: Any,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if row is None:
        return {}

    if isinstance(row, Mapping):
        return dict(row)

    description = getattr(cursor, "description", None)
    if description:
        field_names = tuple(column[0] for column in description)
    else:
        field_names = expected_fields

    return dict(zip(field_names, row, strict=False))


def _coerce_row_count(value: Any) -> int:
    if value is None:
        return 0
    return int(value)
