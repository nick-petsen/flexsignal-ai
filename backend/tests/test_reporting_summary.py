from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.reporting import build_report_summary


GENERATED_AT = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


def _current_risk(action: str = "Human review required.") -> dict[str, object]:
    return {
        "risk_level": "medium",
        "risk_score": 45,
        "confidence_score": 0.9,
        "reason_codes": ["LOW_PRICE", "MODERATE_RENEWABLE_SHARE"],
        "recommended_human_action": action,
        "model_version": "rule-engine-v0",
        "decision_support_only": True,
    }


def _window(
    label: str,
    *,
    risk_level: str = "low",
    row_count: int = 2,
    action: str = "Continue routine human monitoring.",
) -> dict[str, object]:
    return {
        "window_label": label,
        "risk_level": risk_level,
        "row_count": row_count,
        "max_risk_score": None if risk_level == "unknown" else 30,
        "average_risk_score": None if risk_level == "unknown" else 20.0,
        "top_reason_codes": [{"reason_code": "NORMAL_PRICE", "count": 2}],
        "recommended_human_action": action,
        "decision_support_only": True,
    }


def _forecast(windows: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "model_version": "rule-engine-v0+forecast-window-v0",
        "decision_support_only": True,
        "windows": windows
        if windows is not None
        else [
            _window("0-24h"),
            _window("24-48h"),
            _window("48-72h"),
        ],
    }


def test_valid_full_report_returns_expected_fields() -> None:
    report = build_report_summary(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        current_risk=_current_risk(),
        forecast=_forecast(),
        title="Daily read-only summary",
        source_notes=["synthetic local preview"],
    )

    assert report["report_id"].startswith("report-summary-v0-DK1-")
    assert report["title"] == "Daily read-only summary"
    assert report["price_area"] == "DK1"
    assert report["generated_at_utc"] == GENERATED_AT
    assert report["report_version"] == "report-summary-v0"
    assert report["decision_support_only"] is True
    assert report["human_review_required"] is True
    assert report["current_risk_summary"]["risk_score"] == 45
    assert report["forecast_window_summary"]["windows"][0]["window_label"] == "0-24h"
    assert report["model_versions"] == {
        "report": "report-summary-v0",
        "current_risk": "rule-engine-v0",
        "forecast_window": "rule-engine-v0+forecast-window-v0",
    }
    assert report["source_notes"] == ["synthetic local preview"]


def test_report_id_is_deterministic() -> None:
    first = build_report_summary(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        current_risk=_current_risk(),
        forecast=_forecast(),
    )
    second = build_report_summary(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        current_risk=_current_risk(),
        forecast=_forecast(),
    )

    assert first["report_id"] == second["report_id"]


def test_invalid_price_area_rejected() -> None:
    with pytest.raises(ValueError, match="price_area must be DK1 or DK2"):
        build_report_summary(
            price_area="SE3",
            generated_at_utc=GENERATED_AT,
            current_risk=_current_risk(),
            forecast=_forecast(),
        )


def test_timezone_naive_generated_at_rejected() -> None:
    with pytest.raises(ValueError, match="generated_at_utc must be timezone-aware"):
        build_report_summary(
            price_area="DK1",
            generated_at_utc=datetime(2026, 1, 1, 0, 0),
            current_risk=_current_risk(),
            forecast=_forecast(),
        )


def test_missing_current_risk_creates_unavailable_summary_and_limitation() -> None:
    report = build_report_summary(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        current_risk=None,
        forecast=_forecast(),
    )

    assert report["current_risk_summary"]["status"] == "unavailable"
    assert report["current_risk_summary"]["decision_support_only"] is True
    assert "missing or incomplete current risk input" in report["limitations"]


def test_missing_forecast_creates_unavailable_summary_and_limitation() -> None:
    report = build_report_summary(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        current_risk=_current_risk(),
        forecast=None,
    )

    assert report["forecast_window_summary"]["status"] == "unavailable"
    assert report["forecast_window_summary"]["decision_support_only"] is True
    assert "missing or incomplete forecast input" in report["limitations"]


