from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.audit.runtime_events import DEFAULT_ACTOR_ID
from app.audit.runtime_events import build_report_pdf_export_requested_event
from app.audit.writer import write_audit_event
from app.reporting.markdown import render_report_summary_markdown
from app.reporting.pdf import render_report_markdown_pdf_bytes
from app.reporting.summary import build_report_summary


PriceArea = Literal["DK1", "DK2"]
PreviewScenario = Literal["standard", "high-risk"]

router = APIRouter(prefix="/api/report", tags=["report"])

DEFAULT_GENERATED_AT_UTC = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

SAFETY_BOUNDARY = {
    "read_only_decision_support": True,
    "no_automatic_control": True,
    "no_dispatch": True,
    "no_activation": True,
    "no_operational_energy_system_integration": True,
    "human_review_required": True,
}

PREVIEW_SOURCE_NOTES = [
    "synthetic or caller-provided preview data only",
    "does not generate PDF output",
    "does not write files",
    "does not access databases or execute SQL",
    "does not call live Energi Data Service or DMI/weather APIs",
    "does not use ML or LLM behavior",
]

MARKDOWN_PREVIEW_SOURCE_NOTES = [
    "JSON/Markdown preview only",
    "no PDF generated",
    "no file written",
    "no database read/write",
    "no live EDS/DMI calls",
    "no control, dispatch, or activation",
    "read-only decision support; human review required",
]

PDF_PREVIEW_WARNINGS = [
    "dry-run preview only",
    "no PDF generated",
    "no file written",
    "no database read/write",
    "no live EDS/DMI calls",
    "no control, dispatch, or activation",
]

PDF_PREVIEW_SOURCE_NOTES = [
    "PDF dry-run preview only",
    "planned source: report-summary-v0 + markdown preview",
    "planned output format: pdf",
    *PDF_PREVIEW_WARNINGS,
    "read-only decision support; human review required",
]

PDF_EXPORT_SOURCE_NOTES = [
    "PDF export uses synthetic or caller-provided preview data only",
    "PDF bytes generated in memory only",
    "no file written",
    "no file path returned",
    "no database read/write",
    "no live EDS/DMI calls",
    "no ML or LLM behavior",
    "no control, dispatch, or activation",
    "read-only decision support; human review required",
]

MARKDOWN_EXCERPT_CHARACTER_LIMIT = 800
PDF_EXPORT_FILENAME = "flexsignal-report-preview.pdf"
PDF_EXPORT_HEADERS = {
    "Content-Disposition": f'attachment; filename="{PDF_EXPORT_FILENAME}"',
    "X-FlexSignal-Decision-Support-Only": "true",
    "X-FlexSignal-File-Written": "false",
    "X-FlexSignal-Database-Query-Executed": "false",
    "X-FlexSignal-Database-Write-Performed": "false",
    "X-FlexSignal-Requires-Database-Url": "false",
}
AUDITED_PDF_EXPORT_HEADERS = {
    "Content-Disposition": f'attachment; filename="{PDF_EXPORT_FILENAME}"',
    "X-FlexSignal-Decision-Support-Only": "true",
    "X-FlexSignal-File-Written": "false",
    "X-FlexSignal-Pdf-Generated-In-Memory": "true",
    "X-FlexSignal-Audit-Event-Created": "true",
    "X-FlexSignal-Audit-Event-Persisted": "true",
    "X-FlexSignal-Audit-Event-Type": "report_pdf_export_requested",
    "X-FlexSignal-Audit-Table": "audit_events",
    "X-FlexSignal-Database-Query-Executed": "false",
    "X-FlexSignal-Database-Write-Performed": "true",
    "X-FlexSignal-Database-Write-Scope": "audit_events_only",
    "X-FlexSignal-Requires-Database-Url": "true",
    "X-FlexSignal-No-Control-Dispatch-Activation": "true",
}
DEFAULT_API_ACTOR_TYPE = "local_user"


class ReportSummaryPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_area: PriceArea = "DK1"
    generated_at_utc: datetime = DEFAULT_GENERATED_AT_UTC
    scenario: PreviewScenario = "standard"
    title: str | None = Field(default=None, min_length=1)
    current_risk: dict[str, Any] | None = None
    forecast: dict[str, Any] | None = None
    source_notes: list[str] = Field(default_factory=list)

    @field_validator("generated_at_utc")
    @classmethod
    def generated_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return value


