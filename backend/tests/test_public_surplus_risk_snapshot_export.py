from __future__ import annotations

import importlib.util
import io
import json
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


snapshot_export = load_script_module("public_surplus_risk_snapshot_export.py")


def test_snapshot_validates_schema_version() -> None:
    snapshot = snapshot_export.build_snapshot()

    assert snapshot["schema_version"] == "public_surplus_risk_snapshot.v1"
    snapshot_export.validate_snapshot(snapshot)


def test_snapshot_contains_dk1_dk2_summary_metrics() -> None:
    summary = snapshot_export.build_snapshot()["summary_metrics"]

    assert summary["DK1"] == {
        "joined_hours": 4208,
        "skipped_rows": 233,
        "medium_risk_hours": 1663,
        "high_risk_hours": 174,
        "risk_windows": 129,
        "highest_risk_score": 100,
        "negative_price_hours": 132,
        "low_price_hours": 479,
        "average_renewable_share_percent": 68.8,
        "max_renewable_share_percent": 192.2,
    }
    assert summary["DK2"] == {
        "joined_hours": 4208,
        "skipped_rows": 233,
        "medium_risk_hours": 288,
        "high_risk_hours": 2,
        "risk_windows": 72,
        "highest_risk_score": 85,
        "negative_price_hours": 78,
        "low_price_hours": 491,
        "average_renewable_share_percent": 38.2,
        "max_renewable_share_percent": 108.6,
    }


def test_snapshot_contains_top_risk_windows() -> None:
    windows = snapshot_export.build_snapshot()["top_risk_windows"]

    assert len(windows["DK1"]) == 5
    assert len(windows["DK2"]) == 5
    assert windows["DK1"][0] == {
        "start": "2026-04-04T21:00:00",
        "end": "2026-04-06T23:00:00",
        "duration_hours": 51,
        "score": 100,
        "level": "high",
        "low_price_hours": 39,
        "negative_price_hours": 20,
        "average_renewable_share_percent": 98.6,
        "max_renewable_share_percent": 163.3,
        "reasons": [
            "low_price",
            "high_renewable_share",
            "renewable_generation_above_consumption",
            "negative_price",
        ],
    }
    assert windows["DK2"][0] == {
        "start": "2026-04-24T21:00:00",
        "end": "2026-04-25T06:00:00",
        "duration_hours": 10,
        "score": 85,
        "level": "high",
        "low_price_hours": 3,
        "negative_price_hours": 0,
        "average_renewable_share_percent": 98.0,
        "max_renewable_share_percent": 108.6,
        "reasons": [
            "high_renewable_share",
            "renewable_generation_above_consumption",
            "low_price",
        ],
    }


def test_snapshot_contains_safety_boundaries() -> None:
    snapshot = snapshot_export.build_snapshot()

    assert snapshot["scope"] == "public market/system-level only"
    assert snapshot["decision_boundary"] == "read-only decision support"
    assert snapshot["not_customer_specific_savings"] is True
    assert snapshot["no_automatic_control"] is True
    assert snapshot["no_dispatch"] is True
    assert snapshot["no_activation"] is True
    assert snapshot["no_live_control_signals"] is True
    assert snapshot["no_asset_integration"] is True
    assert snapshot["database_write_performed"] is False
    assert "No automatic control, dispatch, or activation." in snapshot[
        "important_boundaries"
    ]


def test_dry_run_does_not_write(tmp_path: Path) -> None:
    output_path = tmp_path / "snapshot.json"
    stdout = io.StringIO()
    config = snapshot_export.SnapshotExportConfig(
        output_path=str(output_path),
        dry_run=True,
        print_snapshot=False,
        write=False,
    )

    result = snapshot_export.export_snapshot(config, stdout=stdout)

    assert output_path.exists() is False
    assert list(tmp_path.iterdir()) == []
    assert result["file_written"] is False
    assert result["database_write_performed"] is False
    assert "Target path:" in stdout.getvalue()
    assert "Validation summary:" in stdout.getvalue()


def test_write_mode_writes_only_requested_artifact(tmp_path: Path) -> None:
    output_path = tmp_path / "artifacts" / "snapshot.json"
    config = snapshot_export.SnapshotExportConfig(
        output_path=str(output_path),
        dry_run=True,
        print_snapshot=False,
        write=True,
    )

    result = snapshot_export.export_snapshot(config, stdout=io.StringIO())

    assert result["file_written"] is True
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "public_surplus_risk_snapshot.v1"
    written_files = [
        path.relative_to(tmp_path) for path in tmp_path.rglob("*") if path.is_file()
    ]
    assert written_files == [Path("artifacts/snapshot.json")]


def test_no_database_writes_network_calls_or_runtime_database_imports() -> None:
    source = (
        REPO_ROOT / "scripts" / "public_surplus_risk_snapshot_export.py"
    ).read_text(encoding="utf-8")
    result = snapshot_export.export_snapshot(
        snapshot_export.SnapshotExportConfig(
            output_path="snapshot.json",
            dry_run=True,
            print_snapshot=False,
            write=False,
        ),
        stdout=io.StringIO(),
    )

    assert result["database_write_performed"] is False
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


def test_no_customer_specific_savings_calculated_or_claimed() -> None:
    snapshot = snapshot_export.build_snapshot()
    payload = snapshot_export.render_snapshot_json(snapshot).lower()

    assert snapshot["customer_specific_savings_calculated"] is False
    assert snapshot["not_customer_specific_savings"] is True
    assert "not customer-specific savings" in payload
    assert "customer-specific savings are" not in payload
    assert "customer-specific savings of" not in payload
    assert "savings estimate" not in payload
