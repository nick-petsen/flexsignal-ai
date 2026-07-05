from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script_module(script_name: str) -> ModuleType:
    module_path = REPO_ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(
        script_name.removesuffix(".py"),
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


report_export = load_script_module("public_surplus_risk_report_export.py")


def test_default_config_is_markdown_dry_run_without_output_path() -> None:
    config = report_export.load_config({})

    assert config.report_format == "markdown"
    assert config.output_path == ""
    assert config.dry_run is True


def test_report_contains_dk1_dk2_metrics() -> None:
    report = report_export.render_markdown_report()

    assert "# Public DK1/DK2 surplus-risk proof-of-work" in report
    assert "2026-01-01 to now" in report
    assert "Energi Data Service DayAheadPrices" in report
    assert (
        "| DK1 | 4,208 | 233 | 1,663 | 174 | 129 | 100 | 132 | 479 | 68.8% |"
        in report
    )
    assert (
        "| DK2 | 4,208 | 233 | 288 | 2 | 72 | 85 | 78 | 491 | 38.2% |"
        in report
    )


def test_report_contains_top_risk_windows() -> None:
    report = report_export.render_markdown_report()

    assert "## Top risk windows" in report
    assert "2026-04-04T21:00:00" in report
    assert "2026-04-06T23:00:00" in report
    assert "2026-04-24T21:00:00" in report
    assert "renewable_generation_above_consumption" in report


def test_report_contains_no_customer_specific_savings_claim() -> None:
    report = report_export.render_markdown_report().lower()

    assert "not customer-specific savings" in report
    assert "customer-specific savings are" not in report
    assert "customer-specific savings of" not in report
    assert "customer savings calculation" not in report
    assert "savings estimate" not in report


def test_report_contains_safety_boundary() -> None:
    report = report_export.render_markdown_report()

    assert "## Safety boundary" in report
    assert "read-only decision support" in report
    assert "public market/system-level data only" in report
    assert "no automatic control, dispatch, activation" in report
    assert "customer load, asset, tariff, and operational data" in report


def test_dry_run_without_output_path_writes_no_files(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    config = report_export.ReportExportConfig(
        report_format="markdown",
        output_path="",
        dry_run=True,
    )

    result = report_export.export_report(config)
    output = capsys.readouterr().out

    assert "# Public DK1/DK2 surplus-risk proof-of-work" in output
    assert list(tmp_path.iterdir()) == []
    assert result["file_written"] is False
    assert result["database_write_performed"] is False


def test_output_path_writes_only_requested_report_file(tmp_path: Path) -> None:
    output_path = tmp_path / "artifacts" / "public-surplus-risk-report.md"
    config = report_export.ReportExportConfig(
        report_format="markdown",
        output_path=str(output_path),
        dry_run=True,
    )

    result = report_export.export_report(config)

    assert output_path.exists()
    assert "# Public DK1/DK2 surplus-risk proof-of-work" in output_path.read_text()
    written_files = [
        path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()
    ]
    assert written_files == [
        Path("artifacts/public-surplus-risk-report.md")
    ]
    assert result["file_written"] is True
    assert result["database_write_performed"] is False


def test_no_database_writes_or_runtime_database_imports() -> None:
    report = report_export.render_markdown_report()
    source = (
        REPO_ROOT / "scripts" / "public_surplus_risk_report_export.py"
    ).read_text()
    forbidden_terms = [
        "psycopg",
        "sqlalchemy",
        "DATABASE_URL",
        "INSERT",
        "UPDATE",
        "DELETE",
        "connect(",
        "execute(",
    ]

    assert "database_write_performed" in report_export.export_report(
        report_export.ReportExportConfig("markdown", "", True),
        stdout=io.StringIO(),
    )
    assert "Public DK1/DK2" in report
    for term in forbidden_terms:
        assert term not in source
