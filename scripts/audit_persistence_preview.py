#!/usr/bin/env python3
"""Manual local dry-run preview for audit-event-v0 persistence planning."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.audit.events import build_audit_event  # noqa: E402
from app.audit.repository import build_audit_event_insert_sql  # noqa: E402


OCCURRED_AT_UTC = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
EVENT_TYPES = (
    "forecast_preview_requested",
    "current_risk_viewed",
    "report_summary_built",
    "report_markdown_rendered",
    "report_pdf_exported",
)
ACTOR_TYPE = "local_developer"
ACTOR_ID = "local-dev"
OUTCOME = "success"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic audit-event-v0 dictionary and a dry-run "
            "repository persistence plan without connecting to a database."
        )
    )
    parser.add_argument(
        "--event-type",
        choices=EVENT_TYPES,
        default="report_pdf_exported",
        help="Synthetic audit event type to preview. Default: report_pdf_exported.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print indented JSON instead of compact JSON.",
    )
    return parser


def build_preview_event(event_type: str) -> dict[str, Any]:
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


def build_persistence_plan(event: dict[str, Any]) -> dict[str, Any]:
    statement = build_audit_event_insert_sql(event)
    params = statement["params"]
    return {
        "table": statement["table"],
        "operation": statement["operation"],
        "sql_preview": statement["sql"],
        "params": params,
        "param_keys": sorted(params),
        "idempotency_key": statement["idempotency_key"],
        "event_id": event["event_id"],
        "conflict_behavior": "ON CONFLICT (event_id) DO NOTHING",
        "execution_performed": False,
    }


def serialize_for_json(value: Any) -> Any:
    if isinstance(value, datetime):
        return _format_utc_timestamp(value)
    if isinstance(value, dict):
        return {key: serialize_for_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_for_json(item) for item in value]
    return value


def _format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    args = build_parser().parse_args()

    event = build_preview_event(args.event_type)
    payload = {
        "dry_run": True,
        "database_write_performed": False,
        "requires_database_url": False,
        "read_only_decision_support": True,
        "no_automatic_control": True,
        "no_dispatch": True,
        "no_activation": True,
        "no_operational_energy_system_integration": True,
        "human_review_required": True,
        "event": event,
        "persistence_plan": build_persistence_plan(event),
    }

    indent = 2 if args.pretty else None
    separators = None if args.pretty else (",", ":")
    print(
        json.dumps(
            serialize_for_json(payload),
            indent=indent,
            sort_keys=True,
            separators=separators,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
