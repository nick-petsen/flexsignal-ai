from __future__ import annotations

import csv
import importlib.util
import io
import json
import sys
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


customer_pilot_report_export = load_script_module(
    "customer_pilot_report_export.py"
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_snapshot(path: Path) -> None:
    write_snapshot_with_signal(path, opportunity_signal_eur_per_mwh=8.0)


def write_snapshot_with_signal(
    path: Path,
    *,
    opportunity_signal_eur_per_mwh: float,
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
    report_write: bool = False,
):
    workflow_config = (
        customer_pilot_report_export.CustomerPilotWorkflowPreviewConfig(
            input_path=input_path,
            snapshot_path=snapshot_path,
            customer_type="common",
            price_area=None,
            dry_run=True,
        )
    )
    return customer_pilot_report_export.CustomerPilotReportExportConfig(
        workflow_config=workflow_config,
        output_path=output_path,
        report_write=report_write,
    )


def test_stdout_markdown_report_for_valid_dk1_workflow(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)
    stdout = io.StringIO()

    result = customer_pilot_report_export.export_report(
        config_for(input_path, snapshot_path),
        stdout=stdout,
    )
    report = stdout.getvalue()

    assert "# Customer pilot workflow preview report" in report
    assert "## Scope note" in report
    assert "read-only pilot preview" in report
    assert "public price signal only" in report
    assert "human review required" in report
    assert "Total customer rows: 24" in report
    assert "Validation status: `valid`" in report
    assert "Signal match status: `matched`" in report
    assert "Opportunity estimate status: `estimate_available`" in report
    assert (
        "| DK1 | 2026-04-04T21:00:00Z | 2026-04-04T23:00:00Z | "
        "100 | high | 1 | 2.00 MWh | 8.00 EUR/MWh | 16.00 EUR |"
    ) in report
    assert (
        "matched flexible MWh x public opportunity signal EUR/MWh"
        in report
    )
    assert result["file_written"] is False


def test_markdown_report_formats_human_numeric_values(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows(flexible_energy_mwh="48.0"))
    write_snapshot_with_signal(
        snapshot_path,
        opportunity_signal_eur_per_mwh=8.343775,
    )
    stdout = io.StringIO()

    customer_pilot_report_export.export_report(
        config_for(input_path, snapshot_path),
        stdout=stdout,
    )
    report = stdout.getvalue()

    assert "48.00 MWh" in report
    assert "8.34 EUR/MWh" in report
    assert "400.50 EUR" in report
    assert "400.5012" not in report
    assert "8.343775" not in report


def test_output_path_writes_only_when_report_write_true(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    output_path = tmp_path / "artifacts" / "customer-pilot-preview.md"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    result = customer_pilot_report_export.export_report(
        config_for(
            input_path,
            snapshot_path,
            output_path=str(output_path),
            report_write=True,
        ),
        stdout=io.StringIO(),
    )

    assert output_path.exists()
    assert "# Customer pilot workflow preview report" in output_path.read_text(
        encoding="utf-8"
    )
    written_files = sorted(
        path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()
    )
    assert written_files == [
        Path("artifacts/customer-pilot-preview.md"),
        Path("customer.csv"),
        Path("snapshot.json"),
    ]
    assert result["file_written"] is True
    assert result["database_write_performed"] is False
    assert result["external_api_calls_performed"] is False


def test_dry_run_output_path_without_write_prints_and_writes_no_report(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    output_path = tmp_path / "artifacts" / "customer-pilot-preview.md"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    stdout = io.StringIO()

    result = customer_pilot_report_export.export_report(
        config_for(
            input_path,
            snapshot_path,
            output_path=str(output_path),
            report_write=False,
        ),
        stdout=stdout,
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert "# Customer pilot workflow preview report" in stdout.getvalue()
    assert output_path.exists() is False
    assert after == before
    assert result["file_written"] is False


def test_invalid_workflow_exits_safely_with_safe_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [{"site_id": "site-a", "load_mwh": "1.0"}])
    write_snapshot(snapshot_path)
    monkeypatch.setenv("CUSTOMER_PILOT_INPUT_PATH", str(input_path))
    monkeypatch.setenv("PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH", str(snapshot_path))

    exit_code = customer_pilot_report_export.main()
    report = capsys.readouterr().out

    assert exit_code == 1
    assert "# Customer pilot workflow preview report" in report
    assert "Validation status: `invalid`" in report
    assert "Signal match status: `not_run`" in report
    assert "## Workflow errors" in report
    assert "## Safety boundary" in report


def test_no_file_db_or_external_writes_beyond_requested_report_file(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    output_path = tmp_path / "report.md"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    result = customer_pilot_report_export.export_report(
        config_for(
            input_path,
            snapshot_path,
            output_path=str(output_path),
            report_write=True,
        ),
        stdout=io.StringIO(),
    )
    source = (
        REPO_ROOT / "scripts" / "customer_pilot_report_export.py"
    ).read_text(encoding="utf-8")

    assert output_path.exists()
    assert sorted(
        path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()
    ) == [Path("customer.csv"), Path("report.md"), Path("snapshot.json")]
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


def test_safety_boundary_text(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)
    stdout = io.StringIO()

    customer_pilot_report_export.export_report(
        config_for(input_path, snapshot_path),
        stdout=stdout,
    )
    report = stdout.getvalue()

    assert "read-only report export only" in report
    assert "no customer-specific monetary benefit calculated" in report
    assert "no commercial outcome calculated" in report
    assert "no automatic control" in report
    assert "no dispatch" in report
    assert "no activation" in report
    assert "no live control signals" in report
    assert "no asset integration" in report
    assert "no database writes" in report
    assert "no external API calls" in report
    assert "human review required" in report


def test_non_boundary_report_content_avoids_forbidden_claim_wording(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)
    stdout = io.StringIO()

    customer_pilot_report_export.export_report(
        config_for(input_path, snapshot_path),
        stdout=stdout,
    )
    report = stdout.getvalue().lower()

    for forbidden in (
        "saved",
        "savings",
        "profit",
        "revenue",
        "earnings",
        "guaranteed",
    ):
        assert forbidden not in report
