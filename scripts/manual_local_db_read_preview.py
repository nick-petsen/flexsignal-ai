#!/usr/bin/env python3
"""Manual local PostgreSQL read preview for existing tables only."""

from __future__ import annotations

import argparse
import datetime as dt
import decimal
import json
import os
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.read_queries import (  # noqa: E402
    build_recent_power_balance_query,
    build_recent_spot_prices_query,
)


ALLOWED_LOCAL_HOSTS = {"localhost", "127.0.0.1"}
SUPPORTED_TABLES = ("spot_prices", "power_balance")
SUPPORTED_PRICE_AREAS = ("DK1", "DK2")
DEFAULT_LIMIT = 10
HARD_MAX_LIMIT = 100
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


def limited_positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than 0")

    if parsed > HARD_MAX_LIMIT:
        raise argparse.ArgumentTypeError(f"must be no greater than {HARD_MAX_LIMIT}")

    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manually read recent rows from an existing local PostgreSQL table "
            "using the backend read-only SELECT query builders."
        )
    )
    parser.add_argument(
        "--table",
        required=True,
        choices=SUPPORTED_TABLES,
        help="Existing table to preview.",
    )
    parser.add_argument(
        "--price-area",
        required=True,
        choices=SUPPORTED_PRICE_AREAS,
        help="Danish price area filter to apply.",
    )
    parser.add_argument(
        "--limit",
        type=limited_positive_int,
        default=DEFAULT_LIMIT,
        help=(
            "Maximum rows to read. "
            f"Default: {DEFAULT_LIMIT}. Hard maximum: {HARD_MAX_LIMIT}."
        ),
    )
    return parser


def require_local_database_url() -> tuple[str, str]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is required")

    parsed = urlparse(database_url)
    if parsed.scheme != "postgresql":
        raise ValueError(
            "DATABASE_URL must use DB-API format, for example "
            "postgresql://localhost/flexsignal_ai"
        )

    host = parsed.hostname
    if host not in ALLOWED_LOCAL_HOSTS:
        raise ValueError(
            "Refusing to run: DATABASE_URL host must be localhost or 127.0.0.1"
        )

    return database_url, host


def build_read_query(*, table: str, price_area: str, limit: int) -> Mapping[str, Any]:
    if table == "spot_prices":
        return build_recent_spot_prices_query(price_area=price_area, limit=limit)

    if table == "power_balance":
        return build_recent_power_balance_query(price_area=price_area, limit=limit)

    raise ValueError(f"Unsupported table: {table}")


def validate_select_only(query: Mapping[str, Any]) -> None:
    sql = str(query.get("sql", "")).strip()
    operation = query.get("operation")

    if operation != "select":
        raise ValueError(f"Refusing non-select query operation: {operation}")

    if not sql.upper().startswith("SELECT "):
        raise ValueError("Refusing to execute SQL that does not start with SELECT")

    for operation_name in FORBIDDEN_SQL_OPERATIONS:
        if re.search(rf"\b{operation_name}\b", sql, flags=re.IGNORECASE):
            raise ValueError(f"Refusing forbidden SQL operation: {operation_name}")


def connect_with_available_dbapi_driver(database_url: str) -> Any:
    connector = _load_dbapi_connector()
    return connector(database_url)


def _load_dbapi_connector() -> Callable[[str], Any]:
    try:
        import psycopg  # type: ignore[import-not-found]

        return psycopg.connect
    except ImportError:
        pass

    try:
        import psycopg2  # type: ignore[import-not-found]

        return psycopg2.connect
    except ImportError as exc:
        raise RuntimeError(
            "No PostgreSQL DB-API driver is available. Install or activate an "
            "environment that already provides psycopg or psycopg2; this script "
            "does not add backend dependencies."
        ) from exc


def fetch_rows(connection: Any, query: Mapping[str, Any]) -> list[dict[str, Any]]:
    validate_select_only(query)

    with connection.cursor() as cursor:
        cursor.execute(query["sql"], query["params"])
        column_names = [description[0] for description in cursor.description]
        return [
            dict(zip(column_names, row, strict=True))
            for row in cursor.fetchall()
        ]


def json_default(value: Any) -> str | float:
    if isinstance(value, (dt.date, dt.datetime, dt.time)):
        return value.isoformat()

    if isinstance(value, decimal.Decimal):
        return float(value)

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def print_summary(
    *,
    host: str,
    table: str,
    price_area: str,
    rows: Sequence[Mapping[str, Any]],
) -> None:
    print(f"target host: {host}")
    print(f"table: {table}")
    print(f"price area: {price_area}")
    print(f"row count: {len(rows)}")
    for row in rows:
        print(json.dumps(row, default=json_default, separators=(",", ":")))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        database_url, host = require_local_database_url()
        query = build_read_query(
            table=args.table,
            price_area=args.price_area,
            limit=args.limit,
        )
        validate_select_only(query)
    except ValueError as exc:
        print(f"Configuration failed: {exc}", file=sys.stderr)
        return 2

    connection = None
    try:
        connection = connect_with_available_dbapi_driver(database_url)
        rows = fetch_rows(connection, query)
    except RuntimeError as exc:
        print(f"Database driver unavailable: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Local database read preview failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if connection is not None:
            connection.close()

    print_summary(
        host=host,
        table=args.table,
        price_area=args.price_area,
        rows=rows,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
