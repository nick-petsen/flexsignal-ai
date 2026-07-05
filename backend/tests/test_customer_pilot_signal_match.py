from __future__ import annotations

import csv
import importlib.util
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


customer_pilot_signal_match = load_script_module("customer_pilot_signal_match.py")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    assert rows
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_snapshot(path: Path) -> None:
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
                }
            ],
            "DK2": [
                {
                    "start": "2026-04-24T21:00:00",
                    "end": "2026-04-24T23:00:00",
                    "duration_hours": 3,
                    "score": 85,
                    "level": "high",
                }
            ],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def base_row(**overrides: object) -> dict[str, object]:
    row = {
        "site_id": "site-a",
        "price_area": "DK1",
        "timestamp": "2026-04-04T22:00:00+00:00",
        "timezone": "UTC",
        "load_mwh": "1.25",
        "generation_mwh": "",
        "flexible_capacity_mw": "0.5",
        "flexible_energy_mwh": "",
    }
    row.update(overrides)
    return row


def config_for(input_path: Path, snapshot_path: Path, **overrides: object):
    values = {
        "input_path": input_path,
        "snapshot_path": snapshot_path,
        "price_area": None,
        "min_match_rows": 1,
        "dry_run": True,
    }
    values.update(overrides)
    return customer_pilot_signal_match.CustomerPilotSignalMatchConfig(**values)


def test_valid_overlap_with_dk1_public_window(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [base_row()])
    write_snapshot(snapshot_path)

    summary = customer_pilot_signal_match.match_customer_pilot_signal(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "matched"
    assert summary.customer_price_areas_detected == ("DK1",)
    assert summary.total_customer_rows == 1
    assert summary.matched_window_count == 1
    assert summary.matched_customer_rows == 1
    assert summary.candidate_windows[0]["price_area"] == "DK1"
    assert summary.candidate_windows[0]["public_risk_score"] == 100
    assert summary.candidate_windows[0]["match_status"] == (
        "candidate_for_human_review"
    )


def test_valid_overlap_with_dk2_public_window(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(
        input_path,
        [
            base_row(
                price_area="DK2",
                timestamp="2026-04-24T22:00:00+00:00",
                generation_mwh="2.5",
                load_mwh="",
                flexible_capacity_mw="",
            )
        ],
    )
    write_snapshot(snapshot_path)

    summary = customer_pilot_signal_match.match_customer_pilot_signal(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "matched"
    assert summary.customer_price_areas_detected == ("DK2",)
    assert summary.candidate_windows[0]["price_area"] == "DK2"
    assert summary.candidate_windows[0]["public_risk_score"] == 85
    assert summary.candidate_windows[0]["customer_has_generation_data"] is True


def test_no_overlap_returns_no_matches(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [base_row(timestamp="2026-02-01T00:00:00+00:00")])
    write_snapshot(snapshot_path)

    summary = customer_pilot_signal_match.match_customer_pilot_signal(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "no_matches"
    assert summary.matched_window_count == 0
    assert summary.matched_customer_rows == 0
    assert summary.candidate_windows == ()


def test_invalid_missing_required_customer_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [{"site_id": "site-a", "load_mwh": "1.0"}])
    write_snapshot(snapshot_path)

    summary = customer_pilot_signal_match.match_customer_pilot_signal(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "invalid"
    assert any(
        "Required customer columns are missing" in error
        for error in summary.errors
    )
    assert "price_area" in summary.errors[0]


def test_invalid_snapshot_path(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    write_csv(input_path, [base_row()])

    summary = customer_pilot_signal_match.match_customer_pilot_signal(
        config_for(input_path, tmp_path / "missing.json")
    )

    assert summary.status == "invalid"
    assert "Public surplus-risk snapshot path is invalid." in summary.errors


def test_price_area_mismatch_does_not_cross_match_dk1_dk2(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(
        input_path,
        [
            base_row(
                price_area="DK2",
                timestamp="2026-04-04T22:00:00+00:00",
            )
        ],
    )
    write_snapshot(snapshot_path)

    summary = customer_pilot_signal_match.match_customer_pilot_signal(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "no_matches"
    assert summary.customer_price_areas_detected == ("DK2",)
    assert summary.candidate_windows == ()


def test_availability_flag_counted_when_present(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(
        input_path,
        [
            base_row(availability_flag="true", operational_note="can review"),
            base_row(timestamp="2026-04-04T23:00:00+00:00", availability_flag="false"),
        ],
    )
    write_snapshot(snapshot_path)

    summary = customer_pilot_signal_match.match_customer_pilot_signal(
        config_for(input_path, snapshot_path)
    )

    candidate = summary.candidate_windows[0]
    assert candidate["customer_rows_in_window"] == 2
    assert candidate["availability_rows_true"] == 1
    assert candidate["notes_present_count"] == 1


def test_limited_customer_data_warning_without_energy_or_flex_columns(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(
        input_path,
        [
            {
                "site_id": "site-a",
                "price_area": "DK1",
                "timestamp": "2026-04-04T22:00:00+00:00",
                "timezone": "UTC",
            }
        ],
    )
    write_snapshot(snapshot_path)

    summary = customer_pilot_signal_match.match_customer_pilot_signal(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "matched_with_warnings"
    assert summary.candidate_windows[0]["match_status"] == (
        "matched_but_customer_data_limited"
    )
    assert any("limited customer load" in warning for warning in summary.warnings)


def test_no_file_db_or_external_writes(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [base_row()])
    write_snapshot(snapshot_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    summary = customer_pilot_signal_match.match_customer_pilot_signal(
        config_for(input_path, snapshot_path)
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    source = (REPO_ROOT / "scripts" / "customer_pilot_signal_match.py").read_text(
        encoding="utf-8"
    )

    assert after == before
    assert summary.file_written is False
    assert summary.database_write_performed is False
    assert summary.external_api_calls_performed is False
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


def test_safety_boundary_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [base_row()])
    write_snapshot(snapshot_path)

    summary = customer_pilot_signal_match.match_customer_pilot_signal(
        config_for(input_path, snapshot_path)
    )
    customer_pilot_signal_match.print_summary(summary)
    output = capsys.readouterr().out

    assert "read-only signal matching only" in output
    assert "no customer-specific savings calculated" in output
    assert "no profit/revenue calculated" in output
    assert "no automatic control" in output
    assert "no dispatch" in output
    assert "no activation" in output
    assert "no live control signals" in output
    assert "no asset integration" in output
    assert "no database writes" in output
    assert "no external API calls" in output
    assert "human review required" in output
