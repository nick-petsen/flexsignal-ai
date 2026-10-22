"""Synthetic-only tests for the manual public EDS input archive."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "archive_public_eds_input.py"
spec = importlib.util.spec_from_file_location("archive_public_eds_input", SCRIPT)
assert spec and spec.loader
archive = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = archive
spec.loader.exec_module(archive)


def prepare(tmp_path: Path, raw: bytes, **overrides):
    source = tmp_path / "download.json"
    source.write_bytes(raw)
    options = {
        "input_path": source,
        "dataset": "DayAheadPrices",
        "price_area": "DK1",
        "requested_start": "2026-01-01T00:00",
        "requested_end": "2026-01-02T00:00",
        "request_timezone": "Europe/Copenhagen",
        "archive_id": "dayahead-dk1-chunk-01",
        "archive_root": tmp_path / "archives",
    }
    options.update(overrides)
    return archive.prepare_archive(**options)


DAY_AHEAD = (
    b'{ "records" : [ {"PriceArea":"DK1", "TimeUTC":"2026-01-01T00:00:00",'
    b' "DayAheadPriceDKK":9.1, "DayAheadPriceEUR":1.2300}, {"PriceArea":"DK1",'
    b' "TimeUTC":"2026-01-01T01:00:00", "DayAheadPriceDKK":14.9, "DayAheadPriceEUR":2.0} ] }\n'
)
SETTLEMENT = b'{"records":[{"PriceArea":"DK2","HourUTC":"2026-01-01T00:00:00","GrossConsumptionMWh":42}]}'


def test_preserves_exact_bytes_and_sha256(tmp_path: Path) -> None:
    raw, manifest, target = prepare(tmp_path, DAY_AHEAD)
    archive.write_archive(raw, manifest, target)

    assert (target / "INPUT.json").read_bytes() == DAY_AHEAD
    saved = json.loads((target / "MANIFEST.json").read_text())
    assert saved["input_sha256"] == hashlib.sha256(DAY_AHEAD).hexdigest()
    assert saved["input_byte_size"] == len(DAY_AHEAD)
    assert saved["record_count"] == 2
    assert saved["requested_start"] == "2026-01-01T00:00"
    assert saved["request_timezone"] == "Europe/Copenhagen"
    assert saved["schema_version"] == archive.SCHEMA_VERSION
    assert saved["tool_version"] == archive.TOOL_VERSION


def test_settlement_and_missing_provenance(tmp_path: Path) -> None:
    _, manifest, _ = prepare(
        tmp_path, SETTLEMENT, dataset="ProductionConsumptionSettlement", price_area="DK2"
    )
    assert manifest["dataset"] == "ProductionConsumptionSettlement"
    assert manifest["retrieved_at"] is None
    assert manifest["source_api_url"] is None
    assert "Retrieval timestamp is unknown." in manifest["provenance_verification_limitations"]
    assert "Source API URL is unknown." in manifest["provenance_verification_limitations"]


def test_manifest_has_no_generated_retrieval_time(tmp_path: Path) -> None:
    _, first, _ = prepare(tmp_path, DAY_AHEAD)
    _, second, _ = prepare(tmp_path, DAY_AHEAD)
    assert first == second
    assert first["retrieved_at"] is None


def test_supplied_provenance_is_recorded_verbatim(tmp_path: Path) -> None:
    url = "https://api.energidataservice.dk/dataset/DayAheadPrices?start=2026-01-01"
    _, manifest, _ = prepare(
        tmp_path, DAY_AHEAD, retrieved_at="2026-01-03T12:00:00+01:00", source_url=url
    )
    assert manifest["retrieved_at"] == "2026-01-03T12:00:00+01:00"
    assert manifest["source_api_url"] == url
    assert manifest["git_commit"] is None or len(manifest["git_commit"]) == 40


def test_no_overwrite(tmp_path: Path) -> None:
    raw, manifest, target = prepare(tmp_path, DAY_AHEAD)
    archive.write_archive(raw, manifest, target)
    first_manifest = (target / "MANIFEST.json").read_bytes()
    with pytest.raises(FileExistsError):
        archive.write_archive(raw, manifest, target)
    assert (target / "MANIFEST.json").read_bytes() == first_manifest


def test_default_cli_is_dry_run_without_writes(tmp_path: Path, capsys) -> None:
    source = tmp_path / "download.json"
    source.write_bytes(DAY_AHEAD)
    archive_id = "synthetic-dry-run-archive-test"
    target = archive.ARCHIVE_ROOT / archive_id
    assert not target.exists()
    assert archive.main([
        str(source), "--dataset", "DayAheadPrices", "--price-area", "DK1",
        "--requested-start", "2026-01-01", "--requested-end", "2026-01-02",
        "--request-timezone", "Europe/Copenhagen", "--archive-id", archive_id,
    ]) == 0
    assert json.loads(capsys.readouterr().out)["write"] is False
    assert not target.exists()


@pytest.mark.parametrize("bad_dataset", ["Unknown", "CustomerLoads", "dayaheadprices"])
def test_unsupported_dataset_rejected(tmp_path: Path, bad_dataset: str) -> None:
    with pytest.raises(archive.ArchiveError, match="unsupported dataset"):
        prepare(tmp_path, DAY_AHEAD, dataset=bad_dataset)


@pytest.mark.parametrize("raw", [b"not json", b"{}", b'{"records":[42]}', b'{"records":[{"PriceArea":"DK2","TimeUTC":"x"}]}', b'{"records":[{"PriceArea":"DK1","TimeUTC":"x","price":NaN}]}', b'{"records":[],"records":[]}'])
def test_invalid_inputs_rejected_without_archive(tmp_path: Path, raw: bytes) -> None:
    with pytest.raises(archive.ArchiveError):
        prepare(tmp_path, raw)
    assert not (tmp_path / "archives").exists()


def test_missing_time_and_invalid_metadata_rejected(tmp_path: Path) -> None:
    with pytest.raises(archive.ArchiveError, match="TimeUTC"):
        prepare(tmp_path, b'{"records":[{"PriceArea":"DK1"}]}')
    with pytest.raises(archive.ArchiveError, match="retrieved-at"):
        prepare(tmp_path, DAY_AHEAD, retrieved_at="2026-01-03T12:00:00")
    with pytest.raises(archive.ArchiveError, match="request boundaries"):
        prepare(tmp_path, DAY_AHEAD, requested_end="now")
    with pytest.raises(archive.ArchiveError, match="source-url"):
        prepare(tmp_path, DAY_AHEAD, source_url="https://example.com/DayAheadPrices")
    with pytest.raises(archive.ArchiveError, match="invalid TimeUTC"):
        prepare(
            tmp_path,
            b'{"records":[{"PriceArea":"DK1","TimeUTC":"invalid","DayAheadPriceDKK":1,"DayAheadPriceEUR":1}]}',
        )


def test_empty_response_has_zero_records_and_area_limitation(tmp_path: Path) -> None:
    _, manifest, _ = prepare(tmp_path, b'{"records":[]}')
    assert manifest["record_count"] == 0
    assert "Empty records list cannot confirm the declared price area." in manifest["provenance_verification_limitations"]


def test_interruption_before_manifest_is_not_valid_archive(tmp_path: Path, monkeypatch) -> None:
    raw, manifest, target = prepare(tmp_path, DAY_AHEAD)

    def interrupted(_fd):
        raise KeyboardInterrupt()

    monkeypatch.setattr(archive.os, "fsync", interrupted)
    with pytest.raises(KeyboardInterrupt):
        archive.write_archive(raw, manifest, target)
    assert not (target / "MANIFEST.json").exists()
