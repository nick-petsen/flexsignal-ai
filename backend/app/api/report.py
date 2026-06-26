from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.reporting.markdown import render_report_summary_markdown
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

MARKDOWN_EXCERPT_CHARACTER_LIMIT = 800


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


class ReportSummaryPreviewResponse(BaseModel):
    report_preview_generated: bool
    pdf_generated: bool
    file_written: bool
    database_query_executed: bool
    database_write_performed: bool
    requires_database_url: bool
    decision_support_only: bool
    report_summary: dict[str, Any]
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
    report_summary: dict[str, Any]
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
    report_summary: dict[str, Any]
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
