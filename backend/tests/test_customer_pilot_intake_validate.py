from __future__ import annotations

import csv
import importlib.util
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


customer_pilot_intake_validate = load_script_module(
    "customer_pilot_intake_validate.py"
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def valid_rows(count: int = 24, **overrides: object) -> list[dict[str, object]]:
    rows = []
    for hour in range(count):
        row = {
            "site_id": "site-a",
            "price_area": "DK1" if hour % 2 == 0 else "DK2",
            "timestamp": f"2026-01-01T{hour % 24:02d}:00:00+00:00",
            "timezone": "UTC",
            "load_mwh": "1.25",
            "flexible_capacity_mw": "0.5",
        }
        row.update(overrides)
        rows.append(row)
    return rows


def config_for(path: Path, **overrides: object):
    values = {
        "input_path": path,
        "customer_type": "common",
        "min_rows": 24,
        "dry_run": True,
    }
    values.update(overrides)
    return customer_pilot_intake_validate.CustomerPilotIntakeConfig(**values)


def test_valid_common_csv(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    write_csv(input_path, valid_rows())

    summary = customer_pilot_intake_validate.validate_customer_pilot_intake(
        config_for(input_path)
    )

    assert summary.status == "valid"
    assert summary.row_count == 24
    assert "site_id" in summary.detected_columns
    assert summary.missing_required_columns == ()
    assert summary.warnings == ()


def test_invalid_missing_required_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    write_csv(input_path, [{"site_id": "site-a", "load_mwh": "1.0"}])

    summary = customer_pilot_intake_validate.validate_customer_pilot_intake(
        config_for(input_path, min_rows=1)
    )

    assert summary.status == "invalid"
    assert summary.missing_required_columns == (
        "price_area",
        "timestamp",
        "timezone",
    )
    assert "Required common columns are missing." in summary.errors


def test_invalid_price_area(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    rows = valid_rows()
    rows[0]["price_area"] = "SE3"
    write_csv(input_path, rows)

    summary = customer_pilot_intake_validate.validate_customer_pilot_intake(
        config_for(input_path)
    )

    assert summary.status == "invalid"
    assert any(
        "price_area values must be DK1 or DK2" in error
        for error in summary.errors
    )


def test_row_count_minimum(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    write_csv(input_path, valid_rows(count=2))

    summary = customer_pilot_intake_validate.validate_customer_pilot_intake(
        config_for(input_path, min_rows=3)
    )

    assert summary.status == "invalid"
    assert "CSV row count is below CUSTOMER_PILOT_MIN_ROWS." in summary.errors


def test_secret_like_column_warning(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    write_csv(input_path, valid_rows(api_key="do-not-use"))

    summary = customer_pilot_intake_validate.validate_customer_pilot_intake(
        config_for(input_path)
    )

    assert summary.status == "valid_with_warnings"
    assert any("api_key" in warning for warning in summary.warnings)


def test_producer_warnings(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    write_csv(input_path, valid_rows())

    summary = customer_pilot_intake_validate.validate_customer_pilot_intake(
        config_for(input_path, customer_type="producer")
    )

    assert summary.status == "valid_with_warnings"
    assert any("producer intake is missing" in warning for warning in summary.warnings)
    assert any("asset_type" in warning for warning in summary.warnings)


def test_flexible_consumption_warnings(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    write_csv(input_path, valid_rows())

    summary = customer_pilot_intake_validate.validate_customer_pilot_intake(
        config_for(input_path, customer_type="flexible_consumption")
    )

    assert summary.status == "valid_with_warnings"
    assert any(
        "flexible_consumption intake is missing" in warning
        for warning in summary.warnings
    )
    assert any("lead_time_minutes" in warning for warning in summary.warnings)


def test_grid_dso_warnings(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    write_csv(input_path, valid_rows())

    summary = customer_pilot_intake_validate.validate_customer_pilot_intake(
        config_for(input_path, customer_type="grid_dso")
    )

    assert summary.status == "valid_with_warnings"
    assert any("grid_dso intake is missing" in warning for warning in summary.warnings)
    assert any(
        "grid_area_id or transformer_area_id" in warning
        for warning in summary.warnings
    )
    assert any(
        "congestion_event or outage_or_constraint_note" in warning
        for warning in summary.warnings
    )


def test_no_file_db_or_external_write_behavior(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    write_csv(input_path, valid_rows())
    before = sorted(path.name for path in tmp_path.iterdir())

    summary = customer_pilot_intake_validate.validate_customer_pilot_intake(
        config_for(input_path)
    )
    after = sorted(path.name for path in tmp_path.iterdir())

    assert after == before
    assert summary.file_written is False
    assert summary.database_write_performed is False
    assert summary.external_api_calls_performed is False


def test_safety_boundary_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_path = tmp_path / "customer.csv"
    write_csv(input_path, valid_rows())
    summary = customer_pilot_intake_validate.validate_customer_pilot_intake(
        config_for(input_path)
    )

    customer_pilot_intake_validate.print_summary(summary)
    output = capsys.readouterr().out

    assert "read-only validation only" in output
    assert "no customer-specific savings calculated" in output
    assert "no automatic control" in output
    assert "no dispatch" in output
    assert "no activation" in output
    assert "no live control signals" in output
    assert "no asset integration" in output
    assert "no database writes" in output
    assert "no external API calls" in output
