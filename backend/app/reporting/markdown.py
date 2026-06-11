from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

UNAVAILABLE = "Unavailable"
NOT_PROVIDED = "Not provided"

MANDATORY_SAFETY_NOTES = [
    "read-only decision support only",
    "human review required",
    "must not be used for automatic control",
    "must not be used for dispatch",
    "must not be used for activation",
    "no autonomous decisions",
]


def render_report_summary_markdown(report: Mapping[str, Any]) -> str:
    """Render a caller-provided report-summary-v0 mapping as Markdown."""
    lines: list[str] = []

    lines.append(
        f"# {_plain_text(report.get('title'), fallback='FlexSignal AI report summary')}"
    )
    lines.append("")

    _append_mapping_table(
        lines,
        "Report metadata",
        (
            ("report_id", report.get("report_id")),
            ("report_version", report.get("report_version")),
            ("price_area", report.get("price_area")),
            ("generated_at_utc", report.get("generated_at_utc")),
            ("decision_support_only", report.get("decision_support_only")),
            ("human_review_required", report.get("human_review_required")),
        ),
    )

    _append_current_risk_summary(lines, report.get("current_risk_summary"))
    _append_forecast_window_summary(lines, report.get("forecast_window_summary"))
    _append_list_section(lines, "Key findings", report.get("key_findings"))
    _append_list_section(
        lines,
        "Recommended human actions",
        report.get("recommended_human_actions"),
    )
    _append_list_section(
        lines,
        "Safety notes",
        _safety_notes(report.get("safety_notes")),
    )
    _append_list_section(lines, "Limitations", report.get("limitations"))
    _append_list_section(lines, "Source notes", report.get("source_notes"))

    return "\n".join(lines).rstrip() + "\n"


def _append_current_risk_summary(lines: list[str], value: Any) -> None:
    lines.append("## Current risk summary")
    lines.append("")

    if not isinstance(value, Mapping) or value.get("status") != "available":
        lines.append(f"**Status:** {UNAVAILABLE}")
        lines.append("")
        lines.append(
            "Current risk summary is unavailable because caller-provided input is missing or incomplete."
        )
        lines.append("")
        return

    _append_table(
        lines,
        (
            ("status", value.get("status")),
            ("risk_level", value.get("risk_level")),
            ("risk_score", value.get("risk_score")),
            ("confidence_score", value.get("confidence_score")),
            ("reason_codes", value.get("reason_codes")),
            ("recommended_human_action", value.get("recommended_human_action")),
            ("model_version", value.get("model_version")),
        ),
    )


def _append_forecast_window_summary(lines: list[str], value: Any) -> None:
    lines.append("## Forecast window summary")
    lines.append("")

    if not isinstance(value, Mapping) or value.get("status") != "available":
        lines.append(f"**Status:** {UNAVAILABLE}")
        lines.append("")
        lines.append(
            "Forecast window summary is unavailable because caller-provided input is missing or incomplete."
        )
        lines.append("")
        return

    _append_table(
        lines,
        (
            ("status", value.get("status")),
            ("model_version", value.get("model_version")),
            ("decision_support_only", value.get("decision_support_only")),
        ),
    )

    windows = value.get("windows")
    if not isinstance(windows, Sequence) or isinstance(windows, (str, bytes)):
        lines.append("No forecast windows provided.")
        lines.append("")
        return

    for index, window in enumerate(windows, start=1):
        lines.append(f"### Forecast window {index}: {_window_label(window)}")
        lines.append("")
        if not isinstance(window, Mapping):
            lines.append(NOT_PROVIDED)
            lines.append("")
            continue
        _append_table(
            lines,
            (
                ("window_label", window.get("window_label")),
                ("risk_level", window.get("risk_level")),
                ("row_count", window.get("row_count")),
                ("max_risk_score", window.get("max_risk_score")),
                ("average_risk_score", window.get("average_risk_score")),
                ("top_reason_codes", window.get("top_reason_codes")),
                (
                    "recommended_human_action",
                    window.get("recommended_human_action"),
                ),
            ),
        )


def _append_mapping_table(
    lines: list[str],
    heading: str,
    rows: Sequence[tuple[str, Any]],
) -> None:
    lines.append(f"## {heading}")
    lines.append("")
    _append_table(lines, rows)


def _append_table(lines: list[str], rows: Sequence[tuple[str, Any]]) -> None:
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    for key, value in rows:
        lines.append(f"| {_plain_text(key)} | {_plain_text(value)} |")
    lines.append("")


def _append_list_section(lines: list[str], heading: str, values: Any) -> None:
    lines.append(f"## {heading}")
    lines.append("")

    items = _as_sequence(values)
    if not items:
        lines.append(f"- {NOT_PROVIDED}")
    else:
        for item in items:
            lines.append(f"- {_plain_text(item)}")
    lines.append("")


def _safety_notes(values: Any) -> list[Any]:
    notes = list(_as_sequence(values))
    for note in MANDATORY_SAFETY_NOTES:
        if note not in notes:
            notes.append(note)
    return notes


def _as_sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return list(value)
    return [value]


def _window_label(value: Any) -> str:
    if not isinstance(value, Mapping):
        return NOT_PROVIDED
    return _plain_text(value.get("window_label"))


def _plain_text(value: Any, *, fallback: str = NOT_PROVIDED) -> str:
    if value is None:
        return fallback
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        utc_value = value.astimezone(timezone.utc) if value.tzinfo else value
        return utc_value.isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        if not value:
            return fallback
        return ", ".join(
            f"{_plain_text(key)}={_plain_text(value[key])}"
            for key in sorted(value, key=lambda item: str(item))
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if not value:
            return fallback
        return ", ".join(_plain_text(item) for item in value)
    return _escape_table_text(str(value)) or fallback


def _escape_table_text(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ").replace("|", "\\|")
