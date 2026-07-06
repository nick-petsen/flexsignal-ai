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

UNAVAILABLE_PRICE_CONTEXT = {
    "min_price_eur_per_mwh": None,
    "average_price_eur_per_mwh": None,
    "max_price_eur_per_mwh": None,
    "price_context_status": "not_available",
    "opportunity_signal_eur_per_mwh": None,
    "opportunity_signal_note": (
        "Public DayAheadPrices rows were unavailable or insufficient for this "
        "window."
    ),
}


def price_context_counts(
    *,
    low_price_hours: int,
    negative_price_hours: int,
) -> dict[str, int]:
    return {
        "low_price_hour_count": low_price_hours,
        "negative_price_hour_count": negative_price_hours,
    }


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
        "min_price_eur_per_mwh": -25.4575,
        "average_price_eur_per_mwh": 16.656225,
        "max_price_eur_per_mwh": 115.707498,
        "price_context_status": "available",
        "opportunity_signal_eur_per_mwh": 8.343775,
        "opportunity_signal_note": (
            "Public market/system-level signal only: max(0, public low-price "
            "threshold 25 EUR/MWh - average window DayAheadPrices EUR/MWh). "
            "Customer load, flexibility, tariff, and constraints are excluded."
        ),
        **price_context_counts(low_price_hours=39, negative_price_hours=20),
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
        "min_price_eur_per_mwh": 8.07,
        "average_price_eur_per_mwh": 43.43525,
        "max_price_eur_per_mwh": 104.827501,
        "price_context_status": "available",
        "opportunity_signal_eur_per_mwh": 0.0,
        "opportunity_signal_note": (
            "Public market/system-level signal only: max(0, public low-price "
            "threshold 25 EUR/MWh - average window DayAheadPrices EUR/MWh). "
            "Customer load, flexibility, tariff, and constraints are excluded."
        ),
        **price_context_counts(low_price_hours=3, negative_price_hours=0),
    }


def test_snapshot_price_context_fields_exist_and_are_available() -> None:
    windows = snapshot_export.build_snapshot()["top_risk_windows"]
    available_by_area = {"DK1": False, "DK2": False}

    for price_area, area_windows in windows.items():
        for window in area_windows:
            assert window["price_context_status"] == "available"
            assert isinstance(window["min_price_eur_per_mwh"], float | int)
            assert isinstance(window["average_price_eur_per_mwh"], float | int)
            assert isinstance(window["max_price_eur_per_mwh"], float | int)
            assert isinstance(
                window["opportunity_signal_eur_per_mwh"],
                float | int,
            )
            expected_signal = max(0.0, 25.0 - window["average_price_eur_per_mwh"])
            assert round(window["opportunity_signal_eur_per_mwh"], 6) == round(
                expected_signal,
                6,
            )
            assert window["low_price_hour_count"] == window["low_price_hours"]
            assert (
                window["negative_price_hour_count"]
                == window["negative_price_hours"]
            )
            available_by_area[price_area] = True

    assert available_by_area == {"DK1": True, "DK2": True}


def test_missing_public_price_rows_stay_unavailable() -> None:
    context = snapshot_export.build_price_context_from_public_prices(
        [],
        low_price_hour_count=0,
        negative_price_hour_count=0,
    )

    assert context == {
        **UNAVAILABLE_PRICE_CONTEXT,
        "low_price_hour_count": None,
        "negative_price_hour_count": None,
    }


def test_available_public_price_context_signal_is_deterministic() -> None:
    context = snapshot_export.build_price_context_from_public_prices(
        [10.0, 20.0, 40.0],
        low_price_hour_count=2,
        negative_price_hour_count=0,
    )

    assert context["price_context_status"] == "available"
    assert context["average_price_eur_per_mwh"] == 70.0 / 3.0
    assert context["opportunity_signal_eur_per_mwh"] == 25.0 - (70.0 / 3.0)
    assert "Public market/system-level signal only" in context[
        "opportunity_signal_note"
    ]


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
    assert "saved money" not in payload
    assert "profit" not in payload
    assert "revenue" not in payload
    assert "customer-specific savings are" not in payload
    assert "customer-specific savings of" not in payload
    assert "savings estimate" not in payload


def test_snapshot_export_keeps_backend_api_contract_out_of_scope() -> None:
    source = (
        REPO_ROOT / "scripts" / "public_surplus_risk_snapshot_export.py"
    ).read_text(encoding="utf-8")

    assert "/api/" not in source
    assert "FastAPI" not in source
    assert "APIRouter" not in source


def test_frontend_snapshot_typing_supports_public_price_context() -> None:
    source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "publicBacktestSnapshot.ts"
    ).read_text(encoding="utf-8")

    for term in (
        "min_price_eur_per_mwh",
        "average_price_eur_per_mwh",
        "max_price_eur_per_mwh",
        "negative_price_hour_count",
        "low_price_hour_count",
        "price_context_status",
        "opportunity_signal_eur_per_mwh",
        "opportunity_signal_note",
        "averagePrice",
        "opportunitySignal",
    ):
        assert term in source


def test_frontend_snapshot_loader_does_not_call_backend() -> None:
    source = (
        REPO_ROOT / "frontend" / "src" / "lib" / "publicBacktestSnapshot.ts"
    ).read_text(encoding="utf-8")

    assert "fetch(" not in source
    assert "backendApiBaseUrl" not in source
    assert "/api/" not in source
