from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.audit.runtime_events import DEFAULT_ACTOR_ID
from app.audit.runtime_plan import (
    build_current_risk_viewed_audit_plan,
    build_forecast_preview_requested_audit_plan,
    build_report_markdown_rendered_audit_plan,
    build_report_pdf_exported_audit_plan,
    build_report_summary_built_audit_plan,
)


router = APIRouter(prefix="/api/audit", tags=["audit"])

DEFAULT_API_ACTOR_TYPE = "local_user"
SUPPORTED_PRICE_AREAS = frozenset({"DK1", "DK2"})

PlanBuilder = Callable[..., dict[str, Any]]

PLAN_BUILDERS: dict[str, PlanBuilder] = {
    "current_risk_viewed": build_current_risk_viewed_audit_plan,
    "forecast_preview_requested": build_forecast_preview_requested_audit_plan,
    "report_summary_built": build_report_summary_built_audit_plan,
    "report_markdown_rendered": build_report_markdown_rendered_audit_plan,
    "report_pdf_exported": build_report_pdf_exported_audit_plan,
}


class AuditPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(min_length=1)
    price_area: str = Field(min_length=1)
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
        "report_pdf_exported",
    }:
        if payload.report_version is not None:
            kwargs["report_version"] = payload.report_version
        if (
            event_type in {"report_markdown_rendered", "report_pdf_exported"}
            and payload.output_format is not None
        ):
            kwargs["output_format"] = payload.output_format

    return kwargs


def _normalized_text(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    return normalized
