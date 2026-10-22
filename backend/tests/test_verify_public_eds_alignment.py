"""Synthetic-only tests for local public EDS archive alignment."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "verify_public_eds_alignment.py"
spec = importlib.util.spec_from_file_location("verify_public_eds_alignment", SCRIPT)
assert spec and spec.loader
verify = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = verify
spec.loader.exec_module(verify)

START = datetime(2026, 4, 1, tzinfo=timezone.utc)
END = START + timedelta(hours=2)


def write_archive(root: Path, archive_id: str, dataset: str, area: str, records: list[dict]) -> None:
    directory = root / archive_id
    directory.mkdir(parents=True)
    raw = json.dumps({"records": records}).encode()
    (directory / "INPUT.json").write_bytes(raw)
    (directory / "MANIFEST.json").write_text(json.dumps({
        "input_file": "INPUT.json",
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "input_byte_size": len(raw),
        "record_count": len(records),
        "dataset": dataset,
        "price_area": area,
    }))


def fixture_archives(tmp_path: Path) -> Path:
    root = tmp_path / "public-eds-inputs"
    for archive_id, dataset, area, field, minutes in verify.ARCHIVES:
        stamps = [START + timedelta(minutes=minutes * i) for i in range(120 // minutes)]
        records = [{"PriceArea": area, field: stamp.isoformat() if i % 2 else stamp.replace(tzinfo=None).isoformat()}
                   for i, stamp in enumerate(stamps)]
        write_archive(root, archive_id, dataset, area, records)
    return root


def modify_records(root: Path, archive_id: str, change) -> None:
    directory = root / archive_id
    manifest = json.loads((directory / "MANIFEST.json").read_text())
    records = json.loads((directory / "INPUT.json").read_text())["records"]
    change(records)
    write_existing = json.dumps({"records": records}).encode()
    (directory / "INPUT.json").write_bytes(write_existing)
    manifest["input_sha256"] = hashlib.sha256(write_existing).hexdigest()
    manifest["input_byte_size"] = len(write_existing)
    manifest["record_count"] = len(records)
    (directory / "MANIFEST.json").write_text(json.dumps(manifest))


def failures(root: Path) -> dict[str, list[str]]:
    return {archive_id: errors for archive_id, _, errors in verify.verify(root, START, END)}


def test_valid_alignment_and_cli_summary(tmp_path: Path, monkeypatch, capsys) -> None:
    root = fixture_archives(tmp_path)
    modify_records(root, verify.ARCHIVES[0][0], lambda records: records[1].__setitem__(
        "TimeUTC", "2026-04-01T02:15:00+02:00"
    ))
    assert all(not errors for errors in failures(root).values())
    monkeypatch.setattr(verify, "START", START)
    monkeypatch.setattr(verify, "END", END)
    assert verify.main(["--archive-root", str(root)]) == 0
    assert capsys.readouterr().out.endswith("PASS public EDS alignment: 4/4 archives passed\n")


def test_missing_and_duplicate_price_quarters(tmp_path: Path) -> None:
    root = fixture_archives(tmp_path)
    archive_id = verify.ARCHIVES[0][0]
    modify_records(root, archive_id, lambda records: records.__setitem__(1, records[0].copy()))
    errors = failures(root)
    assert "1 missing timestamps" in errors[archive_id]
    assert "1 duplicate timestamps" in errors[archive_id]
    assert "1 hourly record lacks exactly four price quarter-hours" in errors[verify.ARCHIVES[2][0]]


def test_missing_hourly_record(tmp_path: Path) -> None:
    root = fixture_archives(tmp_path)
    archive_id = verify.ARCHIVES[3][0]
    modify_records(root, archive_id, lambda records: records.pop())
    assert "1 missing timestamps" in failures(root)[archive_id]
    assert "record count 1 != 2" in failures(root)[archive_id]


def test_sha_and_byte_length_mismatch(tmp_path: Path) -> None:
    root = fixture_archives(tmp_path)
    archive_id = verify.ARCHIVES[0][0]
    with (root / archive_id / "INPUT.json").open("ab") as output:
        output.write(b" ")
    errors = failures(root)[archive_id]
    assert "SHA-256 mismatch" in errors
    assert "byte length mismatch" in errors


@pytest.mark.parametrize("timestamp, expected", [
    ("2026-04-01T00:05:00Z", "1 misaligned timestamps"),
    ("2026-04-01T02:00:00Z", "1 out-of-range timestamps"),
])
def test_bad_price_interval(tmp_path: Path, timestamp: str, expected: str) -> None:
    root = fixture_archives(tmp_path)
    archive_id = verify.ARCHIVES[1][0]
    modify_records(root, archive_id, lambda records: records[0].__setitem__("TimeUTC", timestamp))
    errors = failures(root)[archive_id]
    assert expected in errors
    assert "1 missing timestamps" in errors


def test_misaligned_hour_does_not_match_price_quarters(tmp_path: Path) -> None:
    root = fixture_archives(tmp_path)
    archive_id = verify.ARCHIVES[2][0]
    modify_records(root, archive_id, lambda records: records[0].__setitem__(
        "HourUTC", "2026-04-01T00:15:00Z"
    ))
    errors = failures(root)[archive_id]
    assert "1 misaligned timestamps" in errors
    assert "1 hourly record lacks exactly four price quarter-hours" in errors


def test_manifest_dataset_and_record_area(tmp_path: Path) -> None:
    root = fixture_archives(tmp_path)
    archive_id = verify.ARCHIVES[0][0]
    manifest_path = root / archive_id / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["dataset"] = "ProductionConsumptionSettlement"
    manifest["price_area"] = "DK2"
    manifest_path.write_text(json.dumps(manifest))
    modify_records(root, archive_id, lambda records: records[0].__setitem__("PriceArea", "DK2"))
    errors = failures(root)[archive_id]
    assert "dataset mismatch" in errors
    assert "manifest PriceArea mismatch" in errors
    assert "1 record with invalid PriceArea or TimeUTC" in errors


def test_missing_archive_returns_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(verify, "ARCHIVE_ROOT", tmp_path)
    assert verify.main([]) == 1
    assert capsys.readouterr().out.count("FAIL ") == 5


def test_production_window_requires_672_prices_and_168_hours(tmp_path: Path) -> None:
    root = tmp_path / "public-eds-inputs"
    for archive_id, dataset, area, _, _ in verify.ARCHIVES:
        write_archive(root, archive_id, dataset, area, [])
    errors = {archive_id: messages for archive_id, _, messages in verify.verify(root)}
    assert "record count 0 != 672" in errors[verify.ARCHIVES[0][0]]
    assert "record count 0 != 168" in errors[verify.ARCHIVES[2][0]]
