from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.audit.runtime_events import DEFAULT_ACTOR_ID
from app.audit.runtime_events import build_report_pdf_export_requested_event
from app.audit.runtime_plan import (
    build_current_risk_viewed_audit_plan,
    build_forecast_preview_requested_audit_plan,
    build_report_markdown_rendered_audit_plan,
    build_report_pdf_export_requested_audit_plan,
    build_report_pdf_exported_audit_plan,
    build_report_summary_built_audit_plan,
)
from app.audit.writer import write_audit_event


router = APIRouter(prefix="/api/audit", tags=["audit"])

DEFAULT_API_ACTOR_TYPE = "local_user"
SUPPORTED_PRICE_AREAS = frozenset({"DK1", "DK2"})

PlanBuilder = Callable[..., dict[str, Any]]

PLAN_BUILDERS: dict[str, PlanBuilder] = {
    "current_risk_viewed": build_current_risk_viewed_audit_plan,
    "forecast_preview_requested": build_forecast_preview_requested_audit_plan,
    "report_summary_built": build_report_summary_built_audit_plan,
    "report_markdown_rendered": build_report_markdown_rendered_audit_plan,
    "report_pdf_export_requested": build_report_pdf_export_requested_audit_plan,
    "report_pdf_exported": build_report_pdf_exported_audit_plan,
}


class AuditPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(min_length=1)
    price_area: str = Field(default="DK1", min_length=1)
    actor_type: str | None = Field(default=None, min_length=1)
    actor_id: str | None = Field(default=None, min_length=1)
    request_id: str | None = Field(default=None, min_length=1)
    source: str | None = Field(default=None, min_length=1)
    occurred_at_utc: datetime | None = None
    output_format: str | None = Field(default=None, min_length=1)
    report_version: str | None = Field(default=None, min_length=1)
    forecast_window_version: str | None = Field(default=None, min_length=1)

    @field_validator("occurred_at_utc")
    @classmethod
    def occurred_at_must_be_timezone_aware(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is not None and (
            value.tzinfo is None or value.utcoffset() is None
        ):
            raise ValueError("occurred_at_utc must be timezone-aware")
        return value


class AuditPdfExportPersistRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_area: str = Field(default="DK1", min_length=1)
    actor_type: str | None = Field(default=None, min_length=1)
    actor_id: str | None = Field(default=None, min_length=1)
    request_id: str | None = Field(default=None, min_length=1)
    source: str | None = Field(default=None, min_length=1)
    occurred_at_utc: datetime | None = None

    @field_validator("occurred_at_utc")
    @classmethod
    def occurred_at_must_be_timezone_aware(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is not None and (
            value.tzinfo is None or value.utcoffset() is None
        ):
            raise ValueError("occurred_at_utc must be timezone-aware")
        return value


@router.post("/preview")
def preview_audit_persistence_plan(
    payload: AuditPreviewRequest,
) -> dict[str, Any]:
    event_type = _normalized_text(payload.event_type, field_name="event_type")
    price_area = _normalized_text(payload.price_area, field_name="price_area")

    if event_type not in PLAN_BUILDERS:
        raise HTTPException(status_code=400, detail="Unsupported event_type")
    if price_area not in SUPPORTED_PRICE_AREAS:
        raise HTTPException(status_code=400, detail="Unsupported price_area")

    builder = PLAN_BUILDERS[event_type]
    try:
        return builder(
            **_builder_kwargs(
                payload,
                event_type=event_type,
                price_area=price_area,
            ),
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/pdf-export/persist")
def persist_pdf_export_audit_event(
    payload: AuditPdfExportPersistRequest | None = None,
) -> dict[str, Any]:
    payload = payload or AuditPdfExportPersistRequest()
    price_area = _normalized_text(payload.price_area, field_name="price_area")

    if price_area not in SUPPORTED_PRICE_AREAS:
        raise HTTPException(status_code=400, detail="Unsupported price_area")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "warning": (
                    "DATABASE_URL is required at request time; no audit event "
                    "database write was attempted."
                ),
                "audit_event_created": False,
                "audit_event_persisted": False,
                "database_query_executed": False,
                "database_write_performed": False,
                "requires_database_url": True,
                "table": "audit_events",
            },
        )

    try:
        event = build_report_pdf_export_requested_event(
            price_area=price_area,
            actor_type=payload.actor_type or DEFAULT_API_ACTOR_TYPE,
            actor_id=payload.actor_id or DEFAULT_ACTOR_ID,
            occurred_at_utc=payload.occurred_at_utc,
            request_id=payload.request_id,
            source=payload.source,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    connection = None
    try:
        connection = connect_with_psycopg(database_url)
        write_result = write_audit_event(connection, event)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - real DB failures are env-specific
        raise HTTPException(
            status_code=503,
            detail="Audit event database write failed",
        ) from exc
    finally:
        if connection is not None:
            close = getattr(connection, "close", None)
            if callable(close):
                close()

    return {
        "audit_event_created": True,
        "audit_event_persisted": True,
        "database_query_executed": False,
        "database_write_performed": True,
        "requires_database_url": True,
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "table": write_result["table"],
        "conflict_behavior": write_result["conflict_behavior"],
        "safety_boundary": _event_safety_boundary(event),
        "event": event,
        "warnings": [
            "Persisted one audit-event-v0 row to audit_events only.",
            "No PDF was generated and no file was written.",
            "No energy data tables were read or written.",
        ],
    }


def connect_with_psycopg(database_url: str) -> Any:
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - depends on deployment env
        raise RuntimeError("Database driver is not installed") from exc

    return psycopg.connect(database_url, autocommit=True)


def _builder_kwargs(
    payload: AuditPreviewRequest,
    *,
    event_type: str,
    price_area: str,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "price_area": price_area,
        "actor_type": payload.actor_type or DEFAULT_API_ACTOR_TYPE,
        "actor_id": payload.actor_id or DEFAULT_ACTOR_ID,
        "occurred_at_utc": payload.occurred_at_utc,
        "request_id": payload.request_id,
        "source": payload.source,
    }

    if event_type == "forecast_preview_requested":
        if payload.forecast_window_version is not None:
            kwargs["forecast_window_version"] = payload.forecast_window_version
    elif event_type in {
        "report_summary_built",
        "report_markdown_rendered",
        "report_pdf_export_requested",
        "report_pdf_exported",
    }:
        if payload.report_version is not None:
            kwargs["report_version"] = payload.report_version
        if (
            event_type
            in {
                "report_markdown_rendered",
                "report_pdf_exported",
                "report_pdf_export_requested",
            }
            and payload.output_format is not None
        ):
            kwargs["output_format"] = payload.output_format

    return kwargs


def _normalized_text(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    return normalized


def _event_safety_boundary(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_version": event["event_version"],
        "decision_support_only": event["decision_support_only"],
        **dict(event["safety_boundary"]),
        "pdf_generated_in_memory": event["metadata"]["pdf_generated_in_memory"],
        "server_side_file_written": event["metadata"]["server_side_file_written"],
        "database_query_executed": event["metadata"]["database_query_executed"],
        "no_control_dispatch_activation": event["metadata"][
            "no_control_dispatch_activation"
        ],
    }
