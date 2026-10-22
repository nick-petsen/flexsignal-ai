"""Synthetic tests for the offline observed-price baseline."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "historical_negative_price_baseline.py"
spec = importlib.util.spec_from_file_location("historical_negative_price_baseline", SCRIPT)
assert spec and spec.loader
baseline = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = baseline
spec.loader.exec_module(baseline)


def save_archive(root: Path, area: str, prices: dict[int, object] | None = None) -> None:
    archive_id = next(item[0] for item in baseline.alignment.ARCHIVES if item[2] == area)
    directory = root / archive_id
    directory.mkdir(parents=True, exist_ok=True)
    records = []
    for index in range(7 * 24 * 4):
        stamp = baseline.alignment.START + timedelta(minutes=15 * index)
        records.append({
            "PriceArea": area,
            "TimeUTC": stamp.isoformat(),
            "DayAheadPriceDKK": (prices or {}).get(index, 10),
        })
    write_records(root, area, records)


def write_records(root: Path, area: str, records: list[dict]) -> None:
    archive_id = next(item[0] for item in baseline.alignment.ARCHIVES if item[2] == area)
    directory = root / archive_id
    directory.mkdir(parents=True, exist_ok=True)
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


def archives(tmp_path: Path, dk1: dict[int, object] | None = None, dk2: dict[int, object] | None = None) -> Path:
    root = tmp_path / "archives"
    save_archive(root, "DK1", dk1)
    save_archive(root, "DK2", dk2)
    return root


def change_records(root: Path, area: str, change) -> None:
    archive_id = next(item[0] for item in baseline.alignment.ARCHIVES if item[2] == area)
    records = json.loads((root / archive_id / "INPUT.json").read_text())["records"]
    change(records)
    write_records(root, area, records)


def test_strict_negative_rule_windows_and_area_separation(tmp_path: Path) -> None:
    root = archives(tmp_path, {0: -2, 1: -1, 2: 0, 3: 3, 4: -4}, {1: -5})
    dk1, dk2 = baseline.build_baseline(root)["areas"]
    assert (dk1["interval_count"], dk1["negative_interval_count"], dk1["zero_interval_count"],
            dk1["negative_window_count"], dk1["negative_duration_minutes"]) == (672, 3, 1, 2, 45)
    assert dk1["windows"] == [
        {
            "start_utc": "2026-04-01T00:00:00Z", "end_utc_exclusive": "2026-04-01T00:30:00Z",
            "interval_count": 2, "duration_minutes": 30,
            "observed_price_dkk_per_mwh": {"minimum": "-2", "maximum": "-1", "mean": "-1.500000"},
        },
        {
            "start_utc": "2026-04-01T01:00:00Z", "end_utc_exclusive": "2026-04-01T01:15:00Z",
            "interval_count": 1, "duration_minutes": 15,
            "observed_price_dkk_per_mwh": {"minimum": "-4", "maximum": "-4", "mean": "-4.000000"},
        },
    ]
    assert dk2["negative_interval_count"] == 1
    assert dk2["windows"][0]["start_utc"] == "2026-04-01T00:15:00Z"
    assert dk1["negative_observed_price_dkk_per_mwh"] == {
        "minimum": "-4", "maximum": "-1", "mean": "-2.333333",
    }


def test_utc_day_boundary_and_last_exclusive_end(tmp_path: Path) -> None:
    root = archives(tmp_path, {95: -1, 96: -2, 671: -3})
    payload = baseline.build_baseline(root)
    windows = payload["areas"][0]["windows"]
    assert [(row["start_utc"], row["end_utc_exclusive"]) for row in windows] == [
        ("2026-04-01T23:45:00Z", "2026-04-02T00:15:00Z"),
        ("2026-04-07T23:45:00Z", "2026-04-08T00:00:00Z"),
    ]
    assert payload["data_period"]["end_utc_exclusive"] == "2026-04-08T00:00:00Z"


def test_gap_splits_windows_and_duplicate_is_rejected() -> None:
    start = datetime(2026, 4, 1, tzinfo=timezone.utc)
    observations = [(start, Decimal("-1")), (start + timedelta(minutes=30), Decimal("-2"))]
    assert [row["duration_minutes"] for row in baseline.group_negative_windows(observations)] == [15, 15]
    with pytest.raises(baseline.PriceBaselineError, match="duplicate"):
        baseline.group_negative_windows(observations + [observations[-1]])


@pytest.mark.parametrize("change,expected", [
    (lambda rows: rows.pop(1), "missing timestamps"),
    (lambda rows: rows.__setitem__(1, rows[0].copy()), "duplicate timestamps"),
    (lambda rows: rows[0].__setitem__("TimeUTC", "2026-04-01T00:05:00Z"), "misaligned timestamps"),
    (lambda rows: rows[0].__setitem__("PriceArea", "DK2"), "invalid PriceArea"),
    (lambda rows: rows[0].pop("DayAheadPriceDKK"), "missing or invalid DayAheadPriceDKK"),
    (lambda rows: rows[0].__setitem__("DayAheadPriceDKK", "-1"), "missing or invalid DayAheadPriceDKK"),
    (lambda rows: rows[0].__setitem__("DayAheadPriceDKK", True), "missing or invalid DayAheadPriceDKK"),
])
def test_missing_duplicate_and_malformed_required_input_rejected(tmp_path: Path, change, expected: str) -> None:
    root = archives(tmp_path)
    change_records(root, "DK1", change)
    with pytest.raises(baseline.PriceBaselineError, match=expected):
        baseline.build_baseline(root)


def test_corrupted_archive_and_missing_area_rejected(tmp_path: Path) -> None:
    root = archives(tmp_path)
    archive_id = baseline.alignment.ARCHIVES[0][0]
    input_path = root / archive_id / "INPUT.json"
    input_path.write_bytes(input_path.read_bytes() + b" ")
    with pytest.raises(baseline.PriceBaselineError, match="SHA-256 mismatch"):
        baseline.build_baseline(root)
    input_path.unlink()
    with pytest.raises(baseline.PriceBaselineError, match="missing MANIFEST.json or INPUT.json"):
        baseline.build_baseline(root)


def test_duplicate_json_key_rejected_with_updated_hash(tmp_path: Path) -> None:
    root = archives(tmp_path)
    archive_id = baseline.alignment.ARCHIVES[0][0]
    directory = root / archive_id
    raw = (directory / "INPUT.json").read_bytes().replace(
        b'"DayAheadPriceDKK":10', b'"DayAheadPriceDKK":10,"DayAheadPriceDKK":-1', 1,
    )
    (directory / "INPUT.json").write_bytes(raw)
    manifest = json.loads((directory / "MANIFEST.json").read_text())
    manifest["input_sha256"] = hashlib.sha256(raw).hexdigest()
    manifest["input_byte_size"] = len(raw)
    (directory / "MANIFEST.json").write_text(json.dumps(manifest))
    with pytest.raises(baseline.PriceBaselineError, match="cannot read valid archive"):
        baseline.build_baseline(root)


def test_repeated_cli_output_is_identical_and_machine_readable(tmp_path: Path, capsys) -> None:
    root = archives(tmp_path, {0: -0.0, 1: -0.01, 2: 0, 3: 0.01})
    assert baseline.main(["--archive-root", str(root)]) == 0
    first = capsys.readouterr().out
    assert baseline.main(["--archive-root", str(root)]) == 0
    second = capsys.readouterr().out
    assert first == second
    payload = json.loads(first)
    assert payload["method"]["source_field"] == "DayAheadPriceDKK"
    assert payload["areas"][0]["negative_interval_count"] == 1
    assert payload["areas"][0]["zero_interval_count"] == 2
    assert payload["areas"][1]["negative_observed_price_dkk_per_mwh"] is None