class AuditedReportPdfExportRequest(ReportSummaryPreviewRequest):
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


class ReportSummaryPreviewResponse(BaseModel):
    report_preview_generated: bool
    pdf_generated: bool
    file_written: bool
    database_query_executed: bool
    database_write_performed: bool
    requires_database_url: bool
    decision_support_only: bool
    report_summary: dict[str, Any] = Field(
        description=(
            "Preserves current_risk_summary.confidence_score for compatibility. "
            "That score is an uncalibrated, rule-based internal "
            "input-availability heuristic, not forecast certainty."
        )
    )
    recommendations: list[str]
    explanation: str
    safety_boundary: dict[str, bool]


class ReportMarkdownPreviewResponse(BaseModel):
    markdown_preview_generated: bool
    pdf_generated: bool
    file_written: bool
    database_query_executed: bool
    database_write_performed: bool
    requires_database_url: bool
    decision_support_only: bool
    markdown: str
    report_summary: dict[str, Any] = Field(
        description=(
            "Preserves current_risk_summary.confidence_score for compatibility. "
            "That score is an uncalibrated, rule-based internal "
            "input-availability heuristic, not forecast certainty."
        )
    )
    safety_boundary: dict[str, bool]


class ReportPdfPreviewResponse(BaseModel):
    pdf_preview_planned: bool
    pdf_generated: bool
    file_written: bool
    markdown_preview_generated: bool
    database_query_executed: bool
    database_write_performed: bool
    requires_database_url: bool
    decision_support_only: bool
    planned_source: str
    planned_output_format: str
    report_summary: dict[str, Any] = Field(
        description=(
            "Preserves current_risk_summary.confidence_score for compatibility. "
            "That score is an uncalibrated, rule-based internal "
            "input-availability heuristic, not forecast certainty."
        )
    )
    markdown_excerpt: str
    markdown_character_count: int
    safety_boundary: dict[str, bool]
    warnings: list[str]


@router.post("/summary/preview", response_model=ReportSummaryPreviewResponse)
def preview_report_summary(
    payload: ReportSummaryPreviewRequest | None = None,
) -> dict[str, Any]:
    request = payload or ReportSummaryPreviewRequest()
    current_risk, forecast = _preview_inputs(request)

    try:
        report_summary = build_report_summary(
            price_area=request.price_area,
            generated_at_utc=request.generated_at_utc,
            current_risk=current_risk,
            forecast=forecast,
            title=request.title,
            source_notes=[*PREVIEW_SOURCE_NOTES, *request.source_notes],
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "report_preview_generated": True,
        "pdf_generated": False,
        "file_written": False,
        "database_query_executed": False,
        "database_write_performed": False,
        "requires_database_url": False,
        "decision_support_only": True,
        "report_summary": report_summary,
        "recommendations": list(report_summary["recommended_human_actions"]),
        "explanation": (
            "Read-only report summary preview built from deterministic "
            "synthetic or caller-provided data. No PDF, file, database, SQL, "
            "external API, ML, LLM, control, dispatch, or activation behavior "
            "is performed."
        ),
        "safety_boundary": dict(SAFETY_BOUNDARY),
    }


