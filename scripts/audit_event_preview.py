#!/usr/bin/env python3
"""Manual synthetic local preview for audit-event-v0."""

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


OCCURRED_AT_UTC = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
EVENT_TYPES = (
    "forecast_preview_requested",
    "current_risk_viewed",
    "report_summary_built",
    "report_markdown_rendered",
    "report_pdf_exported",
)
EVENT_TYPE_CHOICES = (*EVENT_TYPES, "all")
ACTOR_TYPE = "local_developer"
OUTCOME = "success"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a manual synthetic local preview of audit-event-v0 using "
            "caller-provided sample fields."
        )
    )
    parser.add_argument(
        "--event-type",
        choices=EVENT_TYPE_CHOICES,
        default="all",
        help="Synthetic audit event type to preview. Default: all.",
    )
    parser.add_argument(
        "--actor-id",
        default="local-dev",
        help=(
            "Caller-provided actor id for the synthetic preview. "
            "Default: local-dev."
        ),
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print indented JSON instead of compact JSON.",
    )
    return parser


def build_preview_event(event_type: str, *, actor_id: str) -> dict[str, Any]:
    example = _event_example(event_type)
    return build_audit_event(
        event_type=event_type,
        actor_type=ACTOR_TYPE,
        actor_id=actor_id,
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


def print_scope_warning() -> None:
    print(
        "WARNING: synthetic local audit-event preview only. Uses caller-provided "
        "sample fields; does not require DATABASE_URL; does not persist audit "
        "logs, write files, access databases, run SQL, fetch Energi Data "
        "Service data, call weather APIs, start servers, expose API endpoints, "
        "run frontend code, schedule jobs, use cloud infrastructure, add "
        "secrets, add auth, train ML models, use LLMs, control assets, "
        "dispatch, activate, or perform operational functionality. Human "
        "review is required.",
        file=sys.stderr,
    )


def main() -> int:
    args = build_parser().parse_args()
    print_scope_warning()

    if args.event_type == "all":
        payload = {
            "events": [
                build_preview_event(event_type, actor_id=args.actor_id)
                for event_type in EVENT_TYPES
            ]
        }
    else:
        payload = {
            "event": build_preview_event(args.event_type, actor_id=args.actor_id)
        }

    json_payload = serialize_for_json(payload)
    indent = 2 if args.pretty else None
    separators = None if args.pretty else (",", ":")
    print(
        json.dumps(
            json_payload,
            indent=indent,
            sort_keys=True,
            separators=separators,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
