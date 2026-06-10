#!/usr/bin/env python3
"""Manual read-only local PostgreSQL backtest for rule-engine-v0."""

from __future__ import annotations

import argparse
import datetime as dt
import decimal
import json
import os
import re
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.read_queries import (  # noqa: E402
    DEFAULT_READ_LIMIT,
    MAX_READ_LIMIT,
    build_recent_power_balance_query,
    build_recent_spot_prices_query,
)
from app.risk import evaluate_risk_backtest, pair_rows_by_nearest_timestamp  # noqa: E402
from app.risk.rule_engine import NUMERIC_FIELDS  # noqa: E402


ALLOWED_LOCAL_HOSTS = {"localhost", "127.0.0.1"}
SUPPORTED_PRICE_AREAS = ("DK1", "DK2")
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
PAIRING_STRATEGY = "nearest_timestamp_v0_1"


def limited_positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than 0")

    if parsed > MAX_READ_LIMIT:
        raise argparse.ArgumentTypeError(f"must be no greater than {MAX_READ_LIMIT}")

    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a manual local PostgreSQL read-only backtest for "
            "rule-engine-v0 using existing spot_prices and power_balance rows."
        )
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
        default=DEFAULT_READ_LIMIT,
        help=(
            "Maximum rows to read from each table. "
            f"Default: {DEFAULT_READ_LIMIT}. Hard maximum: {MAX_READ_LIMIT}."
        ),
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print indented JSON instead of compact JSON.",
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


def validate_select_only(query: Mapping[str, Any]) -> dict[str, Any]:
    sql = query.get("sql")
    params = query.get("params")
    operation = query.get("operation")

    if operation != "select":
        raise ValueError(f"Refusing non-select query operation: {operation}")

    if not isinstance(sql, str) or not re.match(r"^\s*SELECT\b", sql, re.IGNORECASE):
        raise ValueError("Refusing to execute SQL that does not start with SELECT")

    for operation_name in FORBIDDEN_SQL_OPERATIONS:
        if re.search(rf"\b{operation_name}\b", sql, flags=re.IGNORECASE):
            raise ValueError(f"Refusing forbidden SQL operation: {operation_name}")

    if not isinstance(params, Mapping):
        raise ValueError("Refusing malformed SQL params")

    return {
        "sql": sql,
        "params": params,
        "table": query.get("table"),
        "operation": operation,
    }


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
    command = validate_select_only(query)

    with connection.cursor() as cursor:
        cursor.execute(command["sql"], command["params"])
        column_names = [description[0] for description in cursor.description]
        return [dict(zip(column_names, row, strict=True)) for row in cursor.fetchall()]


def compose_backtest_rows(
    *,
    price_area: str,
    spot_price_rows: list[dict[str, Any]],
    power_balance_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paired_rows = pair_rows_by_nearest_timestamp(
        spot_price_rows,
        power_balance_rows,
        price_area,
    )

    return [
        normalize_rule_engine_input(composed_row)
        for composed_row in paired_rows
    ]


def normalize_rule_engine_input(input_data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(input_data)

    timestamp_utc = normalized.get("timestamp_utc")
    if isinstance(timestamp_utc, (dt.datetime, dt.date, dt.time)):
        normalized["timestamp_utc"] = timestamp_utc.isoformat()

    for field in NUMERIC_FIELDS:
        value = normalized.get(field)
        if isinstance(value, decimal.Decimal):
            normalized[field] = float(value)

    return normalized


def build_summary(
    *,
    price_area: str,
    limit: int,
    spot_price_rows: list[dict[str, Any]],
    power_balance_rows: list[dict[str, Any]],
    composed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "price_area": price_area,
        "limit": limit,
        "spot_price_rows_read": len(spot_price_rows),
        "power_balance_rows_read": len(power_balance_rows),
        "composed_rows": len(composed_rows),
        "pairing_strategy": PAIRING_STRATEGY,
        "backtest_summary": evaluate_risk_backtest(composed_rows),
        "decision_support_only": True,
        "read_only": True,
    }


def print_scope_warning(*, host: str) -> None:
    print(
        "WARNING: manual local read-only backtest only. "
        f"Target host: {host}. Executes generated SELECT queries only; "
        "does not write to the database, fetch live Energi Data Service data, "
        "call HTTP APIs, create ingestion jobs, add endpoints, run control, "
        "dispatch, activation, or operational workflows.",
        file=sys.stderr,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        database_url, host = require_local_database_url()
        spot_price_query = build_recent_spot_prices_query(
            price_area=args.price_area,
            limit=args.limit,
        )
        power_balance_query = build_recent_power_balance_query(
            price_area=args.price_area,
            limit=args.limit,
        )
        validate_select_only(spot_price_query)
        validate_select_only(power_balance_query)
    except ValueError as exc:
        print(f"Configuration failed: {exc}", file=sys.stderr)
        return 2

    print_scope_warning(host=host)

    connection = None
    try:
        connection = connect_with_available_dbapi_driver(database_url)
        spot_price_rows = fetch_rows(connection, spot_price_query)
        power_balance_rows = fetch_rows(connection, power_balance_query)
        composed_rows = compose_backtest_rows(
            price_area=args.price_area,
            spot_price_rows=spot_price_rows,
            power_balance_rows=power_balance_rows,
        )
    except RuntimeError as exc:
        print(f"Database driver unavailable: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Local database risk backtest failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if connection is not None:
            connection.close()

    summary = build_summary(
        price_area=args.price_area,
        limit=args.limit,
        spot_price_rows=spot_price_rows,
        power_balance_rows=power_balance_rows,
        composed_rows=composed_rows,
    )

    if args.pretty:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps(summary, separators=(",", ":"), sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
