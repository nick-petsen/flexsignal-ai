#!/usr/bin/env python3
"""Export a read-only customer pilot workflow preview report."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from customer_pilot_workflow_preview import (  # noqa: E402
    CustomerPilotIntakeValidationError,
    CustomerPilotOpportunityEstimateError,
    CustomerPilotSignalMatchError,
    CustomerPilotWorkflowPreviewConfig,
    CustomerPilotWorkflowPreviewError,
    CustomerPilotWorkflowPreviewSummary,
    load_config as load_workflow_config,
    run_customer_pilot_workflow_preview,
)


DEFAULT_REPORT_WRITE = "false"
DEFAULT_REPORT_OUTPUT_PATH = ""
TITLE = "Customer pilot workflow preview report"
REPORT_SAFETY_BOUNDARY = (
    "read-only report export only",
    "no customer-specific savings calculated",
    "no profit/revenue calculated",
    "no automatic control",
    "no dispatch",
    "no activation",
    "no live control signals",
    "no asset integration",
    "no database writes",
    "no external API calls",
    "human review required",
    "customer data must not be committed to git",
)


class CustomerPilotReportExportError(RuntimeError):
    """Expected safe-fail error for customer pilot report export."""


@dataclass(frozen=True)
class CustomerPilotReportExportConfig:
    workflow_config: CustomerPilotWorkflowPreviewConfig
    output_path: str
    report_write: bool


def load_config(
    env: Mapping[str, str] | None = None,
) -> CustomerPilotReportExportConfig:
    safe_env = os.environ if env is None else env
    workflow_config = load_workflow_config(safe_env)
    output_path = safe_env.get(
        "CUSTOMER_PILOT_REPORT_OUTPUT_PATH",
        DEFAULT_REPORT_OUTPUT_PATH,
    ).strip()
    report_write = _parse_bool(
        safe_env.get("CUSTOMER_PILOT_REPORT_WRITE", DEFAULT_REPORT_WRITE),
        "CUSTOMER_PILOT_REPORT_WRITE",
    )

    return CustomerPilotReportExportConfig(
        workflow_config=workflow_config,
        output_path=output_path,
        report_write=report_write,
    )


def render_markdown_report(summary: CustomerPilotWorkflowPreviewSummary) -> str:
    lines: list[str] = [
        f"# {TITLE}",
        "",
        "## Scope note",
        "",
        "- read-only pilot preview.",
        "- public price signal only.",
        "- human review required.",
        "- This is not a customer value claim.",
        (
            "- Customer-specific assessment requires tariff, constraints, "
            "operating costs, and human validation."
        ),
        "- Customer data must not be committed to git.",
        "",
        "## Input summary",
        "",
        f"- Total customer rows: {_format_int(summary.total_customer_rows)}",
        f"- Validation status: `{summary.validation_status}`",
        f"- Signal match status: `{summary.signal_match_status}`",
        f"- Opportunity estimate status: `{summary.opportunity_estimate_status}`",
        "",
        "## Candidate window summary",
        "",
    ]

    if summary.top_candidate_windows:
        lines.extend(
            [
                (
                    "| Price area | Public window start | Public window end | "
                    "Public risk score | Public risk level | Matched customer "
                    "rows | Matched flexible energy MWh | Public opportunity "
                    "signal EUR/MWh | Indicative gross opportunity signal EUR |"
                ),
                (
                    "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |"
                ),
            ]
        )
        for window in summary.top_candidate_windows:
            lines.append(
                "| "
                f"{_cell(window.get('price_area'))} | "
                f"{_cell(window.get('public_window_start'))} | "
                f"{_cell(window.get('public_window_end'))} | "
                f"{_cell(window.get('public_risk_score'))} | "
                f"{_cell(window.get('public_risk_level'))} | "
                f"{_cell(window.get('customer_rows_in_window'))} | "
                f"{_cell(window.get('matched_flexible_energy_mwh'))} | "
                f"{_cell(window.get('public_opportunity_signal_eur_per_mwh'))} | "
                f"{_cell(window.get('indicative_gross_opportunity_signal_eur'))} |"
            )
    else:
        lines.append("No candidate windows are available for this preview.")

    lines.extend(
        [
            "",
            "## Warnings",
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
            "## Next human review steps",
            "",
            *_bullet_lines(summary.next_human_review_steps),
            "",
            "## Safety boundary",
            "",
            *_bullet_lines(REPORT_SAFETY_BOUNDARY),
            "",
            "## Method",
            "",
            (
                "matched flexible MWh x public opportunity signal EUR/MWh = "
                "indicative gross opportunity signal"
            ),
            "",
            "## Limitations",
            "",
            "- No tariff validation.",
            "- No operating cost validation.",
            "- No customer operational approval yet.",
            "- No production readiness claim.",
            "",
        ]
    )
    return "\n".join(lines)


def export_report(
    config: CustomerPilotReportExportConfig,
    *,
    stdout: object | None = None,
) -> dict[str, object]:
    summary = run_customer_pilot_workflow_preview(config.workflow_config)
    report = render_markdown_report(summary)
    output_stream = sys.stdout if stdout is None else stdout

    file_written = False
    if config.output_path and config.report_write:
        output_path = Path(config.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        file_written = True
    else:
        print(report, file=output_stream)

    return {
        "workflow_status": summary.workflow_status,
        "output_path": config.output_path if file_written else "",
        "report_write": config.report_write,
        "file_written": file_written,
        "database_write_performed": False,
        "external_api_calls_performed": False,
    }


def main() -> int:
    try:
        config = load_config()
        result = export_report(config)
    except (
        CustomerPilotReportExportError,
        CustomerPilotWorkflowPreviewError,
        CustomerPilotIntakeValidationError,
        CustomerPilotSignalMatchError,
        CustomerPilotOpportunityEstimateError,
    ) as exc:
        summary = _invalid_summary(str(exc))
        print(render_markdown_report(summary))
        return 1
    except OSError as exc:
        summary = _invalid_summary(f"Report export failed: {exc.__class__.__name__}.")
        print(render_markdown_report(summary))
        return 1

    if result["file_written"]:
        print("Customer pilot report written.")
    if result["workflow_status"] == "invalid":
        return 1
    return 0


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
        safety_boundary=REPORT_SAFETY_BOUNDARY,
        errors=(error,),
        dry_run=True,
    )


def _bullet_lines(values: Sequence[str]) -> list[str]:
    if not values:
        return ["- None."]
    return [f"- {value}" for value in values]


def _cell(value: Any) -> str:
    if value is None or value == "":
        return "not_available"
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value).replace("|", "\\|")


def _format_int(value: int) -> str:
    return f"{value:,}"


def _parse_bool(raw_value: str | None, env_name: str) -> bool:
    normalized = (raw_value or "").strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise CustomerPilotReportExportError(f"{env_name} must be true or false")


if __name__ == "__main__":
    raise SystemExit(main())