@router.post("/markdown/preview", response_model=ReportMarkdownPreviewResponse)
def preview_report_markdown(
    payload: ReportSummaryPreviewRequest | None = None,
) -> dict[str, Any]:
    request = payload or ReportSummaryPreviewRequest()
    current_risk, forecast = _preview_inputs(request)

    try:
        report_summary = build_report_summary(
            price_area=request.price_area,
            generated_at_utc=request.generated_at_utc,
            current_risk=current_risk,
            forecast=forecast,
            title=request.title,
            source_notes=[
                *PREVIEW_SOURCE_NOTES,
                *MARKDOWN_PREVIEW_SOURCE_NOTES,
                *request.source_notes,
            ],
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    markdown = render_report_summary_markdown(report_summary)

    return {
        "markdown_preview_generated": True,
        "pdf_generated": False,
        "file_written": False,
        "database_query_executed": False,
        "database_write_performed": False,
        "requires_database_url": False,
        "decision_support_only": True,
        "markdown": markdown,
        "report_summary": report_summary,
        "safety_boundary": dict(SAFETY_BOUNDARY),
    }


@router.post("/pdf/preview", response_model=ReportPdfPreviewResponse)
def preview_report_pdf(
    payload: ReportSummaryPreviewRequest | None = None,
) -> dict[str, Any]:
    request = payload or ReportSummaryPreviewRequest()
    current_risk, forecast = _preview_inputs(request)

    try:
        report_summary = build_report_summary(
            price_area=request.price_area,
            generated_at_utc=request.generated_at_utc,
            current_risk=current_risk,
            forecast=forecast,
            title=request.title,
            source_notes=[
                *PREVIEW_SOURCE_NOTES,
                *MARKDOWN_PREVIEW_SOURCE_NOTES,
                *PDF_PREVIEW_SOURCE_NOTES,
                *request.source_notes,
            ],
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    markdown = render_report_summary_markdown(report_summary)

    return {
        "pdf_preview_planned": True,
        "pdf_generated": False,
        "file_written": False,
        "markdown_preview_generated": True,
        "database_query_executed": False,
        "database_write_performed": False,
        "requires_database_url": False,
        "decision_support_only": True,
        "planned_source": "report-summary-v0 + markdown preview",
        "planned_output_format": "pdf",
        "report_summary": report_summary,
        "markdown_excerpt": markdown[:MARKDOWN_EXCERPT_CHARACTER_LIMIT],
        "markdown_character_count": len(markdown),
        "safety_boundary": dict(SAFETY_BOUNDARY),
        "warnings": list(PDF_PREVIEW_WARNINGS),
    }


@router.post("/pdf/export")
def export_report_pdf(
    payload: ReportSummaryPreviewRequest | None = None,
) -> Response:
    request = payload or ReportSummaryPreviewRequest()

    try:
        pdf_bytes = _render_report_pdf_bytes(request)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=dict(PDF_EXPORT_HEADERS),
    )


@router.post("/pdf/export/audited")
def export_report_pdf_audited(
    payload: AuditedReportPdfExportRequest | None = None,
) -> Response:
    request = payload or AuditedReportPdfExportRequest()

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "warning": (
                    "DATABASE_URL is required at request time; no audit event "
                    "database write or PDF export was attempted."
                ),
                "audit_event_created": False,
                "audit_event_persisted": False,
                "pdf_generated_in_memory": False,
                "server_side_file_written": False,
                "database_query_executed": False,
                "database_write_performed": False,
                "requires_database_url": True,
                "table": "audit_events",
            },
        )

    try:
        event = build_report_pdf_export_requested_event(
            price_area=request.price_area,
            actor_type=request.actor_type or DEFAULT_API_ACTOR_TYPE,
            actor_id=request.actor_id or DEFAULT_ACTOR_ID,
            occurred_at_utc=request.occurred_at_utc,
            request_id=request.request_id,
            source=request.source,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    connection = None
    try:
        connection = connect_with_psycopg(database_url)
        write_result = write_audit_event(connection, event)
        pdf_bytes = _render_report_pdf_bytes(request)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - real DB failures are env-specific
        raise HTTPException(
            status_code=503,
            detail="Audited PDF export failed",
        ) from exc
    finally:
        if connection is not None:
            close = getattr(connection, "close", None)
            if callable(close):
                close()

    headers = {
        **AUDITED_PDF_EXPORT_HEADERS,
        "X-FlexSignal-Audit-Event-Id": event["event_id"],
        "X-FlexSignal-Audit-Table": write_result["table"],
    }
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers,
    )


def connect_with_psycopg(database_url: str) -> Any:
    try:
        psycopg_module = __import__("psycopg")
    except ImportError as exc:  # pragma: no cover - depends on deployment env
        raise RuntimeError("Database driver is not installed") from exc

    psycopg_connect = getattr(psycopg_module, "connect")
    return psycopg_connect(database_url, autocommit=True)


def _render_report_pdf_bytes(request: ReportSummaryPreviewRequest) -> bytes:
    current_risk, forecast = _preview_inputs(request)

    report_summary = build_report_summary(
        price_area=request.price_area,
        generated_at_utc=request.generated_at_utc,
        current_risk=current_risk,
        forecast=forecast,
        title=request.title,
        source_notes=[
            *PDF_EXPORT_SOURCE_NOTES,
            *request.source_notes,
        ],
    )
    markdown = render_report_summary_markdown(report_summary)
    return render_report_markdown_pdf_bytes(
        markdown,
        title=report_summary.get("title"),
    )


