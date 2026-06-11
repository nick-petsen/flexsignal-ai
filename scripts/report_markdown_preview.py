#!/usr/bin/env python3
"""Manual synthetic local Markdown preview for report-summary-v0."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.reporting.markdown import render_report_summary_markdown  # noqa: E402
from app.reporting.summary import build_report_summary  # noqa: E402


GENERATED_AT_UTC = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
SCENARIOS = (
    "standard",
    "high-risk",
    "missing-current-risk",
    "missing-forecast",
)
SOURCE_NOTES = (
    "synthetic local Markdown preview only",
    "caller-provided sample current-risk and forecast-window data only",
    "does not fetch external data, use persistence, start servers, run browser UI, or write files",
    "does not use model training, language-model reasoning, document export, jobs, cloud resources, secrets, or auth",
    "must not be used for automatic control, dispatch, or activation",
    "human review required before planning",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a manual synthetic local Markdown preview of report-summary-v0 "
            "using sample current-risk and forecast-window data."
        )
    )
    parser.add_argument(
        "--price-area",
        choices=("DK1", "DK2"),
        default="DK1",
        help="Danish price area to include in the preview. Default: DK1.",
    )
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS,
        default="standard",
        help="Synthetic local report scenario to preview. Default: standard.",
    )
    return parser


def build_inputs(scenario: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if scenario == "standard":
        return _medium_current_risk(), _standard_forecast()
    if scenario == "high-risk":
        return _high_current_risk(), _high_risk_forecast()
    if scenario == "missing-current-risk":
        return {"risk_level": "medium"}, _standard_forecast()
    if scenario == "missing-forecast":
        return _medium_current_risk(), {"model_version": "rule-engine-v0+forecast-window-v0"}
    raise ValueError(f"Unsupported scenario: {scenario}")


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


def print_scope_warning() -> None:
    print(
        "WARNING: synthetic local Markdown preview only. Uses sample "
        "current-risk and forecast-window data; does not require DATABASE_URL; "
        "does not fetch external data, use persistence, start servers, run "
        "browser UI, write files, use model training, use language-model "
        "reasoning, perform document export, schedule jobs, use cloud "
        "resources, add secrets, add auth, control assets, dispatch, activate, "
        "or perform operational functionality. Human review is required before "
        "planning.",
        file=sys.stderr,
    )


def main() -> int:
    args = build_parser().parse_args()
    print_scope_warning()

    current_risk, forecast = build_inputs(args.scenario)
    report = build_report_summary(
        price_area=args.price_area,
        generated_at_utc=GENERATED_AT_UTC,
        current_risk=current_risk,
        forecast=forecast,
        source_notes=SOURCE_NOTES,
    )
    print(render_report_summary_markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
