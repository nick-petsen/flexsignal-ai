from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from app.audit.repository import build_audit_event_insert_sql
from app.audit.runtime_events import (
    DEFAULT_ACTOR_ID,
    DEFAULT_ACTOR_TYPE,
    DEFAULT_FORECAST_WINDOW_VERSION,
    DEFAULT_REPORT_VERSION,
    build_current_risk_viewed_event,
    build_forecast_preview_requested_event,
    build_report_markdown_rendered_event,
    build_report_pdf_exported_event,
    build_report_summary_built_event,
)


CONFLICT_BEHAVIOR = "ON CONFLICT (event_id) DO NOTHING"
RUNTIME_AUDIT_PLAN_VERSION = "audit-runtime-persistence-plan-v0"


def build_current_risk_viewed_audit_plan(
    *,
    price_area: str,
    actor_type: str = DEFAULT_ACTOR_TYPE,
    actor_id: str | None = DEFAULT_ACTOR_ID,
    occurred_at_utc: datetime | None = None,
    request_id: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    event = build_current_risk_viewed_event(
        price_area=price_area,
        actor_type=actor_type,
        actor_id=actor_id,
        occurred_at_utc=occurred_at_utc,
        request_id=request_id,
        source=source,
    )
    return _build_runtime_plan(event)


def build_forecast_preview_requested_audit_plan(
    *,
    price_area: str,
    actor_type: str = DEFAULT_ACTOR_TYPE,
    actor_id: str | None = DEFAULT_ACTOR_ID,
    occurred_at_utc: datetime | None = None,
    request_id: str | None = None,
    source: str | None = None,
    forecast_window_version: str = DEFAULT_FORECAST_WINDOW_VERSION,
    model_version: str | None = None,
) -> dict[str, Any]:
    event = build_forecast_preview_requested_event(
        price_area=price_area,
        actor_type=actor_type,
        actor_id=actor_id,
        occurred_at_utc=occurred_at_utc,
        request_id=request_id,
        source=source,
        forecast_window_version=forecast_window_version,
        model_version=model_version,
    )
    return _build_runtime_plan(event)


def build_report_summary_built_audit_plan(
    *,
    price_area: str,
    actor_type: str = DEFAULT_ACTOR_TYPE,
    actor_id: str | None = DEFAULT_ACTOR_ID,
    occurred_at_utc: datetime | None = None,
    request_id: str | None = None,
    source: str | None = None,
    report_version: str = DEFAULT_REPORT_VERSION,
) -> dict[str, Any]:
    event = build_report_summary_built_event(
        price_area=price_area,
        actor_type=actor_type,
        actor_id=actor_id,
        occurred_at_utc=occurred_at_utc,
        request_id=request_id,
        source=source,
        report_version=report_version,
    )
    return _build_runtime_plan(event)


def build_report_markdown_rendered_audit_plan(
    *,
    price_area: str,
    actor_type: str = DEFAULT_ACTOR_TYPE,
    actor_id: str | None = DEFAULT_ACTOR_ID,
    occurred_at_utc: datetime | None = None,
    request_id: str | None = None,
    source: str | None = None,
    report_version: str = DEFAULT_REPORT_VERSION,
    output_format: str = "markdown",
) -> dict[str, Any]:
    event = build_report_markdown_rendered_event(
        price_area=price_area,
        actor_type=actor_type,
        actor_id=actor_id,
        occurred_at_utc=occurred_at_utc,
        request_id=request_id,
        source=source,
        report_version=report_version,
        output_format=output_format,
    )
    return _build_runtime_plan(event)


def build_report_pdf_exported_audit_plan(
    *,
    price_area: str,
    actor_type: str = DEFAULT_ACTOR_TYPE,
    actor_id: str | None = DEFAULT_ACTOR_ID,
    occurred_at_utc: datetime | None = None,
    request_id: str | None = None,
    source: str | None = None,
    report_version: str = DEFAULT_REPORT_VERSION,
    output_format: str = "pdf",
) -> dict[str, Any]:
    event = build_report_pdf_exported_event(
        price_area=price_area,
        actor_type=actor_type,
        actor_id=actor_id,
        occurred_at_utc=occurred_at_utc,
        request_id=request_id,
        source=source,
        report_version=report_version,
        output_format=output_format,
    )
    return _build_runtime_plan(event)


def _build_runtime_plan(event: Mapping[str, Any]) -> dict[str, Any]:
    statement = build_audit_event_insert_sql(event)
    params = statement["params"]
    persistence_plan = {
        "plan_version": RUNTIME_AUDIT_PLAN_VERSION,
        "table": statement["table"],
        "operation": statement["operation"],
        "sql_preview": statement["sql"],
        "params": params,
        "param_keys": sorted(params),
        "idempotency_key": statement["idempotency_key"],
        "event_id": event["event_id"],
        "conflict_behavior": CONFLICT_BEHAVIOR,
        "execution_performed": False,
    }

    return {
        "dry_run": True,
        "database_write_performed": False,
        "requires_database_url": False,
        "event": dict(event),
        "persistence_plan": persistence_plan,
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "table": statement["table"],
        "conflict_behavior": CONFLICT_BEHAVIOR,
        "safety_boundary": _plan_safety_boundary(event),
        "warnings": [
            "Dry-run plan only; no database write was performed.",
            "Runtime wiring is deferred to a separately reviewed step.",
        ],
    }


def _plan_safety_boundary(event: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "event_version": event["event_version"],
        "decision_support_only": event["decision_support_only"],
        **dict(event["safety_boundary"]),
    }