def _preview_inputs(
    request: ReportSummaryPreviewRequest,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current_risk = request.current_risk
    forecast = request.forecast

    if current_risk is None:
        current_risk = (
            _high_current_risk()
            if request.scenario == "high-risk"
            else _medium_current_risk()
        )
    if forecast is None:
        forecast = (
            _high_risk_forecast()
            if request.scenario == "high-risk"
            else _standard_forecast()
        )

    return current_risk, forecast


def _medium_current_risk() -> dict[str, Any]:
    return {
        "risk_level": "medium",
        "risk_score": 45,
        "confidence_score": 0.9,
        "reason_codes": ["LOW_PRICE", "MODERATE_RENEWABLE_SHARE"],
        "recommended_human_action": (
            "Review local operating context before any planning decision."
        ),
        "model_version": "rule-engine-v0",
        "decision_support_only": True,
    }


def _high_current_risk() -> dict[str, Any]:
    return {
        "risk_level": "high",
        "risk_score": 75,
        "confidence_score": 0.95,
        "reason_codes": ["NEGATIVE_PRICE", "HIGH_RENEWABLE_SHARE"],
        "recommended_human_action": (
            "Escalate for human review before any operational planning."
        ),
        "model_version": "rule-engine-v0",
        "decision_support_only": True,
    }


def _standard_forecast() -> dict[str, Any]:
    return _forecast(
        [
            _window(
                "0-24h",
                risk_level="low",
                row_count=2,
                max_risk_score=30,
                average_risk_score=22.5,
                top_reason_codes=[
                    {"reason_code": "NORMAL_PRICE", "count": 2},
                    {"reason_code": "LOW_RENEWABLE_SHARE", "count": 1},
                ],
                action="Continue routine human monitoring.",
            ),
            _window(
                "24-48h",
                risk_level="medium",
                row_count=2,
                max_risk_score=55,
                average_risk_score=42.5,
                top_reason_codes=[
                    {"reason_code": "LOW_PRICE", "count": 1},
                    {"reason_code": "MODERATE_RENEWABLE_SHARE", "count": 1},
                ],
                action="Review the medium-risk window before planning.",
            ),
            _window(
                "48-72h",
                risk_level="low",
                row_count=2,
                max_risk_score=25,
                average_risk_score=20.0,
                top_reason_codes=[
                    {"reason_code": "NORMAL_PRICE", "count": 2},
                ],
                action="Continue routine human monitoring.",
            ),
        ]
    )


def _high_risk_forecast() -> dict[str, Any]:
    return _forecast(
        [
            _window(
                "0-24h",
                risk_level="medium",
                row_count=2,
                max_risk_score=55,
                average_risk_score=40.0,
                top_reason_codes=[
                    {"reason_code": "LOW_PRICE", "count": 1},
                    {"reason_code": "MODERATE_RENEWABLE_SHARE", "count": 1},
                ],
                action="Review the near-term medium-risk window.",
            ),
            _window(
                "24-48h",
                risk_level="high",
                row_count=2,
                max_risk_score=80,
                average_risk_score=72.5,
                top_reason_codes=[
                    {"reason_code": "NEGATIVE_PRICE", "count": 1},
                    {"reason_code": "HIGH_RENEWABLE_SHARE", "count": 1},
                ],
                action=(
                    "Escalate the high-risk forecast window for human review "
                    "before any planning."
                ),
            ),
            _window(
                "48-72h",
                risk_level="low",
                row_count=1,
                max_risk_score=25,
                average_risk_score=25.0,
                top_reason_codes=[
                    {"reason_code": "NORMAL_PRICE", "count": 1},
                ],
                action="Continue routine human monitoring.",
            ),
        ]
    )


def _forecast(windows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "model_version": "rule-engine-v0+forecast-window-v0",
        "decision_support_only": True,
        "windows": windows,
    }


def _window(
    window_label: str,
    *,
    risk_level: str,
    row_count: int,
    max_risk_score: int,
    average_risk_score: float,
    top_reason_codes: list[dict[str, Any]],
    action: str,
) -> dict[str, Any]:
    return {
        "window_label": window_label,
        "risk_level": risk_level,
        "row_count": row_count,
        "max_risk_score": max_risk_score,
        "average_risk_score": average_risk_score,
        "top_reason_codes": top_reason_codes,
        "recommended_human_action": action,
        "decision_support_only": True,
    }
