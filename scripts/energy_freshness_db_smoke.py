#!/usr/bin/env python3
"""Manual local DB smoke script for energy freshness reads."""

from __future__ import annotations

import argparse
import datetime as dt
import decimal
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.repositories.energy_freshness import (  # noqa: E402
    build_energy_freshness_summary_plan,
)
from app.db.repositories.energy_freshness_reader import (  # noqa: E402
    SAFETY_BOUNDARY,
    read_energy_freshness_summary,
)


SUPPORTED_PRICE_AREAS = ("DK1", "DK2")
DEFAULT_PRICE_AREA = "DK1"
LOCAL_HOSTS = {"localhost", "127.0.0.1"}
FORBIDDEN_REMOTE_MARKERS = (
    "azure",
    "amazonaws",
    "supabase",
    "neon",
    "render",
    "railway",
    "heroku",
    "digitalocean",
    "google",
    "cloud",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manually smoke-test energy freshness SELECT reads against an "
            "explicit local PostgreSQL database. Defaults to dry-run and does "
            "not connect to a database unless --execute is set."
        )
    )
    parser.add_argument(
        "--price-area",
        choices=SUPPORTED_PRICE_AREAS,
        default=DEFAULT_PRICE_AREA,
        help=f"Energy price area to inspect. Default: {DEFAULT_PRICE_AREA}.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print indented JSON instead of compact JSON.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the freshness SELECT reads against the explicit local URL.",
    )
    parser.add_argument(
        "--database-url",
        help=(
            "Explicit local PostgreSQL URL. Required with --execute. The raw "
            "value is never printed."
        ),
    )
    return parser


def validate_local_database_url(database_url: str | None) -> str:
    if not database_url:
        raise ValueError("database URL is required for --execute")

    lowered = database_url.lower()
    for marker in FORBIDDEN_REMOTE_MARKERS:
        if marker in lowered:
            raise ValueError("refusing non-local database URL")

    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise ValueError("database URL must use postgresql:// or postgres://")

    host = parsed.hostname
    if host in LOCAL_HOSTS:
        return host

    if host is None and _is_local_socket_style_url(parsed):
        return "local"

    raise ValueError("refusing non-local database URL")


def _is_local_socket_style_url(parsed: Any) -> bool:
    if parsed.netloc:
        return False
    if not parsed.path or parsed.path == "/":
        return False

    query = parse_qs(parsed.query)
    host_values = query.get("host", [])
    if not host_values:
        return True
    return all(value.startswith("/") for value in host_values)


def build_base_payload(
    *,
    price_area: str,
    execute_requested: bool,
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "price_area": price_area,
        "dry_run": not execute_requested,
        "execute_requested": execute_requested,
        "database_query_executed": False,
        "database_write_performed": False,
        "requires_database_url": execute_requested,
        "local_database_only": True,
        "warnings": warnings,
        "safety_boundary": dict(SAFETY_BOUNDARY),
    }


def build_dry_run_payload(
    *,
    price_area: str,
    execute_requested: bool,
    warnings: list[str],
) -> dict[str, Any]:
    payload = build_base_payload(
        price_area=price_area,
        execute_requested=execute_requested,
        warnings=warnings,
    )
    payload["freshness_plan"] = build_energy_freshness_summary_plan(price_area)
    return payload


def execute_freshness_read(
    *,
    database_url: str,
    price_area: str,
) -> dict[str, Any]:
    connection = None
    try:
        connection = connect_with_psycopg(database_url)
        return read_energy_freshness_summary(connection, price_area)
    finally:
        if connection is not None:
            connection.close()


def connect_with_psycopg(database_url: str) -> Any:
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required for --execute; no database read was attempted"
        ) from exc
    return psycopg.connect(database_url)


def serialize_for_json(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return {key: serialize_for_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [serialize_for_json(item) for item in value]
    if isinstance(value, list):
        return [serialize_for_json(item) for item in value]
    return value


def print_json(payload: Mapping[str, Any], *, pretty: bool) -> None:
    indent = 2 if pretty else None
    separators = None if pretty else (",", ":")
    print(
        json.dumps(
            serialize_for_json(payload),
            indent=indent,
            sort_keys=True,
            separators=separators,
        )
    )


def main() -> int:
    args = build_parser().parse_args()
    warnings: list[str] = []
    payload = build_dry_run_payload(
        price_area=args.price_area,
        execute_requested=args.execute,
        warnings=warnings,
    )

    if args.database_url:
        try:
            validate_local_database_url(args.database_url)
        except ValueError as exc:
            warnings.append(str(exc))
            print_json(payload, pretty=args.pretty)
            return 2

    if not args.execute:
        warnings.append(
            "dry-run only; no database connection opened and no SQL executed"
        )
        print_json(payload, pretty=args.pretty)
        return 0

    try:
        validate_local_database_url(args.database_url)
    except ValueError as exc:
        warnings.append(str(exc))
        print_json(payload, pretty=args.pretty)
        return 2

    try:
        result = execute_freshness_read(
            database_url=args.database_url,
            price_area=args.price_area,
        )
    except Exception as exc:
        warnings.append(f"database freshness read failed safely: {type(exc).__name__}")
        print_json(payload, pretty=args.pretty)
        return 1

    payload.pop("freshness_plan", None)
    payload["dry_run"] = False
    payload["database_query_executed"] = bool(result["database_query_executed"])
    payload["database_write_performed"] = bool(result["database_write_performed"])
    payload["freshness_result"] = result
    warnings.extend(result.get("warnings", []))
    print_json(payload, pretty=args.pretty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
