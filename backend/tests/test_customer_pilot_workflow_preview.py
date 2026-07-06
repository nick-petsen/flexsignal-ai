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


customer_pilot_workflow_preview = load_script_module(
    "customer_pilot_workflow_preview.py"
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
                    "duration_hours": 3,
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
                    "duration_hours": 3,
                    "score": 85,
                    "level": "high",
                    "price_context_status": dk2_price_status,
                    "opportunity_signal_eur_per_mwh": dk2_signal,
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


def config_for(input_path: Path, snapshot_path: Path, **overrides: object):
    values = {
        "input_path": input_path,
        "snapshot_path": snapshot_path,
        "customer_type": "common",
        "price_area": None,
        "dry_run": True,
    }
    values.update(overrides)
    return customer_pilot_workflow_preview.CustomerPilotWorkflowPreviewConfig(
        **values
    )


def parse_printed_json(output: str) -> dict[str, object]:
    _, payload = output.split("\n", 1)
    return json.loads(payload)


def test_valid_dk1_workflow_with_estimate_available_is_ready_for_human_review(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    summary = customer_pilot_workflow_preview.run_customer_pilot_workflow_preview(
        config_for(input_path, snapshot_path)
    )

    assert summary.workflow_status == "ready_for_human_review"
    assert summary.validation_status == "valid"
    assert summary.signal_match_status == "matched"
    assert summary.opportunity_estimate_status == "estimate_available"
    assert summary.total_customer_rows == 24
    assert summary.matched_window_count == 1
    assert summary.matched_customer_rows == 1
    assert summary.total_matched_flexible_energy_mwh == 2.0
    assert summary.total_indicative_gross_opportunity_signal_eur == 16.0
    assert summary.top_candidate_windows[0]["price_area"] == "DK1"


def test_valid_dk2_workflow_with_estimate_available_is_ready_for_human_review(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(
        input_path,
        valid_rows(
            price_area="DK2",
            matching_timestamp="2026-04-24T22:00:00+00:00",
            flexible_energy_mwh="4.0",
        ),
    )
    write_snapshot(snapshot_path)

    summary = customer_pilot_workflow_preview.run_customer_pilot_workflow_preview(
        config_for(input_path, snapshot_path)
    )

    assert summary.workflow_status == "ready_for_human_review"
    assert summary.validation_status == "valid"
    assert summary.signal_match_status == "matched"
    assert summary.opportunity_estimate_status == "estimate_available"
    assert summary.total_matched_flexible_energy_mwh == 4.0
    assert summary.total_indicative_gross_opportunity_signal_eur == 22.0
    assert summary.top_candidate_windows[0]["price_area"] == "DK2"


def test_valid_csv_with_warnings_becomes_ready_with_warnings(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    summary = customer_pilot_workflow_preview.run_customer_pilot_workflow_preview(
        config_for(input_path, snapshot_path, customer_type="producer")
    )

    assert summary.workflow_status == "ready_with_warnings"
    assert summary.validation_status == "valid_with_warnings"
    assert any("validation:" in warning for warning in summary.warnings)
    assert summary.opportunity_estimate_status == "estimate_available"


def test_no_overlap_becomes_no_matches(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(
        input_path,
        valid_rows(matching_timestamp="2026-02-01T00:00:00+00:00"),
    )
    write_snapshot(snapshot_path)

    summary = customer_pilot_workflow_preview.run_customer_pilot_workflow_preview(
        config_for(input_path, snapshot_path)
    )

    assert summary.workflow_status == "no_matches"
    assert summary.signal_match_status == "no_matches"
    assert summary.opportunity_estimate_status == "no_matches"
    assert summary.matched_window_count == 0
    assert summary.matched_customer_rows == 0


def test_invalid_csv_becomes_invalid_and_main_exits_1(
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

    exit_code = customer_pilot_workflow_preview.main()
    output = parse_printed_json(capsys.readouterr().out)

    assert exit_code == 1
    assert output["workflow_status"] == "invalid"
    assert output["validation_status"] == "invalid"
    assert output["signal_match_status"] == "not_run"
    assert output["opportunity_estimate_status"] == "not_run"


def test_availability_false_excludes_numeric_estimate(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows(availability_flag="false"))
    write_snapshot(snapshot_path)

    summary = customer_pilot_workflow_preview.run_customer_pilot_workflow_preview(
        config_for(input_path, snapshot_path)
    )

    assert summary.workflow_status == "ready_with_warnings"
    assert summary.opportunity_estimate_status == "matched_with_missing_inputs"
    assert summary.total_matched_flexible_energy_mwh == 0.0
    assert summary.total_indicative_gross_opportunity_signal_eur == 0.0
    assert summary.top_candidate_windows[0]["estimate_status"] == (
        "matched_but_not_available_for_customer"
    )


def test_price_area_mismatch_does_not_cross_match_dk1_dk2(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(
        input_path,
        valid_rows(
            price_area="DK2",
            matching_timestamp="2026-04-04T22:00:00+00:00",
        ),
    )
    write_snapshot(snapshot_path)

    summary = customer_pilot_workflow_preview.run_customer_pilot_workflow_preview(
        config_for(input_path, snapshot_path)
    )

    assert summary.workflow_status == "no_matches"
    assert summary.signal_match_status == "no_matches"
    assert summary.top_candidate_windows == ()


def test_no_file_db_or_external_writes(tmp_path: Path) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    summary = customer_pilot_workflow_preview.run_customer_pilot_workflow_preview(
        config_for(input_path, snapshot_path)
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    source = (
        REPO_ROOT / "scripts" / "customer_pilot_workflow_preview.py"
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
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    summary = customer_pilot_workflow_preview.run_customer_pilot_workflow_preview(
        config_for(input_path, snapshot_path)
    )
    customer_pilot_workflow_preview.print_summary(summary)
    output = capsys.readouterr().out

    assert "read-only workflow preview only" in output
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
    assert "customer data must not be committed to git" in output


def test_non_boundary_content_avoids_forbidden_claim_wording(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "customer.csv"
    snapshot_path = tmp_path / "snapshot.json"
    write_csv(input_path, valid_rows())
    write_snapshot(snapshot_path)

    summary = customer_pilot_workflow_preview.run_customer_pilot_workflow_preview(
        config_for(input_path, snapshot_path)
    )
    non_boundary_content = json.dumps(
        {
            "workflow_status": summary.workflow_status,
            "top_candidate_windows": summary.top_candidate_windows,
            "warnings": summary.warnings,
            "next_human_review_steps": summary.next_human_review_steps,
        }
    ).lower()

    for forbidden in ("saved", "savings", "profit", "revenue", "guaranteed"):
        assert forbidden not in non_boundary_content
