#!/usr/bin/env python3
"""Export a read-only customer pilot workflow preview PDF report."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
BACKEND_ROOT = REPO_ROOT / "backend"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from customer_pilot_report_export import (  # noqa: E402
    CustomerPilotIntakeValidationError,
    CustomerPilotOpportunityEstimateError,
    CustomerPilotSignalMatchError,
    CustomerPilotWorkflowPreviewConfig,
    CustomerPilotWorkflowPreviewError,
    CustomerPilotWorkflowPreviewSummary,
    _cell,
    _format_decimal_cell,
    _format_int,
    _format_int_cell,
    load_workflow_config,
    run_customer_pilot_workflow_preview,
)


DEFAULT_PDF_WRITE = "false"
DEFAULT_PDF_OUTPUT_PATH = ""
PDF_TITLE = "N&O Predict"
PDF_FOOTER = "N&O Predict · Read-only decision support · Human review required"
REPORT_PDF_SAFETY_BOUNDARY = (
    "Read-only PDF report export only.",
    "No customer-specific financial value calculated.",
    "No commercial outcome calculated.",
    "No automatic control, dispatch, or activation.",
    "No live control signals.",
    "No asset integration.",
    "No database writes.",
    "No external API calls.",
    "Human review required.",
)


class CustomerPilotPdfExportError(RuntimeError):
    """Expected safe-fail error for customer pilot PDF export."""


@dataclass(frozen=True)
class CustomerPilotPdfExportConfig:
    workflow_config: CustomerPilotWorkflowPreviewConfig
    output_path: str
    pdf_write: bool


def load_config(env: Mapping[str, str] | None = None) -> CustomerPilotPdfExportConfig:
    safe_env = os.environ if env is None else env
    workflow_config = load_workflow_config(safe_env)
    output_path = safe_env.get(
        "CUSTOMER_PILOT_PDF_OUTPUT_PATH",
        DEFAULT_PDF_OUTPUT_PATH,
    ).strip()
    pdf_write = _parse_bool(
        safe_env.get("CUSTOMER_PILOT_PDF_WRITE", DEFAULT_PDF_WRITE),
        "CUSTOMER_PILOT_PDF_WRITE",
    )

    return CustomerPilotPdfExportConfig(
        workflow_config=workflow_config,
        output_path=output_path,
        pdf_write=pdf_write,
    )


def render_pdf_report_text(summary: CustomerPilotWorkflowPreviewSummary) -> str:
    total_matched_flexible_energy = _format_decimal_cell(
        summary.total_matched_flexible_energy_mwh,
        "MWh",
    )
    total_indicative_signal = _format_decimal_cell(
        summary.total_indicative_gross_opportunity_signal_eur,
        "EUR",
    )
    workflow_status = _human_status(summary.workflow_status)
    validation_status = _human_status(summary.validation_status)
    signal_match_status = _human_status(summary.signal_match_status)
    estimate_status = _human_status(summary.opportunity_estimate_status)
    lines: list[str] = [
        f"# {PDF_TITLE}",
        "",
        "Customer Pilot Preview Report",
        "Read-only decision support · Human review required",
        "",
        "## Executive summary",
        "",
        f"Customer data validation result: {validation_status}.",
        f"Matched public risk windows: {_format_int(summary.matched_window_count)}.",
        f"Matched flexible energy: {total_matched_flexible_energy}.",
        f"Indicative gross opportunity signal: {total_indicative_signal}.",
        "This is not a customer value claim.",
        "",
        "## At-a-glance",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Overall status | {workflow_status} |",
        f"| Matched windows | {_format_int(summary.matched_window_count)} |",
        f"| Matched customer rows | {_format_int(summary.matched_customer_rows)} |",
        f"| Matched flexible energy | {total_matched_flexible_energy} |",
        (
            "| Indicative gross opportunity signal | "
            f"{total_indicative_signal} |"
        ),
        f"| Validation | {validation_status} |",
        f"| Signal match | {signal_match_status} |",
        f"| Opportunity estimate | {estimate_status} |",
        "",
    ]

    if summary.top_candidate_windows:
        for window in summary.top_candidate_windows:
            public_window = _format_public_window(
                window.get("public_window_start"),
                window.get("public_window_end"),
            )
            lines.extend(
                [
                    "## Candidate window",
                    "",
                    "| Field | Value |",
                    "| --- | --- |",
                    f"| Price area | {_cell(window.get('price_area'))} |",
                    f"| Public window | {public_window} |",
                    (
                        "| Risk score | "
                        f"{_format_int_cell(window.get('public_risk_score'))} |"
                    ),
                    (
                        "| Risk level | "
                        f"{_human_status(window.get('public_risk_level'))} |"
                    ),
                    (
                        "| Public opportunity signal | "
                        f"{_format_decimal_cell(window.get('public_opportunity_signal_eur_per_mwh'), 'EUR/MWh')} |"
                    ),
                    (
                        "| Matched flexible energy | "
                        f"{_format_decimal_cell(window.get('matched_flexible_energy_mwh'), 'MWh')} |"
                    ),
                    (
                        "| Indicative gross opportunity signal | "
                        f"{_format_decimal_cell(window.get('indicative_gross_opportunity_signal_eur'), 'EUR')} |"
                    ),
                    "",
                ]
            )
    else:
        lines.extend(["## Candidate window", ""])
        lines.append("No candidate windows are available for this preview.")

    lines.extend(
        [
            "",
            "## What we found",
            "",
            (
                "The public DK1/DK2 signal and the customer pilot data overlap "
                "in the matched window. This points to a candidate period for "
                "human review, not an automated action or verified customer "
                "value."
            ),
        ]
    )

    if summary.warnings:
        lines.extend(
            [
                "",
                "## Review notes",
                "",
                *_bullet_lines(summary.warnings),
            ]
        )

    if summary.errors:
        lines.extend(
            [
                "",
                "## Workflow errors",
                "",
                *_bullet_lines(summary.errors),
            ]
        )

    lines.extend(
        [
            "",
            "## Recommended human review steps",
            "",
            "Review the matched window with the customer operational owner.",
            "Confirm actual operational availability and constraints.",
            "Validate tariff, contract, operating cost, and site-specific context.",
            "Decide whether a customer-specific assessment is justified.",
            "",
            "## Method",
            "",
            (
                "matched flexible energy MWh x public opportunity signal EUR/MWh = "
                "indicative gross opportunity signal"
            ),
            "",
            "## Limitations",
            "",
            "Public price signal only.",
            "No tariff validation.",
            "No operating cost validation.",
            "No customer operational approval yet.",
            "Not financial advice.",
            "No production readiness claim.",
            "",
            "## Safety boundary",
            "",
            *_bullet_lines(REPORT_PDF_SAFETY_BOUNDARY),
            "",
            PDF_FOOTER,
            "",
        ]
    )
    return "\n".join(lines)


def render_pdf_bytes(summary: CustomerPilotWorkflowPreviewSummary) -> bytes:
    render_report_markdown_pdf_bytes = _load_pdf_renderer()
    return render_report_markdown_pdf_bytes(
        render_pdf_report_text(summary),
        title=PDF_TITLE,
    )


def export_pdf(
    config: CustomerPilotPdfExportConfig,
    *,
    stdout: object | None = None,
) -> dict[str, object]:
    summary = run_customer_pilot_workflow_preview(config.workflow_config)
    output_stream = sys.stdout if stdout is None else stdout

    file_written = False
    if config.output_path and config.pdf_write:
        output_path = Path(config.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(render_pdf_bytes(summary))
        file_written = True
    else:
        _print_no_write_summary(summary, config=config, stdout=output_stream)

    return {
        "workflow_status": summary.workflow_status,
        "output_path": config.output_path if file_written else "",
        "pdf_write": config.pdf_write,
        "file_written": file_written,
        "database_write_performed": False,
        "external_api_calls_performed": False,
    }


def main() -> int:
    try:
        config = load_config()
        result = export_pdf(config)
    except (
        CustomerPilotPdfExportError,
        CustomerPilotWorkflowPreviewError,
        CustomerPilotIntakeValidationError,
        CustomerPilotSignalMatchError,
        CustomerPilotOpportunityEstimateError,
    ) as exc:
        summary = _invalid_summary(str(exc))
        print(render_pdf_report_text(summary))
        return 1
    except OSError as exc:
        summary = _invalid_summary(f"PDF export failed: {exc.__class__.__name__}.")
        print(render_pdf_report_text(summary))
        return 1

    if result["file_written"]:
        print("Customer pilot PDF report written.")
    if result["workflow_status"] == "invalid":
        return 1
    return 0


def _print_no_write_summary(
    summary: CustomerPilotWorkflowPreviewSummary,
    *,
    config: CustomerPilotPdfExportConfig,
    stdout: object,
) -> None:
    reason = (
        "No PDF output path was provided."
        if not config.output_path
        else "PDF write mode is disabled."
    )
    print("Customer pilot PDF report preview summary", file=stdout)
    print(f"No PDF was written. {reason}", file=stdout)
    print(
        "Set CUSTOMER_PILOT_PDF_WRITE=true and CUSTOMER_PILOT_PDF_OUTPUT_PATH "
        "to write one local PDF file.",
        file=stdout,
    )
    print(f"Workflow status: {summary.workflow_status}", file=stdout)
    print(f"Validation status: {summary.validation_status}", file=stdout)
    print(f"Signal match status: {summary.signal_match_status}", file=stdout)
    print(
        f"Opportunity estimate status: {summary.opportunity_estimate_status}",
        file=stdout,
    )
    print("Safety boundary: read-only PDF report export only.", file=stdout)


def _invalid_summary(error: str) -> CustomerPilotWorkflowPreviewSummary:
    return CustomerPilotWorkflowPreviewSummary(
        workflow_status="invalid",
        validation_status="not_run",
        signal_match_status="not_run",
        opportunity_estimate_status="not_run",
        total_customer_rows=0,
        matched_window_count=0,
        matched_customer_rows=0,
        total_matched_flexible_energy_mwh=0.0,
        total_indicative_gross_opportunity_signal_eur=0.0,
        top_candidate_windows=(),
        warnings=(),
        next_human_review_steps=(
            "Review configuration and input format before rerunning.",
            "Keep customer data and pilot CSV files out of git.",
            "Use human review before any customer-specific assessment.",
        ),
        safety_boundary=REPORT_PDF_SAFETY_BOUNDARY,
        errors=(error,),
        dry_run=True,
    )


def _bullet_lines(values: Sequence[str]) -> list[str]:
    if not values:
        return ["- None."]
    return [f"- {value}" for value in values]


def _parse_bool(raw_value: str | None, env_name: str) -> bool:
    normalized = (raw_value or "").strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise CustomerPilotPdfExportError(f"{env_name} must be true or false")


def _human_status(value: Any) -> str:
    raw_value = _cell(value)
    if raw_value == "not_available":
        return "Not available"
    return raw_value.replace("_", " ").capitalize()


def _format_public_window(start: Any, end: Any) -> str:
    return f"{_format_timestamp(start)} to {_format_timestamp(end)}"


def _format_timestamp(value: Any) -> str:
    if value is None or value == "":
        return "not_available"
    raw_value = str(value)
    normalized = raw_value.replace("Z", "+00:00")
    try:
        timestamp = datetime.fromisoformat(normalized)
    except ValueError:
        return raw_value
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    timestamp = timestamp.astimezone(timezone.utc)
    return timestamp.strftime("%Y-%m-%d %H:%M UTC")


def _load_pdf_renderer():
    try:
        from app.reporting.pdf import render_report_markdown_pdf_bytes
    except ModuleNotFoundError as exc:
        if exc.name == "reportlab":
            raise CustomerPilotPdfExportError(
                "PDF export requires the backend dependency 'reportlab'. "
                "Install backend dependencies from backend/pyproject.toml, "
                "for example: cd backend && python -m pip install -e '.[dev]'. "
                "Then rerun the PDF export command from the repository root "
                "using the same Python environment."
            ) from exc
        raise
    return render_report_markdown_pdf_bytes


if __name__ == "__main__":
    raise SystemExit(main())
