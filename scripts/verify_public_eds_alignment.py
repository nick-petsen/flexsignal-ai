#!/usr/bin/env python3
"""Verify hourly alignment of four local, archived public EDS inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


ARCHIVE_ROOT = Path(__file__).resolve().parents[1] / "artifacts" / "public-eds-inputs"
START = datetime(2026, 4, 1, tzinfo=timezone.utc)
END = datetime(2026, 4, 8, tzinfo=timezone.utc)
ARCHIVES = (
    ("dayaheadprices-dk1-20260401-20260408-utc", "DayAheadPrices", "DK1", "TimeUTC", 15),
    ("dayaheadprices-dk2-20260401-20260408-utc", "DayAheadPrices", "DK2", "TimeUTC", 15),
    (
        "productionconsumption-dk1-20260401-20260408-utc",
        "ProductionConsumptionSettlement", "DK1", "HourUTC", 60,
    ),
    (
        "productionconsumption-dk2-20260401-20260408-utc",
        "ProductionConsumptionSettlement", "DK2", "HourUTC", 60,
    ),
)


def _utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or "T" not in value:
        raise ValueError(f"invalid {field}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {field}") from exc
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


def _read_archive(
    root: Path, archive_id: str, dataset: str, area: str, field: str, minutes: int,
    start: datetime, end: datetime,
) -> tuple[Counter[datetime], list[str]]:
    errors: list[str] = []
    directory = root / archive_id
    manifest_path = directory / "MANIFEST.json"
    input_path = directory / "INPUT.json"
    try:
        if directory.is_symlink() or manifest_path.is_symlink() or input_path.is_symlink():
            raise ValueError("archive paths must not be symlinks")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw = input_path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except FileNotFoundError:
        return Counter(), ["missing MANIFEST.json or INPUT.json"]
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return Counter(), [f"cannot read valid archive: {type(exc).__name__}"]
    if not isinstance(manifest, dict) or not isinstance(payload, dict):
        return Counter(), ["manifest and input must be JSON objects"]
    if manifest.get("input_file") != "INPUT.json":
        errors.append("manifest input_file mismatch")
    if manifest.get("input_sha256") != hashlib.sha256(raw).hexdigest():
        errors.append("SHA-256 mismatch")
    if type(manifest.get("input_byte_size")) is not int or manifest["input_byte_size"] != len(raw):
        errors.append("byte length mismatch")
    if manifest.get("dataset") != dataset:
        errors.append("dataset mismatch")
    if manifest.get("price_area") != area:
        errors.append("manifest PriceArea mismatch")
    records = payload.get("records")
    if not isinstance(records, list):
        return Counter(), errors + ["input records must be a list"]
    if manifest.get("record_count") != len(records):
        errors.append("manifest record_count mismatch")

    timestamps: Counter[datetime] = Counter()
    invalid = 0
    for record in records:
        if not isinstance(record, dict) or record.get("PriceArea") != area:
            invalid += 1
            continue
        try:
            timestamp = _utc(record.get(field), field)
        except ValueError:
            invalid += 1
            continue
        timestamps[timestamp] += 1
    if invalid:
        errors.append(f"{invalid} record{'s' if invalid != 1 else ''} with invalid PriceArea or {field}")

    interval_count = int((end - start).total_seconds() // (minutes * 60))
    expected = {start + timedelta(minutes=minutes * index) for index in range(interval_count)}
    missing = expected - timestamps.keys()
    duplicates = sum(count - 1 for count in timestamps.values() if count > 1)
    out_of_range = sum(count for stamp, count in timestamps.items() if stamp < start or stamp >= end)
    misaligned = sum(count for stamp, count in timestamps.items() if stamp not in expected and start <= stamp < end)
    if len(records) != len(expected):
        errors.append(f"record count {len(records)} != {len(expected)}")
    if missing:
        errors.append(f"{len(missing)} missing timestamps")
    if duplicates:
        errors.append(f"{duplicates} duplicate timestamps")
    if out_of_range:
        errors.append(f"{out_of_range} out-of-range timestamps")
    if misaligned:
        errors.append(f"{misaligned} misaligned timestamps")
    return timestamps, errors


def verify(
    root: Path = ARCHIVE_ROOT, start: datetime = START, end: datetime = END,
) -> list[tuple[str, int, list[str]]]:
    """Return one deterministic result per archive, using an exclusive UTC end."""
    if (
        start.tzinfo != timezone.utc or end.tzinfo != timezone.utc
        or end <= start or (end - start) % timedelta(hours=1)
    ):
        raise ValueError("start and end must delimit whole UTC hours")
    results = []
    by_area: dict[str, dict[str, Counter[datetime]]] = {}
    for archive_id, dataset, area, field, minutes in ARCHIVES:
        timestamps, errors = _read_archive(root, archive_id, dataset, area, field, minutes, start, end)
        by_area.setdefault(area, {})[field] = timestamps
        results.append((archive_id, sum(timestamps.values()), errors))
    for area in ("DK1", "DK2"):
        prices = by_area[area]["TimeUTC"]
        hours = by_area[area]["HourUTC"]
        mismatched = sum(
            1 for hour in hours
            if hour != hour.replace(minute=0, second=0, microsecond=0)
            or any(prices[hour + timedelta(minutes=offset)] != 1 for offset in (0, 15, 30, 45))
        )
        if mismatched:
            index = next(
                i for i, (_, _, name, field, _) in enumerate(ARCHIVES)
                if name == area and field == "HourUTC"
            )
            noun = "record" if mismatched == 1 else "records"
            verb = "lacks" if mismatched == 1 else "lack"
            results[index][2].append(f"{mismatched} hourly {noun} {verb} exactly four price quarter-hours")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-root", type=Path, default=ARCHIVE_ROOT)
    args = parser.parse_args(argv)
    results = verify(args.archive_root, START, END)
    for archive_id, count, errors in results:
        status = "FAIL" if errors else "PASS"
        details = "; ".join(errors) if errors else "aligned"
        print(f"{status} {archive_id}: {count} parsed timestamps; {details}")
    passed = sum(not errors for _, _, errors in results)
    print(f"{'PASS' if passed == 4 else 'FAIL'} public EDS alignment: {passed}/4 archives passed")
    return 0 if passed == 4 else 1


if __name__ == "__main__":
    sys.exit(main())
