"""Offline tests for manually selected historical price comparisons."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import timedelta
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "manual_flexibility_price_scenario", SCRIPTS / "manual_flexibility_price_scenario.py"
)
assert spec and spec.loader
scenario = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = scenario
spec.loader.exec_module(scenario)


def _write_area(root: Path, area: str, prices: dict[int, object] | None = None) -> None:
    archive_id = next(item[0] for item in scenario.baseline.alignment.ARCHIVES if item[2] == area)
    directory = root / archive_id
    directory.mkdir(parents=True, exist_ok=True)
    records = [
        {
            "PriceArea": area,
            "TimeUTC": (scenario.baseline.alignment.START + timedelta(minutes=15 * index)).isoformat(),
            "DayAheadPriceDKK": (prices or {}).get(index, 10),
        }
        for index in range(7 * 24 * 4)
    ]
    raw = json.dumps({"records": records}, separators=(",", ":")).encode()
    (directory / "INPUT.json").write_bytes(raw)
    (directory / "MANIFEST.json").write_text(json.dumps({
        "input_file": "INPUT.json",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "input_byte_size": len(raw),
        "record_count": len(records),
        "dataset": "DayAheadPrices",
        "price_area": area,
    }))


@pytest.fixture
def archives(tmp_path: Path) -> Path:
    root = tmp_path / "archives"
    _write_area(root, "DK1", {0: 100.125, 1: 0, 2: -20.25, 3: 100.125})
    _write_area(root, "DK2", {0: 999, 1: -999})
    return root


def _args(root: Path, **overrides: str) -> dict:
    return {
        "archive_root": root,
        "price_area": "DK1",
        "original_utc": "2026-04-01T00:00:00Z",
        "alternative_utc": "2026-04-01T00:15:00Z",
        "energy_mwh": "0.125",
        "max_flexible_power_mw": "0.5",
        **overrides,
    }


def _constraints(**overrides: str) -> dict:
    return {
        "assess_operating_constraints": True,
        "max_shiftable_energy_mwh": "0.125",
        "max_absolute_shift_minutes": "15",
        "allowed_destination_start_utc": "2026-04-01T00:15:00Z",
        "allowed_destination_end_utc_exclusive": "2026-04-01T00:30:00Z",
        **overrides,
    }


@pytest.mark.parametrize("original,alternative,expected", [
    ("00:00", "00:15", "12.515625"),
    ("00:00", "00:45", "0.000000"),
    ("00:30", "00:00", "-15.046875"),
    ("00:15", "00:30", "2.53125"),
])
def test_signed_exact_gross_difference(archives: Path, original: str, alternative: str, expected: str) -> None:
    result = scenario.evaluate_scenario(**_args(
        archives,
        original_utc=f"2026-04-01T{original}:00Z",
        alternative_utc=f"2026-04-01T{alternative}:00Z",
    ))
    assert result["indicative_spot_price_gross_difference_dkk"] == expected
    assert result["method"]["source_field"] == "DayAheadPriceDKK"


def test_power_conversion_and_insufficient_declared_power(archives: Path) -> None:
    sufficient = scenario.evaluate_scenario(**_args(archives))
    assert sufficient["required_average_power_mw"] == "0.500"
    assert sufficient["power_check"] == {"within_declared_maximum": True, "interval_minutes": 15}
    insufficient = scenario.evaluate_scenario(**_args(archives, max_flexible_power_mw="0.499"))
    assert insufficient["power_check"]["within_declared_maximum"] is False
    assert insufficient["indicative_spot_price_gross_difference_dkk"] == "12.515625"


def test_declared_constraints_pass_at_exact_boundaries(archives: Path) -> None:
    result = scenario.evaluate_scenario(**_args(archives, **_constraints()))
    assessment = result["operating_constraints_assessment"]
    assert assessment["status"] == "PASS"
    assert assessment["reason_code"] == "ALL_DECLARED_CHECKS_PASS"
    assert assessment["observed_absolute_shift_minutes"] == "15"
    assert {name: check["status"] for name, check in assessment["checks"].items()} == {
        "energy_limit": "PASS", "absolute_shift_limit": "PASS",
        "destination_window": "PASS", "flexible_power_limit": "PASS",
    }
    assert result["power_check"]["within_declared_maximum"] is True
    assert "no operational feasibility determination" in assessment["scope"]


@pytest.mark.parametrize("overrides,failed_check,reason", [
    ({"max_shiftable_energy_mwh": "0.124"}, "energy_limit", "ENERGY_EXCEEDS_MAXIMUM"),
    ({"max_absolute_shift_minutes": "14.999"}, "absolute_shift_limit", "SHIFT_EXCEEDS_MAXIMUM"),
    ({"allowed_destination_start_utc": "2026-04-01T00:15:01Z"},
     "destination_window", "DESTINATION_OUTSIDE_WINDOW"),
    ({"allowed_destination_end_utc_exclusive": "2026-04-01T00:29:59Z"},
     "destination_window", "DESTINATION_OUTSIDE_WINDOW"),
    ({"max_flexible_power_mw": "0.499"}, "flexible_power_limit", "POWER_EXCEEDS_MAXIMUM"),
])
def test_declared_constraint_failures(archives: Path, overrides: dict, failed_check: str, reason: str) -> None:
    assessment = scenario.evaluate_scenario(**_args(archives, **_constraints(**overrides)))[
        "operating_constraints_assessment"
    ]
    assert assessment["status"] == "FAIL"
    assert assessment["reason_code"] == "DECLARED_CHECKS_FAILED"
    assert assessment["checks"][failed_check] == {"status": "FAIL", "reason_code": reason}
    assert sum(check["status"] == "FAIL" for check in assessment["checks"].values()) == 1


def test_absolute_shift_in_either_direction_and_unaligned_window_edges(archives: Path) -> None:
    result = scenario.evaluate_scenario(**_args(
        archives,
        original_utc="2026-04-01T00:30:00Z",
        alternative_utc="2026-04-01T00:15:00Z",
        **_constraints(allowed_destination_start_utc="2026-04-01T00:14:59Z",
                       allowed_destination_end_utc_exclusive="2026-04-01T00:30:01Z"),
    ))
    assert result["operating_constraints_assessment"]["status"] == "PASS"
    assert result["indicative_spot_price_gross_difference_dkk"] == "-2.53125"


def test_assessment_not_enabled_preserves_p1_0a_results(archives: Path) -> None:
    result = scenario.evaluate_scenario(**_args(archives))
    assert result["operating_constraints_assessment"]["status"] == "NOT_ASSESSED"
    assert {check["status"] for check in result["operating_constraints_assessment"]["checks"].values()} == {
        "NOT_ASSESSED"
    }
    assert result["indicative_spot_price_gross_difference_dkk"] == "12.515625"
    assert result["power_check"] == {"within_declared_maximum": True, "interval_minutes": 15}


@pytest.mark.parametrize("overrides,match", [
    ({"max_shiftable_energy_mwh": None}, "assessment requires"),
    ({"max_absolute_shift_minutes": None}, "assessment requires"),
    ({"allowed_destination_start_utc": None}, "assessment requires"),
    ({"allowed_destination_end_utc_exclusive": None}, "assessment requires"),
    ({"max_shiftable_energy_mwh": "0"}, "max_shiftable_energy_mwh"),
    ({"max_shiftable_energy_mwh": "NaN"}, "max_shiftable_energy_mwh"),
    ({"max_absolute_shift_minutes": "-15"}, "max_absolute_shift_minutes"),
    ({"max_absolute_shift_minutes": "Infinity"}, "max_absolute_shift_minutes"),
    ({"allowed_destination_start_utc": "2026-04-01T00:15:00+02:00"}, "explicit UTC"),
    ({"allowed_destination_end_utc_exclusive": "2026-02-30T00:30:00Z"}, "invalid"),
    ({"allowed_destination_end_utc_exclusive": "2026-04-01T00:15:00Z"}, "start must precede end"),
    ({"allowed_destination_end_utc_exclusive": "2026-04-01T00:00:00Z"}, "start must precede end"),
])
def test_incomplete_or_invalid_constraint_inputs(archives: Path, overrides: dict, match: str) -> None:
    with pytest.raises(scenario.ScenarioError, match=match):
        scenario.evaluate_scenario(**_args(archives, **_constraints(**overrides)))


def test_constraint_input_requires_explicit_enable(archives: Path) -> None:
    with pytest.raises(scenario.ScenarioError, match="require --assess-operating-constraints"):
        scenario.evaluate_scenario(**_args(archives, max_shiftable_energy_mwh="0.125"))


@pytest.mark.parametrize("overrides,match", [
    ({"price_area": "SE1"}, "price_area"),
    ({"alternative_price_area": "DK2"}, "areas must match"),
    ({"alternative_utc": "2026-04-01T00:00:00Z"}, "distinct"),
    ({"original_utc": "2026-04-01T00:05:00Z"}, "15-minute"),
    ({"original_utc": "2026-04-01T00:00:01Z"}, "15-minute"),
    ({"original_utc": "2026-04-01T00:00:00+02:00"}, "explicit UTC"),
    ({"original_utc": "2026-02-30T00:00:00Z"}, "invalid"),
    ({"alternative_utc": "2026-04-08T00:00:00Z"}, "missing"),
    ({"energy_mwh": "0"}, "energy_mwh"),
    ({"energy_mwh": "-1"}, "energy_mwh"),
    ({"energy_mwh": "NaN"}, "energy_mwh"),
    ({"energy_mwh": "1e3"}, "energy_mwh"),
    ({"max_flexible_power_mw": "0"}, "max_flexible_power_mw"),
    ({"max_flexible_power_mw": "Infinity"}, "max_flexible_power_mw"),
])
def test_invalid_manual_inputs_rejected(archives: Path, overrides: dict, match: str) -> None:
    with pytest.raises(scenario.ScenarioError, match=match):
        scenario.evaluate_scenario(**_args(archives, **overrides))


def test_missing_and_corrupted_archive_rejected(archives: Path) -> None:
    archive_id = scenario.baseline.alignment.ARCHIVES[0][0]
    input_path = archives / archive_id / "INPUT.json"
    input_path.write_bytes(input_path.read_bytes() + b" ")
    with pytest.raises(scenario.ScenarioError, match="SHA-256 mismatch"):
        scenario.evaluate_scenario(**_args(archives))
    input_path.unlink()
    with pytest.raises(scenario.ScenarioError, match="missing MANIFEST.json or INPUT.json"):
        scenario.evaluate_scenario(**_args(archives))


def test_invalid_price_rejected_even_outside_selected_quarters(archives: Path) -> None:
    _write_area(archives, "DK2", {42: "bad"})
    with pytest.raises(scenario.ScenarioError, match="missing or invalid DayAheadPriceDKK"):
        scenario.evaluate_scenario(**_args(archives))


def test_repeated_cli_output_is_identical_and_machine_readable(archives: Path, capsys) -> None:
    argv = [
        "--archive-root", str(archives), "--price-area", "DK1",
        "--original-utc", "2026-04-01T00:00:00Z",
        "--alternative-utc", "2026-04-01T00:15:00Z",
        "--energy-mwh", "0.125", "--max-flexible-power-mw", "0.5",
    ]
    assert scenario.main(argv) == 0
    first = capsys.readouterr().out
    assert scenario.main(argv) == 0
    assert first == capsys.readouterr().out
    parsed = json.loads(first)
    assert parsed["original_price_dkk_per_mwh"] == "100.125"
    assert parsed["alternative_price_dkk_per_mwh"] == "0"
    assert parsed["method"]["selection"].startswith("original and alternative intervals manually")


def test_repeated_assessment_cli_output_is_identical(archives: Path, capsys) -> None:
    argv = [
        "--archive-root", str(archives), "--price-area", "DK1",
        "--original-utc", "2026-04-01T00:00:00Z",
        "--alternative-utc", "2026-04-01T00:15:00Z",
        "--energy-mwh", "0.125", "--max-flexible-power-mw", "0.5",
        "--assess-operating-constraints", "--max-shiftable-energy-mwh", "0.125",
        "--max-absolute-shift-minutes", "15",
        "--allowed-destination-start-utc", "2026-04-01T00:15:00Z",
        "--allowed-destination-end-utc-exclusive", "2026-04-01T00:30:00Z",
    ]
    assert scenario.main(argv) == 0
    first = capsys.readouterr().out
    assert scenario.main(argv) == 0
    assert first == capsys.readouterr().out
    assert json.loads(first)["operating_constraints_assessment"]["status"] == "PASS"
