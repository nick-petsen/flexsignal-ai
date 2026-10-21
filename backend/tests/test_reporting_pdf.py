from __future__ import annotations

import builtins
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.reporting import (
    build_report_summary,
    render_report_markdown_pdf_bytes,
    render_report_summary_markdown,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "report_pdf_preview.py"
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


def _forecast() -> dict[str, object]:
    return {
        "model_version": "rule-engine-v0+forecast-window-v0",
        "decision_support_only": True,
        "windows": [
            {
                "window_label": "0-24h",
                "risk_level": "medium",
                "row_count": 2,
                "max_risk_score": 45,
                "average_risk_score": 42.5,
                "top_reason_codes": [{"reason_code": "LOW_PRICE", "count": 1}],
                "recommended_human_action": "Review before planning.",
                "decision_support_only": True,
            }
        ],
    }


def _markdown() -> str:
    report = build_report_summary(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        current_risk=_current_risk(),
        forecast=_forecast(),
        source_notes=["synthetic local preview only"],
    )
    return render_report_summary_markdown(report)


def _run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def test_pdf_renderer_returns_non_empty_pdf_bytes() -> None:
    data = render_report_markdown_pdf_bytes(_markdown())

    assert data.startswith(b"%PDF")
    assert len(data) > 1000


def test_pdf_export_inherits_calibration_disclaimer_without_raw_score() -> None:
    data = render_report_markdown_pdf_bytes(_markdown())

    assert b"risk_score: 45" in data
    assert b"confidence_score:" not in data
    assert b"Forecast calibration: Not calibrated" in data
    assert b"fixed penalties for missing inputs" in data


def test_pdf_renderer_preserves_required_safety_wording_in_uncompressed_output() -> None:
    safety_wording = (
        "must not be used for automatic " + "control, dispatch, or activation"
    )

    data = render_report_markdown_pdf_bytes(
        "# Safety\n\n- read-only decision support only\n"
        "- human review required\n"
        f"- {safety_wording}\n"
    )

    assert b"read-only decision support only" in data
    assert safety_wording.encode("utf-8") in data


def test_pdf_renderer_does_not_write_files(monkeypatch) -> None:
    def fail_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("renderer attempted file access")

    def fail_path_method(*args: object, **kwargs: object) -> None:
        raise AssertionError("renderer attempted file output")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(Path, "write_text", fail_path_method)
    monkeypatch.setattr(Path, "write_bytes", fail_path_method)

    data = render_report_markdown_pdf_bytes(_markdown())

    assert data.startswith(b"%PDF")


def test_script_refuses_to_run_without_output() -> None:
    result = _run_script()

    assert result.returncode != 0
    assert "--output" in result.stderr


def test_script_writes_one_pdf_to_explicit_output_path(tmp_path: Path) -> None:
    output_path = tmp_path / "report.pdf"

    result = _run_script("--output", str(output_path))

    assert result.returncode == 0, result.stderr
    data = output_path.read_bytes()
    summary = json.loads(result.stdout)
    assert data.startswith(b"%PDF")
    assert summary["output_path"] == str(output_path)
    assert summary["bytes_written"] == len(data)
    assert summary["price_area"] == "DK1"
    assert summary["scenario"] == "standard"
    assert summary["report_version"] == "report-summary-v0"
    assert summary["decision_support_only"] is True
    assert summary["synthetic_preview_only"] is True
    assert sorted(path.name for path in tmp_path.iterdir()) == ["report.pdf"]


def test_script_refuses_overwrite_without_force(tmp_path: Path) -> None:
    output_path = tmp_path / "report.pdf"
    output_path.write_bytes(b"existing")

    result = _run_script("--output", str(output_path))

    assert result.returncode != 0
    assert output_path.read_bytes() == b"existing"
    assert "Refusing to overwrite" in result.stderr


def test_script_can_overwrite_with_force(tmp_path: Path) -> None:
    output_path = tmp_path / "report.pdf"
    output_path.write_bytes(b"existing")

    result = _run_script("--output", str(output_path), "--force")

    assert result.returncode == 0, result.stderr
    assert output_path.read_bytes().startswith(b"%PDF")


def test_script_standard_scenario_works(tmp_path: Path) -> None:
    output_path = tmp_path / "standard.pdf"

    result = _run_script("--scenario", "standard", "--output", str(output_path))

    assert result.returncode == 0, result.stderr
    assert output_path.read_bytes().startswith(b"%PDF")


def test_script_high_risk_scenario_works(tmp_path: Path) -> None:
    output_path = tmp_path / "high-risk.pdf"

    result = _run_script(
        "--price-area",
        "DK2",
        "--scenario",
        "high-risk",
        "--output",
        str(output_path),
    )

    assert result.returncode == 0, result.stderr
    assert output_path.read_bytes().startswith(b"%PDF")


def test_script_missing_current_risk_scenario_works(tmp_path: Path) -> None:
    output_path = tmp_path / "missing-current.pdf"

    result = _run_script(
        "--scenario",
        "missing-current-risk",
        "--output",
        str(output_path),
    )

    assert result.returncode == 0, result.stderr
    assert output_path.read_bytes().startswith(b"%PDF")


def test_script_missing_forecast_scenario_works(tmp_path: Path) -> None:
    output_path = tmp_path / "missing-forecast.pdf"

    result = _run_script(
        "--scenario",
        "missing-forecast",
        "--output",
        str(output_path),
    )

    assert result.returncode == 0, result.stderr
    assert output_path.read_bytes().startswith(b"%PDF")


def test_pdf_renderer_and_script_have_no_external_runtime_imports_or_actions() -> None:
    module_source = Path("app/reporting/pdf.py").read_text()
    script_source = (REPO_ROOT / "scripts" / "report_pdf_preview.py").read_text()
    combined_source = module_source + "\n" + script_source
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
        "sched" + "uler",
        "Az" + "ure",
    ]

    for term in forbidden_terms:
        assert term not in combined_source
