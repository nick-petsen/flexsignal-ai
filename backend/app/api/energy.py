from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any, Literal
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Query

from app.db.read_queries import (
    DEFAULT_READ_LIMIT,
    MAX_READ_LIMIT,
    build_recent_power_balance_query,
    build_recent_spot_prices_query,
)


PriceArea = Literal["DK1", "DK2"]

LOCAL_DATABASE_HOSTS = {"localhost", "127.0.0.1", "::1"}
FORBIDDEN_SQL_OPERATIONS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "UPSERT",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
)

router = APIRouter(prefix="/api/energy", tags=["energy"])


@router.get("/spot-prices")
def get_recent_spot_prices(
    price_area: PriceArea,
    limit: int = Query(DEFAULT_READ_LIMIT, ge=1, le=MAX_READ_LIMIT),
) -> dict[str, Any]:
    query = build_recent_spot_prices_query(price_area=price_area, limit=limit)
    return _read_response(query=query, price_area=price_area)


@router.get("/power-balance")
def get_recent_power_balance(
    price_area: PriceArea,
    limit: int = Query(DEFAULT_READ_LIMIT, ge=1, le=MAX_READ_LIMIT),
) -> dict[str, Any]:
    query = build_recent_power_balance_query(price_area=price_area, limit=limit)
    return _read_response(query=query, price_area=price_area)


def _read_response(*, query: Mapping[str, Any], price_area: str) -> dict[str, Any]:
    rows = execute_read_query(query)
    return {
        "table": query["table"],
        "price_area": price_area,
        "row_count": len(rows),
        "rows": rows,
    }


def execute_read_query(query: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Execute a validated read-only query against a local PostgreSQL database.

    The helper is deliberately lazy: it reads DATABASE_URL and imports psycopg
    only when a request reaches one of the energy endpoints.
    """
    command = _validate_read_query(query)
    database_url = _get_local_database_url()

    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:  # pragma: no cover - depends on deployment env
        raise HTTPException(
            status_code=503,
            detail="Database driver is not installed",
        ) from exc

    try:
        with psycopg.connect(
            database_url,
            row_factory=dict_row,
            autocommit=True,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(command["sql"], command["params"])
                return [dict(row) for row in cursor.fetchall()]
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - real DB failures are env-specific
        raise HTTPException(
            status_code=503,
            detail="Database read failed",
        ) from exc


def _get_local_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="DATABASE_URL is required for this endpoint",
        )

    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise HTTPException(
            status_code=400,
            detail="DATABASE_URL must use a PostgreSQL DB-API URL",
        )

    if parsed.hostname not in LOCAL_DATABASE_HOSTS:
        raise HTTPException(
            status_code=403,
            detail="Only local DATABASE_URL hosts are supported for this endpoint",
        )

    return database_url


def _validate_read_query(query: Mapping[str, Any]) -> dict[str, Any]:
    if query.get("operation") != "select":
        raise HTTPException(status_code=500, detail="Unsupported database operation")

    sql = query.get("sql")
    params = query.get("params")
    table = query.get("table")

    if not isinstance(sql, str) or not re.match(r"^\s*SELECT\b", sql, re.IGNORECASE):
        raise HTTPException(status_code=500, detail="Unsupported database operation")

    for operation in FORBIDDEN_SQL_OPERATIONS:
        if re.search(rf"\b{operation}\b", sql, flags=re.IGNORECASE):
            raise HTTPException(status_code=500, detail="Unsupported database operation")

    if not isinstance(params, Mapping):
        raise HTTPException(status_code=500, detail="Malformed database query params")

    if not isinstance(table, str) or not table:
        raise HTTPException(status_code=500, detail="Malformed database query table")

    return {
        "sql": sql,
        "params": params,
        "table": table,
    }
