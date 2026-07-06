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


customer_pilot_opportunity_estimate = load_script_module(
    "customer_pilot_opportunity_estimate.py"
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
    dk1_price_status: str = "available",
    dk1_signal: object = 8.0,
    dk2_price_status: str = "available",
    dk2_signal: object = 5.5,
) -> None:
    payload = {
        "schema_version": "public_surplus_risk_snapshot.v1",
        "top_risk_windows": {
            "DK1": [
                {
                    "start": "2026-04-04T21:00:00",
                    "end": "2026-04-04T23:00:00",
                    "score": 100,
                    "level": "high",
                    "price_context_status": dk1_price_status,
                    "opportunity_signal_eur_per_mwh": dk1_signal,
                }
            ],
            "DK2": [
                {
                    "start": "2026-04-24T21:00:00",
                    "end": "2026-04-24T23:00:00",
                    "score": 85,
                    "level": "high",
                    "price_context_status": dk2_price_status,
                    "opportunity_signal_eur_per_mwh": dk2_signal,
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
        "flexible_energy_mwh": "2.0",
        "load_mwh": "1.25",
        "generation_mwh": "",
        "flexible_capacity_mw": "0.5",
        "availability_flag": "true",
        "operational_note": "reviewed locally",
    }
    row.update(overrides)
    return row


def config_for(input_path: Path, snapshot_path: Path, **overrides: object):
    values = {
        "input_path": input_path,
        "snapshot_path": snapshot_path,
        "price_area": None,
        "dry_run": True,
    }
    values.update(overrides)
    return (
        customer_pilot_opportunity_estimate.CustomerPilotOpportunityEstimateConfig(
            **values
        )
    )


def test_estimate_for_dk1_overlap_with_flexible_energy(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [base_row()])
    write_snapshot(snapshot_path)

    summary = customer_pilot_opportunity_estimate.estimate_customer_pilot_opportunity(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "estimate_available"
    assert summary.total_customer_rows == 1
    assert summary.matched_window_count == 1
    assert summary.matched_customer_rows == 1
    assert summary.total_matched_flexible_energy_mwh == 2.0
    assert summary.total_indicative_gross_opportunity_signal_eur == 16.0
    estimate = summary.candidate_estimates[0]
    assert estimate["price_area"] == "DK1"
    assert estimate["public_risk_score"] == 100
    assert estimate["public_opportunity_signal_eur_per_mwh"] == 8.0
    assert estimate["estimate_status"] == "estimate_available"


def test_estimate_for_dk2_overlap_with_flexible_energy(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(
        input_path,
        [
            base_row(
                price_area="DK2",
                timestamp="2026-04-24T22:00:00+00:00",
                flexible_energy_mwh="4.0",
            )
        ],
    )
    write_snapshot(snapshot_path)

    summary = customer_pilot_opportunity_estimate.estimate_customer_pilot_opportunity(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "estimate_available"
    assert summary.customer_price_areas_detected == ("DK2",)
    assert summary.total_matched_flexible_energy_mwh == 4.0
    assert summary.total_indicative_gross_opportunity_signal_eur == 22.0
    assert summary.candidate_estimates[0]["price_area"] == "DK2"
    assert summary.candidate_estimates[0]["public_risk_score"] == 85


def test_availability_flag_false_excludes_rows_from_numeric_estimate(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [base_row(availability_flag="false")])
    write_snapshot(snapshot_path)

    summary = customer_pilot_opportunity_estimate.estimate_customer_pilot_opportunity(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "matched_with_missing_inputs"
    assert summary.total_matched_flexible_energy_mwh == 0.0
    assert summary.total_indicative_gross_opportunity_signal_eur == 0.0
    assert summary.candidate_estimates[0]["estimate_status"] == (
        "matched_but_not_available_for_customer"
    )


def test_matched_but_missing_flexible_energy_returns_warning_and_status(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [base_row(flexible_energy_mwh="")])
    write_snapshot(snapshot_path)

    summary = customer_pilot_opportunity_estimate.estimate_customer_pilot_opportunity(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "matched_with_missing_inputs"
    assert summary.candidate_estimates[0]["estimate_status"] == (
        "matched_but_missing_flexible_energy"
    )
    assert any("flexible energy" in warning for warning in summary.warnings)


def test_price_context_status_not_available_returns_no_numeric_estimate(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [base_row()])
    write_snapshot(snapshot_path, dk1_price_status="not_available", dk1_signal=None)

    summary = customer_pilot_opportunity_estimate.estimate_customer_pilot_opportunity(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "matched_with_missing_inputs"
    assert summary.total_indicative_gross_opportunity_signal_eur == 0.0
    assert summary.candidate_estimates[0]["public_opportunity_signal_eur_per_mwh"] is None
    assert summary.candidate_estimates[0]["estimate_status"] == (
        "matched_but_price_signal_unavailable"
    )


def test_no_overlap_returns_no_matches(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [base_row(timestamp="2026-02-01T00:00:00+00:00")])
    write_snapshot(snapshot_path)

    summary = customer_pilot_opportunity_estimate.estimate_customer_pilot_opportunity(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "no_matches"
    assert summary.matched_window_count == 0
    assert summary.matched_customer_rows == 0
    assert summary.candidate_estimates == ()


def test_invalid_missing_required_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [{"site_id": "site-a", "flexible_energy_mwh": "1.0"}])
    write_snapshot(snapshot_path)

    summary = customer_pilot_opportunity_estimate.estimate_customer_pilot_opportunity(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "invalid"
    assert any(
        "Required customer columns are missing" in error
        for error in summary.errors
    )
    assert "price_area" in summary.errors[0]


def test_price_area_mismatch_does_not_cross_match_dk1_dk2(
    tmp_path: Path,
) -> None:
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

    summary = customer_pilot_opportunity_estimate.estimate_customer_pilot_opportunity(
        config_for(input_path, snapshot_path)
    )

    assert summary.status == "no_matches"
    assert summary.customer_price_areas_detected == ("DK2",)
    assert summary.candidate_estimates == ()


def test_no_file_db_or_external_writes(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [base_row()])
    write_snapshot(snapshot_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    summary = customer_pilot_opportunity_estimate.estimate_customer_pilot_opportunity(
        config_for(input_path, snapshot_path)
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    source = (
        REPO_ROOT / "scripts" / "customer_pilot_opportunity_estimate.py"
    ).read_text(encoding="utf-8")

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

    summary = customer_pilot_opportunity_estimate.estimate_customer_pilot_opportunity(
        config_for(input_path, snapshot_path)
    )
    customer_pilot_opportunity_estimate.print_summary(summary)
    output = capsys.readouterr().out

    assert "read-only opportunity preview only" in output
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


def test_estimate_content_avoids_forbidden_claim_wording(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, [base_row()])
    write_snapshot(snapshot_path)

    summary = customer_pilot_opportunity_estimate.estimate_customer_pilot_opportunity(
        config_for(input_path, snapshot_path)
    )
    estimate_content = json.dumps(
        {
            "status": summary.status,
            "candidate_estimates": summary.candidate_estimates,
            "warnings": summary.warnings,
        }
    ).lower()

    for forbidden in ("saved", "savings", "profit", "revenue", "guaranteed"):
        assert forbidden not in estimate_content
