"""Synthetic contract checks for the read-only P0.9b.1 audit."""

from __future__ import annotations

import copy
import json
import sys
from datetime import timedelta
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import audit_historical_risk_replay as audit  # noqa: E402


def hourly_payload() -> dict:
    records = []
    for area in audit.AREAS:
        for index in range(168):
            settlement = {field: 1 for field in audit.RENEWABLE_FIELDS}
            settlement.update({"GrossConsumptionMWh": 100, "HydroPowerMWh": 0})
            records.append({
                "price_area": area,
                "hour_utc": audit.hourly._utc_text(audit.hourly.alignment.START + timedelta(hours=index)),
                "price_eur_per_mwh": "25.00",
                "settlement_observed": settlement,
            })
    return {
        "schema_version": audit.EXPECTED_SCHEMA,
        "start_utc": audit.hourly._utc_text(audit.hourly.alignment.START),
        "end_utc_exclusive": audit.hourly._utc_text(audit.hourly.alignment.END),
        "records": records,
    }


def test_complete_observed_mapping_still_blocks_forecast_replay() -> None:
    payload = hourly_payload()
    first = audit.audit_hourly_input(payload)
    assert first == audit.audit_hourly_input(copy.deepcopy(payload))
    assert first["overall_status"] == "BLOCKED"
    for area in first["areas"]:
        assert area["row_count"] == 168
        assert area["observed_historical_input"]["status"] == "PASS"
        assert area["current_rule_engine"]["status"] == "BLOCKED"
        assert area["forecast_issuance"]["status"] == "BLOCKED"
        assert "look-ahead bias" in " ".join(area["forecast_issuance"]["reasons"])


def test_missing_null_and_invalid_required_fields_block_only_affected_area() -> None:
    payload = hourly_payload()
    payload["records"][0]["settlement_observed"].pop("OnshoreWindGe50kW_MWh")
    payload["records"][1]["settlement_observed"]["GrossConsumptionMWh"] = None
    payload["records"][2]["settlement_observed"]["SolarPowerGe40kW_MWh"] = "NaN"
    report = audit.audit_hourly_input(payload)
    dk1, dk2 = report["areas"]
    assert dk1["observed_historical_input"]["status"] == "BLOCKED"
    assert dk2["observed_historical_input"]["status"] == "PASS"
    assert dk1["source_field_coverage"]["OnshoreWindGe50kW_MWh"]["absent"] == 1
    assert dk1["source_field_coverage"]["GrossConsumptionMWh"]["null"] == 1
    reasons = " ".join(dk1["observed_historical_input"]["reasons"])
    assert "OnshoreWindGe50kW_MWh" in reasons
    assert "GrossConsumptionMWh" in reasons
    assert "invalid values in 1 rows" in reasons


def test_missing_hydro_price_and_duplicate_hour_fail_closed() -> None:
    payload = hourly_payload()
    payload["records"][0]["settlement_observed"].pop("HydroPowerMWh")
    payload["records"][0]["price_eur_per_mwh"] = None
    payload["records"][1]["hour_utc"] = payload["records"][0]["hour_utc"]
    report = audit.audit_hourly_input(payload)
    reasons = " ".join(report["areas"][0]["observed_historical_input"]["reasons"])
    assert "hydro/other-renewable" in reasons
    assert "price_eur_per_mwh" in reasons
    assert "UTC hours" in reasons


def test_malformed_settlement_and_incompatible_price_field_fail_closed() -> None:
    payload = hourly_payload()
    payload["records"][0]["settlement_observed"] = []
    payload["records"][1]["hour_utc"] = ["invalid"]
    payload["records"][2].pop("price_eur_per_mwh")
    payload["records"][2]["price_dkk_per_mwh"] = 100
    report = audit.audit_hourly_input(payload)
    reasons = " ".join(report["areas"][0]["observed_historical_input"]["reasons"])
    assert "settlement_observed" in reasons
    assert "hour_utc" in reasons
    assert "price_eur_per_mwh" in reasons
    assert report["overall_status"] == "BLOCKED"


def test_current_engine_contract_drift_is_reported(monkeypatch) -> None:
    payload = hourly_payload()
    monkeypatch.setattr(audit.rule_engine, "NUMERIC_FIELDS", set())
    report = audit.audit_hourly_input(payload)
    assert any(
        "scoring fields changed" in reason
        for reason in report["areas"][0]["current_rule_engine"]["reasons"]
    )
    assert report["areas"][0]["observed_historical_input"]["status"] == "PASS"


def test_current_engine_required_fields_are_checked_with_its_validator(monkeypatch) -> None:
    monkeypatch.setattr(audit.rule_engine, "_validate_input", lambda value: None)
    report = audit.audit_hourly_input(hourly_payload())
    reasons = " ".join(report["areas"][0]["current_rule_engine"]["reasons"])
    assert "no longer requires price_area" in reasons
    assert "no longer requires timestamp_utc" in reasons


def test_valid_archive_readiness_block_uses_exit_one(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(audit.hourly, "build_hourly_input", lambda root: hourly_payload())
    assert audit.main(["--archive-root", str(tmp_path)]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["overall_status"] == "BLOCKED"
    assert "execution_error" not in output


def test_bad_envelope_and_unreadable_archive_report_both_areas(tmp_path: Path, capsys) -> None:
    report = audit.audit_hourly_input({"records": [{"price_area": "SE3"}]})
    assert all(area["observed_historical_input"]["status"] == "BLOCKED" for area in report["areas"])
    assert audit.main(["--archive-root", str(tmp_path)]) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["overall_status"] == "BLOCKED"
    assert "archive verification/build failed" in output["execution_error"]


def test_unexpected_audit_error_uses_exit_two(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(audit.hourly, "build_hourly_input", lambda root: hourly_payload())

    def fail(_payload):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(audit, "audit_hourly_input", fail)
    assert audit.main(["--archive-root", str(tmp_path)]) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["overall_status"] == "BLOCKED"
    assert "readiness audit failed: RuntimeError" in output["execution_error"]
