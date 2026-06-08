#!/usr/bin/env python3
"""Manual local PostgreSQL smoke test for the EDS DB write path."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.repositories.eds_records import (  # noqa: E402
    DAY_AHEAD_PRICES_DATASET,
    ELECTRICITY_PRODEX_5MIN_REALTIME_DATASET,
)
from app.db.sql_builder import build_eds_write_plan_entry_upsert_sql  # noqa: E402
from app.db.transaction import execute_sql_commands_transaction  # noqa: E402
from app.db.write_plan import build_eds_write_plan  # noqa: E402
from app.integrations.energi_data_service_normalizers import (  # noqa: E402
    DAY_AHEAD_PRICES_SOURCE,
    ELECTRICITY_PRODEX_5MIN_REALTIME_SOURCE,
)


ALLOWED_LOCAL_HOSTS = {"localhost", "127.0.0.1"}
CONFIRM_FLAG = "--confirm-local-db-write"

SampleBatch = tuple[str, list[Mapping[str, Any]]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manually validate the existing EDS write-plan, SQL builder, and "
            "transaction path against a local PostgreSQL database. Defaults to "
            "dry-run and never uses live Energi Data Service data."
        )
    )
    parser.add_argument(
        CONFIRM_FLAG,
        action="store_true",
        help=(
            "Actually write the hardcoded sample records. Without this flag, "
            "the script validates and prints a dry-run summary only."
        ),
    )
    return parser


def build_sample_batches() -> list[SampleBatch]:
    return [
        (
            DAY_AHEAD_PRICES_DATASET,
            [
                {
                    "price_area": "DK1",
                    "timestamp_utc": "2026-01-01T00:00:00Z",
                    "price_dkk_per_mwh": 512.3400,
                    "price_eur_per_mwh": 68.6700,
                    "source": DAY_AHEAD_PRICES_SOURCE,
                    "source_record_id": (
                        "manual-local-smoke:DayAheadPrices:DK1:2026-01-01T00:00:00Z"
                    ),
                }
            ],
        ),
        (
            ELECTRICITY_PRODEX_5MIN_REALTIME_DATASET,
            [
                {
                    "price_area": "DK1",
                    "timestamp_utc": "2026-01-01T00:05:00Z",
                    "production_mw": 4280.2500,
                    "consumption_mw": None,
                    "wind_onshore_mw": 1225.5000,
                    "wind_offshore_mw": 840.7500,
                    "solar_mw": 0.0000,
                    "exchange_net_mw": -315.2500,
                    "source": ELECTRICITY_PRODEX_5MIN_REALTIME_SOURCE,
                    "source_record_id": (
                        "manual-local-smoke:"
                        "ElectricityProdex5MinRealtime:DK1:2026-01-01T00:05:00Z"
                    ),
                }
            ],
        ),
    ]


def build_sql_commands(sample_batches: list[SampleBatch]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    for dataset, normalized_records in sample_batches:
        write_plan = build_eds_write_plan(
            dataset=dataset,
            normalized_records=normalized_records,
        )
        commands.extend(
            build_eds_write_plan_entry_upsert_sql(write_plan_entry)
            for write_plan_entry in write_plan
        )

    if not commands:
        raise ValueError("Smoke test generated no SQL commands")

    return commands


def require_local_database_url() -> tuple[str, str]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is required")

    parsed = urlparse(database_url)
    host = parsed.hostname
    if host not in ALLOWED_LOCAL_HOSTS:
        raise ValueError(
            "Refusing to run: DATABASE_URL host must be localhost or 127.0.0.1"
        )

    return database_url, host


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


def print_summary(
    *,
    host: str,
    sql_commands: list[Mapping[str, Any]],
    committed: bool,
    rolled_back: bool,
) -> None:
    print(f"target host: {host}")
    print(f"command count: {len(sql_commands)}")
    tables = ", ".join(sorted({command["table"] for command in sql_commands}))
    print(f"tables: {tables}")
    print(f"committed: {str(committed).lower()}")
    print(f"rolled_back: {str(rolled_back).lower()}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        database_url, host = require_local_database_url()
        sql_commands = build_sql_commands(build_sample_batches())
    except ValueError as exc:
        print(f"Configuration failed: {exc}", file=sys.stderr)
        return 2

    print(
        "WARNING: Manual local PostgreSQL smoke test for hardcoded sample "
        "records only. Do not use production databases, live service data, "
        "dispatch workflows, activation workflows, or control systems."
    )

    if not args.confirm_local_db_write:
        print("Dry-run only. Re-run with --confirm-local-db-write to execute writes.")
        print_summary(
            host=host,
            sql_commands=sql_commands,
            committed=False,
            rolled_back=False,
        )
        return 0

    connection = None
    try:
        connection = connect_with_available_dbapi_driver(database_url)
        result = execute_sql_commands_transaction(sql_commands, connection)
    except RuntimeError as exc:
        print(f"Database driver unavailable: {exc}", file=sys.stderr)
        print_summary(
            host=host,
            sql_commands=sql_commands,
            committed=False,
            rolled_back=False,
        )
        return 1
    except Exception as exc:
        print(f"Database smoke test failed: {exc}", file=sys.stderr)
        print_summary(
            host=host,
            sql_commands=sql_commands,
            committed=False,
            rolled_back=connection is not None,
        )
        return 1
    finally:
        if connection is not None:
            connection.close()

    print_summary(
        host=host,
        sql_commands=sql_commands,
        committed=bool(result["committed"]),
        rolled_back=bool(result["rolled_back"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
