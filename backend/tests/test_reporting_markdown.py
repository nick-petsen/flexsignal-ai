from __future__ import annotations

import builtins
from datetime import datetime, timezone
from pathlib import Path

from app.reporting import build_report_summary, render_report_summary_markdown


GENERATED_AT = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)


def _current_risk() -> dict[str, object]:
    return {
        "risk_level": "medium",
        "risk_score": 45,
        "confidence_score": 0.9,
        "reason_codes": ["LOW_PRICE", "MODERATE_RENEWABLE_SHARE"],
        "recommended_human_action": "Human review required before planning.",
        "model_version": "rule-engine-v0",
        "decision_support_only": True,
    }


def _window(
    label: str,
    *,
    risk_level: str = "low",
    max_risk_score: int = 30,
    average_risk_score: float = 20.0,
) -> dict[str, object]:
    return {
        "window_label": label,
        "risk_level": risk_level,
        "row_count": 2,
        "max_risk_score": max_risk_score,
        "average_risk_score": average_risk_score,
        "top_reason_codes": [{"reason_code": "NORMAL_PRICE", "count": 2}],
        "recommended_human_action": "Continue routine human monitoring.",
        "decision_support_only": True,
    }


def _forecast() -> dict[str, object]:
    return {
        "model_version": "rule-engine-v0+forecast-window-v0",
        "decision_support_only": True,
        "windows": [
            _window("0-24h"),
            _window(
                "24-48h",
                risk_level="high",
                max_risk_score=80,
                average_risk_score=60.0,
            ),
            _window("48-72h"),
        ],
    }


def _report() -> dict[str, object]:
    return build_report_summary(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        current_risk=_current_risk(),
        forecast=_forecast(),
        title="Daily read-only summary",
        source_notes=["synthetic local preview"],
    )


def test_full_report_renders_title_and_metadata() -> None:
    markdown = render_report_summary_markdown(_report())

    assert markdown.startswith("# Daily read-only summary\n")
    assert "## Report metadata" in markdown
    assert "| report_id | report-summary-v0-DK1-" in markdown
    assert "| report_version | report-summary-v0 |" in markdown
    assert "| price_area | DK1 |" in markdown
    assert "| generated_at_utc | 2026-01-01T00:00:00Z |" in markdown
    assert "| decision_support_only | true |" in markdown
    assert "| human_review_required | true |" in markdown


def test_current_risk_summary_renders_core_fields() -> None:
    markdown = render_report_summary_markdown(_report())

    assert "## Current risk summary" in markdown
    assert "| risk_level | medium |" in markdown
    assert "| risk_score | 45 |" in markdown
    assert "| reason_codes | LOW_PRICE, MODERATE_RENEWABLE_SHARE |" in markdown
    assert "| recommended_human_action | Human review required before planning. |" in markdown


def test_report_does_not_present_internal_score_as_forecast_certainty() -> None:
    report = _report()
    assert report["current_risk_summary"]["confidence_score"] == 0.9
    assert report["current_risk_summary"]["risk_score"] == 45

    markdown = render_report_summary_markdown(report)

    assert "| risk_score | 45 |" in markdown
    assert "| confidence_score |" not in markdown
    assert "Forecast calibration: Not calibrated" in markdown
    assert (
        "The internal score uses fixed penalties for missing inputs and has "
        "not been statistically calibrated against outcomes."
    ) in markdown


def test_forecast_windows_render_all_three_window_labels() -> None:
    markdown = render_report_summary_markdown(_report())

    assert "### Forecast window 1: 0-24h" in markdown
    assert "### Forecast window 2: 24-48h" in markdown
    assert "### Forecast window 3: 48-72h" in markdown


def test_high_risk_window_appears_in_markdown() -> None:
    markdown = render_report_summary_markdown(_report())

    assert "### Forecast window 2: 24-48h" in markdown
    assert "| risk_level | high |" in markdown
    assert "| max_risk_score | 80 |" in markdown
    assert "Forecast window 24-48h is high risk." in markdown


def test_missing_current_risk_renders_unavailable_without_crashing() -> None:
    report = _report()
    report.pop("current_risk_summary")

    markdown = render_report_summary_markdown(report)

    assert "## Current risk summary" in markdown
    assert "**Status:** Unavailable" in markdown
    assert "Current risk summary is unavailable" in markdown


def test_missing_forecast_renders_unavailable_without_crashing() -> None:
    report = _report()
    report.pop("forecast_window_summary")

    markdown = render_report_summary_markdown(report)

    assert "## Forecast window summary" in markdown
    assert "**Status:** Unavailable" in markdown
    assert "Forecast window summary is unavailable" in markdown


def test_safety_notes_include_no_control_dispatch_activation() -> None:
    markdown = render_report_summary_markdown({"title": "Safety check"})

    assert "read-only decision support only" in markdown
    assert "human review required" in markdown
    assert "must not be used for automatic control" in markdown
    assert "must not be used for dispatch" in markdown
    assert "must not be used for activation" in markdown
    assert "no autonomous decisions" in markdown


def test_output_is_deterministic_for_same_input() -> None:
    report = _report()

    first = render_report_summary_markdown(report)
    second = render_report_summary_markdown(report)

    assert first == second


def test_renderer_does_not_write_files(monkeypatch) -> None:
    def fail_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("renderer attempted file access")

    def fail_path_method(*args: object, **kwargs: object) -> None:
        raise AssertionError("renderer attempted file output")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(Path, "write_text", fail_path_method)
    monkeypatch.setattr(Path, "write_bytes", fail_path_method)

    markdown = render_report_summary_markdown(_report())

    assert "# Daily read-only summary" in markdown


def test_renderer_module_has_no_external_runtime_imports_or_output_engines() -> None:
    module_source = Path("app/reporting/markdown.py").read_text()
    forbidden_terms = [
        "Fast" + "API",
        "API" + "Router",
        "psyc" + "opg",
        "sql" + "alchemy",
        "SE" + "LECT",
        "INS" + "ERT",
        "UP" + "DATE",
        "DEL" + "ETE",
        "reque" + "sts",
        "ht" + "tpx",
        "api.energi" + "dataservice",
        "D" + "MI",
        "P" + "DF",
        "report" + "lab",
        "weasy" + "print",
        "sched" + "uler",
        "Az" + "ure",
    ]

    for term in forbidden_terms:
        assert term not in module_source
