#!/usr/bin/env python3
"""Manual local EDS-to-PostgreSQL ingestion for developer validation only."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.transaction import execute_sql_commands_transaction  # noqa: E402
from app.ingestion.eds_dry_run import (  # noqa: E402
    SUPPORTED_DATASETS,
    SUPPORTED_PRICE_AREAS,
    run_eds_dry_run,
)
from app.ingestion.eds_persistence_dry_run import (  # noqa: E402
    run_eds_persistence_dry_run,
)
from app.integrations.energi_data_service import build_eds_url  # noqa: E402


ALLOWED_LOCAL_HOSTS = {"localhost", "127.0.0.1"}
CONFIRM_FLAG = "--confirm-local-db-write"
DEFAULT_LIMIT = 2
HARD_MAX_LIMIT = 50
DEFAULT_TIMEOUT_SECONDS = 15
USER_AGENT = "flexsignal-ai-manual-eds-local-db-ingest/0.1"


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
            "Manually fetch a tiny supported Energi Data Service sample, build "
            "normalized records, write-plan entries, and SQL commands, then "
            "write only to a local PostgreSQL database when explicitly confirmed."
        )
    )
    parser.add_argument(
        "--dataset",
        required=True,
        choices=sorted(SUPPORTED_DATASETS),
        help="Energi Data Service dataset to fetch.",
    )
    parser.add_argument(
        "--price-area",
        required=True,
        choices=sorted(SUPPORTED_PRICE_AREAS),
        help="Danish price area filter to apply.",
    )
    parser.add_argument(
        "--limit",
        type=limited_positive_int,
        default=DEFAULT_LIMIT,
        help=(
            "Maximum raw records to request. "
            f"Default: {DEFAULT_LIMIT}. Hard maximum: {HARD_MAX_LIMIT}."
        ),
    )
    parser.add_argument(
        CONFIRM_FLAG,
        action="store_true",
        help=(
            "Actually execute generated SQL against the local database. Without "
            "this flag, the script is dry-run only."
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


def fetch_json(url: str) -> tuple[int, Mapping[str, Any]]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT},
    )

    with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read()
        payload = json.loads(body.decode(charset, errors="replace"))

    if not isinstance(payload, Mapping):
        raise ValueError("Energi Data Service response must be a JSON object")

    return response.status, payload


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


def print_warning(*, confirmed_write: bool) -> None:
    mode = "CONFIRMED LOCAL WRITE" if confirmed_write else "DRY-RUN"
    print(
        "WARNING: Manual local developer validation only. "
        f"Mode: {mode}. This script fetches a tiny live Energi Data Service "
        "sample and must not be used for production databases, scheduled jobs, "
        "FastAPI startup, API endpoints, forecasting, dispatch, activation, "
        "control workflows, or operational energy infrastructure."
    )


def print_summary(
    *,
    request_url: str,
    http_status: int | str,
    raw_count: int,
    normalized_count: int,
    sql_commands: list[Mapping[str, Any]],
    committed: bool,
    rolled_back: bool,
) -> None:
    tables = ", ".join(sorted({command["table"] for command in sql_commands}))
    if not tables:
        tables = "none"

    print(f"Final request URL: {request_url}")
    print(f"HTTP status: {http_status}")
    print(f"Raw record count: {raw_count}")
    print(f"Normalized record count: {normalized_count}")
    print(f"SQL command count: {len(sql_commands)}")
    print(f"Tables: {tables}")
    print(f"Committed: {str(committed).lower()}")
    print(f"Rolled back: {str(rolled_back).lower()}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    http_status: int | None = None

    try:
        database_url, _host = require_local_database_url()
        request_url = build_eds_url(
            args.dataset,
            price_area=args.price_area,
            limit=args.limit,
        )
    except ValueError as exc:
        print(f"Configuration failed: {exc}", file=sys.stderr)
        return 2

    print_warning(confirmed_write=args.confirm_local_db_write)

    def fetch(url: str) -> Mapping[str, Any]:
        nonlocal http_status
        http_status, payload = fetch_json(url)
        return payload

    try:
        dry_run_summary = run_eds_dry_run(
            dataset=args.dataset,
            price_area=args.price_area,
            limit=args.limit,
            fetch=fetch,
        )
        persistence_preview = run_eds_persistence_dry_run(
            dataset=args.dataset,
            normalized_records=dry_run_summary.normalized_records,
        )
    except urllib.error.HTTPError as exc:
        print_summary(
            request_url=request_url,
            http_status=exc.code,
            raw_count=0,
            normalized_count=0,
            sql_commands=[],
            committed=False,
            rolled_back=False,
        )
        print(
            f"HTTP request failed: server returned HTTP {exc.code} {exc.reason}",
            file=sys.stderr,
        )
        return 1
    except urllib.error.URLError as exc:
        print_summary(
            request_url=request_url,
            http_status="unavailable",
            raw_count=0,
            normalized_count=0,
            sql_commands=[],
            committed=False,
            rolled_back=False,
        )
        print(f"HTTP request failed: {exc.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print_summary(
            request_url=request_url,
            http_status="unavailable",
            raw_count=0,
            normalized_count=0,
            sql_commands=[],
            committed=False,
            rolled_back=False,
        )
        print(
            f"HTTP request failed: timed out after {DEFAULT_TIMEOUT_SECONDS} seconds",
            file=sys.stderr,
        )
        return 1
    except json.JSONDecodeError as exc:
        print_summary(
            request_url=request_url,
            http_status=http_status or "unavailable",
            raw_count=0,
            normalized_count=0,
            sql_commands=[],
            committed=False,
            rolled_back=False,
        )
        print(f"Response was not valid JSON: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print_summary(
            request_url=request_url,
            http_status=http_status or "unavailable",
            raw_count=0,
            normalized_count=0,
            sql_commands=[],
            committed=False,
            rolled_back=False,
        )
        print(f"Manual EDS local DB ingest failed: {exc}", file=sys.stderr)
        return 1

    sql_commands = list(persistence_preview["sql_commands"])
    if not args.confirm_local_db_write:
        print("Dry-run only. Re-run with --confirm-local-db-write to execute writes.")
        print_summary(
            request_url=dry_run_summary.request_url,
            http_status=http_status or "unavailable",
            raw_count=dry_run_summary.raw_record_count,
            normalized_count=dry_run_summary.normalized_record_count,
            sql_commands=sql_commands,
            committed=False,
            rolled_back=False,
        )
        return 0

    if not sql_commands:
        print("No SQL commands were generated; no local write was attempted.")
        print_summary(
            request_url=dry_run_summary.request_url,
            http_status=http_status or "unavailable",
            raw_count=dry_run_summary.raw_record_count,
            normalized_count=dry_run_summary.normalized_record_count,
            sql_commands=sql_commands,
            committed=False,
            rolled_back=False,
        )
        return 0

    connection = None
    try:
        connection = connect_with_available_dbapi_driver(database_url)
        transaction_result = execute_sql_commands_transaction(sql_commands, connection)
    except RuntimeError as exc:
        print(f"Database driver unavailable: {exc}", file=sys.stderr)
        print_summary(
            request_url=dry_run_summary.request_url,
            http_status=http_status or "unavailable",
            raw_count=dry_run_summary.raw_record_count,
            normalized_count=dry_run_summary.normalized_record_count,
            sql_commands=sql_commands,
            committed=False,
            rolled_back=False,
        )
        return 1
    except Exception as exc:
        print(f"Local database write failed: {exc}", file=sys.stderr)
        print_summary(
            request_url=dry_run_summary.request_url,
            http_status=http_status or "unavailable",
            raw_count=dry_run_summary.raw_record_count,
            normalized_count=dry_run_summary.normalized_record_count,
            sql_commands=sql_commands,
            committed=False,
            rolled_back=connection is not None,
        )
        return 1
    finally:
        if connection is not None:
            connection.close()

    print_summary(
        request_url=dry_run_summary.request_url,
        http_status=http_status or "unavailable",
        raw_count=dry_run_summary.raw_record_count,
        normalized_count=dry_run_summary.normalized_record_count,
        sql_commands=sql_commands,
        committed=bool(transaction_result["committed"]),
        rolled_back=bool(transaction_result["rolled_back"]),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
