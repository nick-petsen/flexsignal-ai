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


customer_pilot_artifact_pack = load_script_module(
    "customer_pilot_artifact_pack.py"
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_snapshot(
    path: Path,
    *,
    opportunity_signal_eur_per_mwh: float = 8.343775,
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
            "flexible_energy_mwh": "48.0",
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
    artifact_dir: Path,
    *,
    run_id: str | None = "pilot-demo-001",
    artifact_write: bool = False,
):
    workflow_config = (
        customer_pilot_artifact_pack.CustomerPilotWorkflowPreviewConfig(
            input_path=input_path,
            snapshot_path=snapshot_path,
            customer_type="common",
            price_area=None,
            dry_run=True,
        )
    )
    return customer_pilot_artifact_pack.CustomerPilotArtifactPackConfig(
        workflow_config=workflow_config,
        artifact_dir=artifact_dir,
        run_id=run_id,
        artifact_write=artifact_write,
    )


def test_dry_run_creates_no_files(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    artifact_dir = tmp_path / "artifacts"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    stdout = io.StringIO()

    result = customer_pilot_artifact_pack.create_customer_pilot_artifact_pack(
        config_for(input_path, snapshot_path, artifact_dir, artifact_write=False),
        stdout=stdout,
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    output = json.loads(stdout.getvalue())

    assert after == before
    assert artifact_dir.exists() is False
    assert result["file_written"] is False
    assert output["artifact_pack_status"] == "dry_run"
    assert output["file_written"] is False
    assert output["database_write_performed"] is False
    assert output["external_api_calls_performed"] is False
    assert output["would_create_files"] == list(
        customer_pilot_artifact_pack.ARTIFACT_FILENAMES
    )


def test_dry_run_does_not_render_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    artifact_dir = tmp_path / "artifacts"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    def fail_pdf_render(*args: object, **kwargs: object) -> bytes:
        raise AssertionError("dry-run should not render PDF bytes")

    monkeypatch.setattr(
        customer_pilot_artifact_pack,
        "render_pdf_bytes",
        fail_pdf_render,
    )

    result = customer_pilot_artifact_pack.create_customer_pilot_artifact_pack(
        config_for(input_path, snapshot_path, artifact_dir, artifact_write=False),
        stdout=io.StringIO(),
    )

    assert result["file_written"] is False
    assert artifact_dir.exists() is False


def test_write_mode_creates_exactly_one_run_folder_with_exact_files(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    artifact_dir = tmp_path / "artifacts"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    result = customer_pilot_artifact_pack.create_customer_pilot_artifact_pack(
        config_for(input_path, snapshot_path, artifact_dir, artifact_write=True),
        stdout=io.StringIO(),
    )

    run_dirs = [path for path in artifact_dir.iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    assert run_dirs[0].name == "pilot-demo-001"
    assert sorted(path.name for path in run_dirs[0].iterdir()) == sorted(
        customer_pilot_artifact_pack.ARTIFACT_FILENAMES
    )
    assert sorted(
        path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()
    ) == [
        Path("artifacts/pilot-demo-001/README.txt"),
        Path("artifacts/pilot-demo-001/customer-pilot-preview.md"),
        Path("artifacts/pilot-demo-001/customer-pilot-preview.pdf"),
        Path("artifacts/pilot-demo-001/workflow-summary.json"),
        Path("customer.csv"),
        Path("snapshot.json"),
    ]
    assert result["file_written"] is True
    assert result["database_write_performed"] is False
    assert result["external_api_calls_performed"] is False


def test_pdf_bytes_start_with_pdf_header(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    artifact_dir = tmp_path / "artifacts"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    customer_pilot_artifact_pack.create_customer_pilot_artifact_pack(
        config_for(input_path, snapshot_path, artifact_dir, artifact_write=True),
        stdout=io.StringIO(),
    )

    pdf_path = artifact_dir / "pilot-demo-001" / "customer-pilot-preview.pdf"
    assert pdf_path.read_bytes().startswith(b"%PDF")


def test_human_facing_reports_use_formatted_values(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    artifact_dir = tmp_path / "artifacts"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    customer_pilot_artifact_pack.create_customer_pilot_artifact_pack(
        config_for(input_path, snapshot_path, artifact_dir, artifact_write=True),
        stdout=io.StringIO(),
    )

    run_dir = artifact_dir / "pilot-demo-001"
    markdown = (run_dir / "customer-pilot-preview.md").read_text(encoding="utf-8")
    summary = customer_pilot_artifact_pack.run_customer_pilot_workflow_preview(
        config_for(input_path, snapshot_path, artifact_dir).workflow_config
    )
    pdf_source = customer_pilot_artifact_pack.render_pdf_report_text(summary)

    for report_text in (markdown, pdf_source):
        assert "48.00 MWh" in report_text
        assert "8.34 EUR/MWh" in report_text
        assert "400.50 EUR" in report_text
        assert "400.5012" not in report_text
        assert "8.343775" not in report_text


def test_artifact_text_avoids_forbidden_claim_wording(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    artifact_dir = tmp_path / "artifacts"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    customer_pilot_artifact_pack.create_customer_pilot_artifact_pack(
        config_for(input_path, snapshot_path, artifact_dir, artifact_write=True),
        stdout=io.StringIO(),
    )

    run_dir = artifact_dir / "pilot-demo-001"
    summary = json.loads((run_dir / "workflow-summary.json").read_text("utf-8"))
    report_text = "\n".join(
        [
            json.dumps(summary),
            (run_dir / "customer-pilot-preview.md").read_text(encoding="utf-8"),
            (run_dir / "README.txt").read_text(encoding="utf-8"),
        ]
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


def test_path_traversal_run_id_is_sanitized_inside_artifact_dir(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    artifact_dir = tmp_path / "artifacts"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    result = customer_pilot_artifact_pack.create_customer_pilot_artifact_pack(
        config_for(
            input_path,
            snapshot_path,
            artifact_dir,
            run_id="../outside",
            artifact_write=True,
        ),
        stdout=io.StringIO(),
    )

    run_dir = Path(result["run_dir"])
    assert run_dir.parent == artifact_dir.resolve()
    assert run_dir.name == "outside"
    assert (tmp_path / "outside").exists() is False
    assert len([path for path in artifact_dir.iterdir() if path.is_dir()]) == 1


def test_workflow_summary_contains_required_safety_flags(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    artifact_dir = tmp_path / "artifacts"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    customer_pilot_artifact_pack.create_customer_pilot_artifact_pack(
        config_for(input_path, snapshot_path, artifact_dir, artifact_write=True),
        stdout=io.StringIO(),
    )

    summary = json.loads(
        (artifact_dir / "pilot-demo-001" / "workflow-summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert summary["file_written"] is True
    assert summary["database_write_performed"] is False
    assert summary["external_api_calls_performed"] is False
    assert summary["safety_flags"] == {
        "file_written": True,
        "database_write_performed": False,
        "external_api_calls_performed": False,
        "automatic_control_performed": False,
        "dispatch_performed": False,
        "activation_performed": False,
        "live_control_signals_performed": False,
        "asset_integration_performed": False,
        "human_review_required": True,
    }
    assert "no automatic control" in summary["safety_boundary"]
    assert "no dispatch" in summary["safety_boundary"]
    assert "no activation" in summary["safety_boundary"]
    assert "human review required" in summary["safety_boundary"]


def test_no_database_external_api_or_control_behavior_added(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    artifact_dir = tmp_path / "artifacts"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    result = customer_pilot_artifact_pack.create_customer_pilot_artifact_pack(
        config_for(input_path, snapshot_path, artifact_dir, artifact_write=True),
        stdout=io.StringIO(),
    )
    source = (
        REPO_ROOT / "scripts" / "customer_pilot_artifact_pack.py"
    ).read_text(encoding="utf-8")

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
        "socket",
        "subprocess",
        "send_control",
        "dispatch_request",
        "activate_asset",
        "asset_client",
    ):
        assert term not in source


def test_non_csv_input_is_rejected(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.xlsx"
    snapshot_path = tmp_path / "snapshot.json"
    artifact_dir = tmp_path / "artifacts"
    input_path.write_text("not,csv\n", encoding="utf-8")
    write_snapshot(snapshot_path)

    with pytest.raises(customer_pilot_artifact_pack.CustomerPilotArtifactPackError):
        customer_pilot_artifact_pack.load_config(
            {
                "CUSTOMER_PILOT_INPUT_PATH": str(input_path),
                "PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH": str(snapshot_path),
                "CUSTOMER_PILOT_ARTIFACT_DIR": str(artifact_dir),
            }
        )
