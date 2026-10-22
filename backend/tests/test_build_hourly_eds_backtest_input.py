"""Synthetic tests for the offline hourly EDS input builder."""

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
SCRIPT = SCRIPTS / "build_hourly_eds_backtest_input.py"
spec = importlib.util.spec_from_file_location("build_hourly_eds_backtest_input", SCRIPT)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


def save_archive(root: Path, archive_id: str, dataset: str, area: str, records: list[dict]) -> None:
    directory = root / archive_id
    directory.mkdir(parents=True, exist_ok=True)
    raw = json.dumps({"records": records}, separators=(",", ":")).encode()
    (directory / "INPUT.json").write_bytes(raw)
    (directory / "MANIFEST.json").write_text(json.dumps({
        "input_file": "INPUT.json",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "input_byte_size": len(raw),
        "record_count": len(records),
        "dataset": dataset,
        "price_area": area,
    }))


def archives(tmp_path: Path) -> Path:
    root = tmp_path / "archives"
    for archive_id, dataset, area, field, minutes in builder.alignment.ARCHIVES:
        records = []
        for index in range(7 * 24 * 60 // minutes):
            stamp = builder.alignment.START + timedelta(minutes=index * minutes)
            record = {"PriceArea": area, field: stamp.isoformat()}
            if dataset == "DayAheadPrices":
                record["DayAheadPriceEUR"] = (
                    [0.1, 0.2, 0.3, 0.4][index % 4] if area == "DK1" else
                    [10.01, 10.02, 10.03, 10.04][index % 4]
                )
                record["DayAheadPriceDKK"] = (
                    [0.01, -0.02, 0.03, -0.04][index % 4] if area == "DK1" else
                    [100.01, 100.02, 100.03, 100.04][index % 4]
                )
            else:
                record["GrossConsumptionMWh"] = 100 + index if area == "DK1" else 200 + index
                record["CentralPowerMWh"] = 50 + index
                record["LocalPowerMWh"] = 25 + index
                record["ExchangeNO_MWh"] = None
                if area == "DK1":
                    record["OnshoreWindGe50kW_MWh"] = None
            records.append(record)
        save_archive(root, archive_id, dataset, area, records)
    return root


def change_records(root: Path, archive_index: int, change) -> None:
    archive_id, dataset, area, _, _ = builder.alignment.ARCHIVES[archive_index]
    records = json.loads((root / archive_id / "INPUT.json").read_text())["records"]
    change(records)
    directory = root / archive_id
    (directory / "INPUT.json").unlink()
    (directory / "MANIFEST.json").unlink()
    directory.rmdir()
    save_archive(root, archive_id, dataset, area, records)


def test_hourly_mean_area_join_and_observed_fields(tmp_path: Path) -> None:
    payload = builder.build_hourly_input(archives(tmp_path))
    rows = payload["records"]
    assert len(rows) == 336
    assert rows[0] == {
        "price_area": "DK1", "hour_utc": "2026-04-01T00:00:00Z",
        "price_eur_per_mwh": "0.25",
        "price_dkk_per_mwh": "-0.005",
        "settlement_observed": {
            "GrossConsumptionMWh": 100, "CentralPowerMWh": 50,
            "LocalPowerMWh": 25, "ExchangeNO_MWh": None,
            "OnshoreWindGe50kW_MWh": None,
        },
    }
    assert rows[167]["hour_utc"] == "2026-04-07T23:00:00Z"
    assert rows[168] == {
        "price_area": "DK2", "hour_utc": "2026-04-01T00:00:00Z",
        "price_eur_per_mwh": "10.025",
        "price_dkk_per_mwh": "100.025",
        "settlement_observed": {
            "GrossConsumptionMWh": 200, "CentralPowerMWh": 50,
            "LocalPowerMWh": 25, "ExchangeNO_MWh": None,
        },
    }


def test_offset_timestamp_at_utc_boundary(tmp_path: Path) -> None:
    root = archives(tmp_path)
    change_records(root, 0, lambda rows: rows[0].__setitem__("TimeUTC", "2026-04-01T02:00:00+02:00"))
    change_records(root, 2, lambda rows: rows[-1].__setitem__("HourUTC", "2026-04-08T01:00:00+02:00"))
    rows = builder.build_hourly_input(root)["records"]
    assert rows[0]["hour_utc"] == "2026-04-01T00:00:00Z"
    assert rows[167]["hour_utc"] == "2026-04-07T23:00:00Z"


@pytest.mark.parametrize("archive_index,change,expected", [
    (0, lambda rows: rows.pop(), "missing timestamps"),
    (0, lambda rows: rows.__setitem__(1, rows[0].copy()), "duplicate timestamps"),
    (2, lambda rows: rows.pop(), "missing timestamps"),
    (0, lambda rows: rows[0].__setitem__("TimeUTC", "2026-04-01T00:05:00Z"), "misaligned timestamps"),
    (0, lambda rows: rows[0].pop("DayAheadPriceEUR"), "missing or invalid DayAheadPriceEUR"),
    (0, lambda rows: rows[0].__setitem__("DayAheadPriceEUR", None), "missing or invalid DayAheadPriceEUR"),
    (0, lambda rows: rows[0].pop("DayAheadPriceDKK"), "missing or invalid DayAheadPriceDKK"),
    (1, lambda rows: rows[0].pop("DayAheadPriceDKK"), "missing or invalid DayAheadPriceDKK"),
])
def test_missing_duplicate_alignment_and_price_rejected(
    tmp_path: Path, archive_index: int, change, expected: str,
) -> None:
    root = archives(tmp_path)
    change_records(root, archive_index, change)
    with pytest.raises(builder.HourlyInputError, match=expected):
        builder.build_hourly_input(root)


@pytest.mark.parametrize("archive_index", [0, 1])
@pytest.mark.parametrize("bad_value", [None, "NaN", "Infinity", "1.2", True, {}, []])
def test_invalid_dkk_price_rejected(tmp_path: Path, archive_index: int, bad_value) -> None:
    root = archives(tmp_path)
    change_records(root, archive_index, lambda rows: rows[0].__setitem__("DayAheadPriceDKK", bad_value))
    with pytest.raises(builder.HourlyInputError, match="missing or invalid DayAheadPriceDKK"):
        builder.build_hourly_input(root)


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_dkk_json_constant_rejected(tmp_path: Path, bad_value: float) -> None:
    root = archives(tmp_path)
    change_records(root, 0, lambda rows: rows[0].__setitem__("DayAheadPriceDKK", bad_value))
    with pytest.raises(builder.HourlyInputError, match="cannot read valid archive"):
        builder.build_hourly_input(root)


def test_missing_archive_and_corrupted_bytes_rejected(tmp_path: Path) -> None:
    root = archives(tmp_path)
    archive_id = builder.alignment.ARCHIVES[0][0]
    input_path = root / archive_id / "INPUT.json"
    input_path.write_bytes(input_path.read_bytes() + b" ")
    with pytest.raises(builder.HourlyInputError, match="SHA-256 mismatch"):
        builder.build_hourly_input(root)
    input_path.unlink()
    with pytest.raises(builder.HourlyInputError, match="missing MANIFEST.json or INPUT.json"):
        builder.build_hourly_input(root)


def test_corrupted_json_rejected_even_with_updated_hash(tmp_path: Path) -> None:
    root = archives(tmp_path)
    directory = root / builder.alignment.ARCHIVES[0][0]
    input_path = directory / "INPUT.json"
    raw = input_path.read_bytes().replace(
        b'"DayAheadPriceEUR":0.1',
        b'"DayAheadPriceEUR":0.1,"DayAheadPriceEUR":0.1',
        1,
    )
    input_path.write_bytes(raw)
    manifest_path = directory / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["input_sha256"] = hashlib.sha256(raw).hexdigest()
    manifest["input_byte_size"] = len(raw)
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(builder.HourlyInputError, match="cannot read valid archive: ValueError"):
        builder.build_hourly_input(root)


def test_repeated_cli_output_is_byte_identical(tmp_path: Path, capsys) -> None:
    root = archives(tmp_path)
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    assert builder.main(["--archive-root", str(root), "--output", str(first)]) == 0
    summary_a = capsys.readouterr().out
    assert builder.main(["--archive-root", str(root), "--output", str(second)]) == 0
    summary_b = capsys.readouterr().out
    assert first.read_bytes() == second.read_bytes()
    assert "DK1=168 DK2=168 total=336" in summary_a
    assert summary_a.split("sha256=")[1].split(";")[0] == summary_b.split("sha256=")[1].split(";")[0]
    assert json.loads(first.read_text())["records"][0]["price_eur_per_mwh"] == "0.25"
    assert json.loads(first.read_text())["records"][0]["price_dkk_per_mwh"] == "-0.005"


def test_output_cannot_change_archive(tmp_path: Path, capsys) -> None:
    root = archives(tmp_path)
    assert builder.main(["--archive-root", str(root), "--output", str(root / "out.json")]) == 1
    assert "outside the read-only archive root" in capsys.readouterr().err
    assert not (root / "out.json").exists()