def test_high_forecast_window_appears_in_key_findings() -> None:
    report = build_report_summary(
        price_area="DK2",
        generated_at_utc=GENERATED_AT,
        current_risk=_current_risk(),
        forecast=_forecast([_window("0-24h"), _window("24-48h", risk_level="high")]),
    )

    assert "Forecast window 24-48h is high risk." in report["key_findings"]
    assert "No forecast window is high risk." not in report["key_findings"]


def test_unknown_forecast_window_appears_in_key_findings() -> None:
    report = build_report_summary(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        current_risk=_current_risk(),
        forecast=_forecast([_window("48-72h", risk_level="unknown", row_count=0)]),
    )

    assert (
        "Forecast window 48-72h is unknown due to no caller-provided rows."
        in report["key_findings"]
    )


def test_recommended_human_actions_are_deduplicated() -> None:
    repeated_action = "Human review required before planning."
    report = build_report_summary(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        current_risk=_current_risk(action=repeated_action),
        forecast=_forecast(
            [
                _window("0-24h", action=repeated_action),
                _window("24-48h", action=repeated_action),
            ]
        ),
    )

    assert report["recommended_human_actions"].count(repeated_action) == 1
    assert (
        "human review required before operational planning"
        in report["recommended_human_actions"]
    )
    assert (
        "verify source data and operational context"
        in report["recommended_human_actions"]
    )
    assert (
        "do not use for automatic control, dispatch, or activation"
        in report["recommended_human_actions"]
    )


def test_decision_support_only_true_appears_at_report_level_and_summaries() -> None:
    report = build_report_summary(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        current_risk=_current_risk(),
        forecast=_forecast(),
    )

    assert report["decision_support_only"] is True
    assert report["current_risk_summary"]["decision_support_only"] is True
    assert report["forecast_window_summary"]["decision_support_only"] is True
    assert all(
        window["decision_support_only"] is True
        for window in report["forecast_window_summary"]["windows"]
    )


def test_safety_notes_include_no_control_dispatch_activation() -> None:
    report = build_report_summary(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        current_risk=_current_risk(),
        forecast=_forecast(),
    )

    assert "must not be used for automatic control" in report["safety_notes"]
    assert "must not be used for dispatch" in report["safety_notes"]
    assert "must not be used for activation" in report["safety_notes"]


def test_object_inputs_are_supported() -> None:
    @dataclass(frozen=True)
    class CurrentRisk:
        risk_level: str
        risk_score: int
        confidence_score: float
        reason_codes: list[str]
        recommended_human_action: str
        model_version: str

    @dataclass(frozen=True)
    class Window:
        window_label: str
        risk_level: str
        row_count: int
        max_risk_score: int
        average_risk_score: float
        top_reason_codes: list[dict[str, object]]
        recommended_human_action: str

    @dataclass(frozen=True)
    class Forecast:
        model_version: str
        windows: list[Window]

    report = build_report_summary(
        price_area="DK2",
        generated_at_utc=GENERATED_AT,
        current_risk=CurrentRisk(
            risk_level="low",
            risk_score=20,
            confidence_score=1.0,
            reason_codes=["NORMAL_PRICE"],
            recommended_human_action="Continue routine human monitoring.",
            model_version="rule-engine-v0",
        ),
        forecast=Forecast(
            model_version="rule-engine-v0+forecast-window-v0",
            windows=[
                Window(
                    window_label="0-24h",
                    risk_level="low",
                    row_count=1,
                    max_risk_score=20,
                    average_risk_score=20.0,
                    top_reason_codes=[],
                    recommended_human_action="Continue routine human monitoring.",
                )
            ],
        ),
    )

    assert report["current_risk_summary"]["risk_level"] == "low"
    assert report["forecast_window_summary"]["windows"][0]["row_count"] == 1


def test_module_has_no_db_api_network_pdf_or_rendering_behavior() -> None:
    module_source = Path("app/reporting/summary.py").read_text()

    forbidden_terms = [
        "FastAPI",
        "APIRouter",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "DATABASE_URL",
        "app.db",
        "app.api",
        "reportlab",
        "weasyprint",
        "fpdf",
        "pdfkit",
        "jinja",
    ]
    for term in forbidden_terms:
        assert term not in module_source
