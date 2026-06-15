#!/usr/bin/env python3
"""Manual local audit-event-v0 database write smoke script."""

from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
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

from app.audit.events import SAFETY_BOUNDARY, build_audit_event  # noqa: E402
from app.audit.repository import build_audit_event_insert_sql  # noqa: E402


OCCURRED_AT_UTC = dt.datetime(2026, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
EVENT_TYPES = (
    "forecast_preview_requested",
    "current_risk_viewed",
    "report_summary_built",
    "report_markdown_rendered",
    "report_pdf_exported",
)
DEFAULT_EVENT_TYPE = "report_pdf_exported"
ACTOR_TYPE = "local_developer"
ACTOR_ID = "local-dev"
OUTCOME = "success"
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
CONFLICT_BEHAVIOR = "ON CONFLICT (event_id) DO NOTHING"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manually smoke-test one deterministic audit-event-v0 insert "
            "against an explicit local PostgreSQL database. Defaults to "
            "dry-run and does not connect to a database unless --execute is set."
        )
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print indented JSON instead of compact JSON.",
    )
    parser.add_argument(
        "--event-type",
        choices=EVENT_TYPES,
        default=DEFAULT_EVENT_TYPE,
        help=f"Synthetic audit event type. Default: {DEFAULT_EVENT_TYPE}.",
    )
    parser.add_argument(
        "--database-url",
        help=(
            "Explicit local PostgreSQL URL. Required with --execute. The raw "
            "value is never printed."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually write to the explicit local database URL.",
    )
    parser.add_argument(
        "--verify-read",
        action="store_true",
        help="After executing and committing, read the row back by event_id.",
    )
    return parser


def build_smoke_event(event_type: str) -> dict[str, Any]:
    example = _event_example(event_type)
    return build_audit_event(
        event_type=event_type,
        actor_type=ACTOR_TYPE,
        actor_id=ACTOR_ID,
        occurred_at_utc=OCCURRED_AT_UTC,
        resource_type=example["resource_type"],
        resource_id=example["resource_id"],
        action=example["action"],
        outcome=OUTCOME,
        decision_support_only=True,
        metadata=example["metadata"],
    )


def _event_example(event_type: str) -> dict[str, Any]:
    base_metadata: dict[str, Any] = {
        "price_area": "DK1",
        "synthetic_preview_only": True,
        "local_only": True,
    }
    examples: dict[str, dict[str, Any]] = {
        "forecast_preview_requested": {
            "resource_type": "forecast_preview",
            "resource_id": "forecast-window-v0:DK1:synthetic",
            "action": "preview_forecast_window",
            "metadata": {
                **base_metadata,
                "output_format": "json",
            },
        },
        "current_risk_viewed": {
            "resource_type": "current_risk",
            "resource_id": "rule-engine-v0:DK1:synthetic",
            "action": "view_current_risk",
            "metadata": {
                **base_metadata,
                "output_format": "json",
            },
        },
        "report_summary_built": {
            "resource_type": "report_summary",
            "resource_id": "report-summary-v0:DK1:synthetic",
            "action": "build_report_summary",
            "metadata": {
                **base_metadata,
                "report_version": "report-summary-v0",
                "output_format": "json",
            },
        },
        "report_markdown_rendered": {
            "resource_type": "report_markdown",
            "resource_id": "report-summary-v0:DK1:synthetic-markdown",
            "action": "render_report_markdown",
            "metadata": {
                **base_metadata,
                "report_version": "report-summary-v0",
                "output_format": "markdown",
            },
        },
        "report_pdf_exported": {
            "resource_type": "report_pdf",
            "resource_id": "report-summary-v0:DK1:synthetic-pdf",
            "action": "preview_report_pdf_export",
            "metadata": {
                **base_metadata,
                "report_version": "report-summary-v0",
                "output_format": "pdf",
            },
        },
    }
    return examples[event_type]


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

    if host is not None:
        try:
            ip_address = ipaddress.ip_address(host)
        except ValueError:
            raise ValueError("refusing non-local database URL") from None
        if not ip_address.is_loopback:
            raise ValueError("refusing non-local database URL")

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
    event: Mapping[str, Any],
    execute_requested: bool,
    warnings: list[str],
) -> dict[str, Any]:
    statement = build_audit_event_insert_sql(event)
    return {
        "dry_run": not execute_requested,
        "execute_requested": execute_requested,
        "database_write_performed": False,
        "verify_read_performed": False,
        "local_database_only": True,
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "table": statement["table"],
        "inserted_attempts": 0,
        "conflict_behavior": CONFLICT_BEHAVIOR,
        "rowcount_first_insert": None,
        "rowcount_second_insert": None,
        "safety_boundary": dict(SAFETY_BOUNDARY),
        "warnings": warnings,
    }


def execute_smoke_write(
    *,
    database_url: str,
    event: Mapping[str, Any],
    verify_read: bool,
) -> dict[str, Any]:
    statement = build_audit_event_insert_sql(event)
    connection = None
    try:
        connection = connect_with_psycopg(database_url)
        with connection.cursor() as cursor:
            cursor.execute(statement["sql"], statement["params"])
            rowcount_first = cursor.rowcount
            cursor.execute(statement["sql"], statement["params"])
            rowcount_second = cursor.rowcount
        connection.commit()

        verified_row = None
        if verify_read:
            with connection.cursor() as cursor:
                cursor.execute(
                    (
                        "SELECT event_id, event_version, event_type, actor_type, "
                        "actor_id, occurred_at_utc, resource_type, resource_id, "
                        "action, outcome, decision_support_only, safety_boundary, "
                        "metadata FROM audit_events WHERE event_id = %(event_id)s"
                    ),
                    {"event_id": event["event_id"]},
                )
                row = cursor.fetchone()
                if row is not None:
                    columns = [description[0] for description in cursor.description]
                    verified_row = dict(zip(columns, row, strict=True))

        result = {
            "database_write_performed": True,
            "verify_read_performed": verify_read,
            "inserted_attempts": 2,
            "rowcount_first_insert": rowcount_first,
            "rowcount_second_insert": rowcount_second,
        }
        if verify_read:
            result["verified_row"] = verified_row
        return result
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()


def connect_with_psycopg(database_url: str) -> Any:
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "psycopg is required for --execute; no database write was attempted"
        ) from exc
    return psycopg.connect(database_url)


def serialize_for_json(value: Any) -> Any:
    if isinstance(value, (dt.datetime, dt.date, dt.time)):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {key: serialize_for_json(item) for key, item in value.items()}
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
    event = build_smoke_event(args.event_type)
    warnings: list[str] = []
    payload = build_base_payload(
        event=event,
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
            "dry-run only; no database connection opened and no write performed"
        )
        if args.verify_read:
            warnings.append("--verify-read ignored without --execute")
        print_json(payload, pretty=args.pretty)
        return 0

    try:
        validate_local_database_url(args.database_url)
    except ValueError as exc:
        warnings.append(str(exc))
        print_json(payload, pretty=args.pretty)
        return 2

    try:
        payload.update(
            execute_smoke_write(
                database_url=args.database_url,
                event=event,
                verify_read=args.verify_read,
            )
        )
    except Exception as exc:
        warnings.append(f"database smoke write failed safely: {type(exc).__name__}")
        print_json(payload, pretty=args.pretty)
        return 1

    print_json(payload, pretty=args.pretty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
