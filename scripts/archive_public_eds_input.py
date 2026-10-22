#!/usr/bin/env python3
"""Manually archive an already downloaded public EDS JSON response."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = REPO_ROOT / "artifacts" / "public-eds-inputs"
SCHEMA_VERSION = "public_eds_input_archive.v0"
TOOL_VERSION = "0.1.0"
DATASETS = {"DayAheadPrices": "TimeUTC", "ProductionConsumptionSettlement": "HourUTC"}
AREAS = {"DK1", "DK2"}
INPUT_NAME = "INPUT.json"
MANIFEST_NAME = "MANIFEST.json"


class ArchiveError(ValueError):
    """Invalid input or unsafe archive request."""


def _boundary(value: str) -> datetime:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2})?", value):
        raise ArchiveError("request boundaries must use YYYY-MM-DD or YYYY-MM-DDTHH:MM")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ArchiveError("invalid request boundary") from exc


def _retrieved_at(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ArchiveError("retrieved-at must be an ISO 8601 timestamp with offset") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ArchiveError("retrieved-at must include a UTC offset")
    return value


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"nonstandard JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def prepare_archive(
    *,
    input_path: Path,
    dataset: str,
    price_area: str,
    requested_start: str,
    requested_end: str,
    request_timezone: str,
    archive_id: str,
    retrieved_at: str | None = None,
    source_url: str | None = None,
    archive_root: Path = ARCHIVE_ROOT,
) -> tuple[bytes, dict, Path]:
    if dataset not in DATASETS:
        raise ArchiveError("unsupported dataset")
    if price_area not in AREAS:
        raise ArchiveError("price area must be DK1 or DK2")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", archive_id) or archive_id in {".", ".."}:
        raise ArchiveError("archive-id must contain only letters, digits, dots, underscores or hyphens")
    start, end = _boundary(requested_start), _boundary(requested_end)
    if end <= start:
        raise ArchiveError("requested end must be after requested start")
    try:
        ZoneInfo(request_timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ArchiveError("request-timezone must be a valid IANA timezone") from exc
    retrieved_at = _retrieved_at(retrieved_at)
    if source_url is not None:
        parsed = urlparse(source_url)
        if parsed.scheme != "https" or parsed.hostname != "api.energidataservice.dk" or parsed.username or parsed.password:
            raise ArchiveError("source-url must be a public HTTPS EDS API URL")
        if not parsed.path.rstrip("/").endswith("/" + dataset):
            raise ArchiveError("source-url dataset does not match")
    if input_path.is_symlink() or not input_path.is_file():
        raise ArchiveError("input must be a regular local file")
    raw = input_path.read_bytes()
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_json_constant,
            object_pairs_hook=_unique_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ArchiveError("input is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise ArchiveError("input must contain an EDS records list")
    timestamp_key = DATASETS[dataset]
    for index, record in enumerate(payload["records"]):
        if not isinstance(record, dict) or record.get("PriceArea") != price_area or not isinstance(record.get(timestamp_key), str) or not record[timestamp_key]:
            raise ArchiveError(f"record {index} lacks the expected price area or {timestamp_key}")
        if "T" not in record[timestamp_key]:
            raise ArchiveError(f"record {index} has an invalid {timestamp_key}")
        try:
            datetime.fromisoformat(record[timestamp_key].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ArchiveError(f"record {index} has an invalid {timestamp_key}") from exc
        if dataset == "DayAheadPrices" and (
            "DayAheadPriceDKK" not in record or "DayAheadPriceEUR" not in record
        ):
            raise ArchiveError(f"record {index} lacks required day-ahead price fields")

    target = archive_root / archive_id
    if target.exists() or target.is_symlink():
        raise ArchiveError("archive already exists")
    limitations = [
        "Metadata is operator supplied and is not independently verified against the API request.",
        "JSON shape and price area checks do not prove dataset origin, completeness, or historical revision.",
        "Git commit identifies the current checkout, not necessarily the version that fetched or processed this input.",
        "This archive is an input copy, not a verified backtest or risk-window result.",
    ]
    if retrieved_at is None:
        limitations.append("Retrieval timestamp is unknown.")
    if source_url is None:
        limitations.append("Source API URL is unknown.")
    if not payload["records"]:
        limitations.append("Empty records list cannot confirm the declared price area.")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "dataset": dataset,
        "price_area": price_area,
        "requested_start": requested_start,
        "requested_end": requested_end,
        "request_timezone": request_timezone,
        "retrieved_at": retrieved_at,
        "source_api_url": source_url,
        "input_file": INPUT_NAME,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "input_byte_size": len(raw),
        "record_count": len(payload["records"]),
        "git_commit": _git_commit(),
        "tool_version": TOOL_VERSION,
        "provenance_verification_limitations": limitations,
    }
    return raw, manifest, target


def write_archive(raw: bytes, manifest: dict, target: Path) -> None:
    root = target.parent
    if root.is_symlink() or (root == ARCHIVE_ROOT and not root.resolve().is_relative_to(REPO_ROOT)):
        raise ArchiveError("archive root must be a local directory")
    root.mkdir(parents=True, exist_ok=True)
    target.mkdir(exist_ok=False)
    manifest_published = False
    try:
        input_file = target / INPUT_NAME
        with input_file.open("xb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        if hashlib.sha256(input_file.read_bytes()).hexdigest() != manifest["input_sha256"]:
            raise ArchiveError("archived input verification failed")
        pending = target / ".MANIFEST.pending"
        with pending.open("x", encoding="utf-8") as output:
            json.dump(manifest, output, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(pending, target / MANIFEST_NAME)
        manifest_published = True
    except Exception:
        if not manifest_published:
            shutil.rmtree(target)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--price-area", required=True)
    parser.add_argument("--requested-start", required=True)
    parser.add_argument("--requested-end", required=True)
    parser.add_argument("--request-timezone", required=True)
    parser.add_argument("--archive-id", required=True)
    parser.add_argument("--retrieved-at", help="Known ISO 8601 retrieval timestamp with offset")
    parser.add_argument("--source-url", help="Known public EDS API request URL")
    parser.add_argument("--write", action="store_true", help="Write archive; default only validates")
    args = parser.parse_args(argv)
    try:
        raw, manifest, target = prepare_archive(
            input_path=args.input,
            dataset=args.dataset,
            price_area=args.price_area,
            requested_start=args.requested_start,
            requested_end=args.requested_end,
            request_timezone=args.request_timezone,
            archive_id=args.archive_id,
            retrieved_at=args.retrieved_at,
            source_url=args.source_url,
        )
        if args.write:
            write_archive(raw, manifest, target)
        print(json.dumps({"write": args.write, "archive_path": str(target), "manifest": manifest}, indent=2, sort_keys=True))
        return 0
    except (ArchiveError, OSError) as exc:
        print(f"Archive rejected: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
