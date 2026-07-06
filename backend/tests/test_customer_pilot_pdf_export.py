from __future__ import annotations

import builtins
import csv
import importlib.util
import io
import json
import sys
import tomllib
from pathlib import Path
from types import ModuleType

import pytest


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


customer_pilot_pdf_export = load_script_module("customer_pilot_pdf_export.py")


def test_backend_project_dependencies_declare_reportlab() -> None:
    pyproject = tomllib.loads(
        (REPO_ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert "reportlab" in pyproject["project"]["dependencies"]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_snapshot(
    path: Path,
    *,
    opportunity_signal_eur_per_mwh: float = 8.0,
) -> None:
    payload = {
        "schema_version": "public_surplus_risk_snapshot.v1",
        "top_risk_windows": {
            "DK1": [
                {
                    "start": "2026-04-04T21:00:00",
                    "end": "2026-04-04T23:00:00",
                    "duration_hours": 3,
                    "score": 100,
                    "level": "high",
                    "price_context_status": "available",
                    "opportunity_signal_eur_per_mwh": (
                        opportunity_signal_eur_per_mwh
                    ),
                }
            ],
            "DK2": [
                {
                    "start": "2026-04-24T21:00:00",
                    "end": "2026-04-24T23:00:00",
                    "duration_hours": 3,
                    "score": 85,
                    "level": "high",
                    "price_context_status": "available",
                    "opportunity_signal_eur_per_mwh": 5.5,
                }
            ],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def valid_rows(
    *,
    price_area: str = "DK1",
    matching_timestamp: str = "2026-04-04T22:00:00+00:00",
    row_count: int = 24,
    **overrides: object,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for hour in range(row_count):
        row = {
            "site_id": "site-a",
            "price_area": price_area,
            "timestamp": f"2026-02-01T{hour:02d}:00:00+00:00",
            "timezone": "UTC",
            "load_mwh": "1.25",
            "generation_mwh": "",
            "flexible_capacity_mw": "0.5",
            "flexible_energy_mwh": "2.0",
            "availability_flag": "true",
            "operational_note": "review locally",
        }
        row.update(overrides)
        rows.append(row)
    rows[0]["timestamp"] = matching_timestamp
    return rows


def config_for(
    input_path: Path,
    snapshot_path: Path,
    *,
    output_path: str = "",
    pdf_write: bool = False,
):
    workflow_config = (
        customer_pilot_pdf_export.CustomerPilotWorkflowPreviewConfig(
            input_path=input_path,
            snapshot_path=snapshot_path,
            customer_type="common",
            price_area=None,
            dry_run=True,
        )
    )
    return customer_pilot_pdf_export.CustomerPilotPdfExportConfig(
        workflow_config=workflow_config,
        output_path=output_path,
        pdf_write=pdf_write,
    )


def build_summary(input_path: Path, snapshot_path: Path):
    return customer_pilot_pdf_export.run_customer_pilot_workflow_preview(
        config_for(input_path, snapshot_path).workflow_config
    )


def test_no_write_mode_with_output_path_does_not_create_pdf(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    output_path = tmp_path / "customer-pilot-preview.pdf"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    stdout = io.StringIO()

    result = customer_pilot_pdf_export.export_pdf(
        config_for(
            input_path,
            snapshot_path,
            output_path=str(output_path),
            pdf_write=False,
        ),
        stdout=stdout,
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert output_path.exists() is False
    assert after == before
    assert result["file_written"] is False
    assert "No PDF was written." in stdout.getvalue()
    assert str(output_path) not in stdout.getvalue()


def test_no_output_path_prints_safe_summary_and_writes_no_pdf(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    stdout = io.StringIO()

    result = customer_pilot_pdf_export.export_pdf(
        config_for(input_path, snapshot_path, output_path="", pdf_write=True),
        stdout=stdout,
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert after == before
    assert result["file_written"] is False
    assert "No PDF output path was provided." in stdout.getvalue()
    assert "Safety boundary: read-only PDF report export only." in stdout.getvalue()


def test_explicit_write_mode_creates_only_requested_pdf_file(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    output_path = tmp_path / "artifacts" / "customer-pilot-preview.pdf"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    result = customer_pilot_pdf_export.export_pdf(
        config_for(
            input_path,
            snapshot_path,
            output_path=str(output_path),
            pdf_write=True,
        ),
        stdout=io.StringIO(),
    )

    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"%PDF")
    assert sorted(
        path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()
    ) == [
        Path("artifacts/customer-pilot-preview.pdf"),
        Path("customer.csv"),
        Path("snapshot.json"),
    ]
    assert result["file_written"] is True
    assert result["database_write_performed"] is False
    assert result["external_api_calls_performed"] is False


def test_rendered_pdf_bytes_start_with_pdf_header(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    pdf_bytes = customer_pilot_pdf_export.render_pdf_bytes(
        build_summary(input_path, snapshot_path)
    )

    assert pdf_bytes.startswith(b"%PDF")


def test_missing_reportlab_error_message_is_human_readable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "app.reporting.pdf":
            raise ModuleNotFoundError(
                "No module named 'reportlab'",
                name="reportlab",
            )
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(customer_pilot_pdf_export.CustomerPilotPdfExportError) as exc:
        customer_pilot_pdf_export.render_pdf_bytes(
            build_summary(input_path, snapshot_path)
        )

    message = str(exc.value)
    assert "PDF export requires the backend dependency 'reportlab'" in message
    assert "cd backend && python -m pip install -e '.[dev]'" in message


def test_no_file_db_or_external_writes_beyond_requested_pdf_file(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    output_path = tmp_path / "report.pdf"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    result = customer_pilot_pdf_export.export_pdf(
        config_for(
            input_path,
            snapshot_path,
            output_path=str(output_path),
            pdf_write=True,
        ),
        stdout=io.StringIO(),
    )
    source = (REPO_ROOT / "scripts" / "customer_pilot_pdf_export.py").read_text(
        encoding="utf-8"
    )

    assert output_path.exists()
    assert sorted(
        path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()
    ) == [Path("customer.csv"), Path("report.pdf"), Path("snapshot.json")]
    assert result["database_write_performed"] is False
    assert result["external_api_calls_performed"] is False
    for term in (
        "psycopg",
        "sqlalchemy",
        "DATABASE_URL",
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "urlopen",
        "requests",
        "httpx",
    ):
        assert term not in source


def test_pdf_report_text_includes_required_safety_boundary(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    report_text = customer_pilot_pdf_export.render_pdf_report_text(
        build_summary(input_path, snapshot_path)
    )

    assert "Read-only PDF report export only." in report_text
    assert "No customer-specific financial value calculated." in report_text
    assert "No commercial outcome calculated." in report_text
    assert "No automatic control, dispatch, or activation." in report_text
    assert "No live control signals." in report_text
    assert "No asset integration." in report_text
    assert "No database writes." in report_text
    assert "No external API calls." in report_text
    assert "Human review required." in report_text


def test_pdf_report_text_uses_customer_friendly_sections_and_statuses(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows(flexible_energy_mwh="48.0"))
    write_snapshot(snapshot_path, opportunity_signal_eur_per_mwh=8.343775)

    report_text = customer_pilot_pdf_export.render_pdf_report_text(
        build_summary(input_path, snapshot_path)
    )

    assert "N&O Predict" in report_text
    assert "Customer Pilot Preview Report" in report_text
    assert report_text.count("Customer Pilot Preview Report") == 1
    assert "Read-only decision support · Human review required" in report_text
    assert "Executive summary" in report_text
    assert "At-a-glance" in report_text
    assert "Candidate window" in report_text
    assert "What we found" in report_text
    assert "Recommended human review steps" in report_text
    assert "Ready for human review" in report_text
    assert "Valid" in report_text
    assert "Matched" in report_text
    assert "Estimate available" in report_text
    assert "High" in report_text
    assert "ready_for_human_review" not in report_text
    assert "estimate_available" not in report_text
    assert "Risk level | high" not in report_text
    assert "2026-04-04 21:00 UTC to 2026-04-04 23:00 UTC" in report_text
    assert "This is not a customer value claim." in report_text
    assert "N&O Predict · Read-only decision support · Human review required" in (
        report_text
    )


def test_non_boundary_pdf_source_avoids_forbidden_claim_wording(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    report_text = customer_pilot_pdf_export.render_pdf_report_text(
        build_summary(input_path, snapshot_path)
    ).lower()
    for forbidden in (
        "saved",
        "savings",
        "profit",
        "revenue",
        "earnings",
        "guaranteed",
    ):
        assert forbidden not in report_text


def test_pdf_report_text_uses_formatted_human_values(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows(flexible_energy_mwh="48.0"))
    write_snapshot(snapshot_path, opportunity_signal_eur_per_mwh=8.343775)

    report_text = customer_pilot_pdf_export.render_pdf_report_text(
        build_summary(input_path, snapshot_path)
    )

    assert "48.00 MWh" in report_text
    assert "8.34 EUR/MWh" in report_text
    assert "400.50 EUR" in report_text
    assert "400.5012" not in report_text
    assert "8.343775" not in report_text
