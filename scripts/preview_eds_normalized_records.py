#!/usr/bin/env python3
"""Preview normalized Energi Data Service records with one read-only request."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.integrations.energi_data_service import (  # noqa: E402
    ALLOWED_DATASETS,
    ALLOWED_PRICE_AREAS,
    build_eds_url,
    extract_records,
)
from app.integrations.energi_data_service_normalizers import (  # noqa: E402
    normalize_day_ahead_price,
    normalize_electricity_prodex_5min_realtime,
)


DEFAULT_LIMIT = 5
DEFAULT_TIMEOUT_SECONDS = 15
USER_AGENT = "flexsignal-ai-eds-normalized-preview/0.1"

Normalizer = Callable[[dict], dict]

NORMALIZERS: dict[str, Normalizer] = {
    "DayAheadPrices": normalize_day_ahead_price,
    "ElectricityProdex5MinRealtime": normalize_electricity_prodex_5min_realtime,
}


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than 0")

    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manually preview normalized Energi Data Service records with one "
            "read-only HTTP GET request."
        )
    )
    parser.add_argument(
        "--dataset",
        required=True,
        choices=sorted(ALLOWED_DATASETS),
        help="Energi Data Service dataset to preview.",
    )
    parser.add_argument(
        "--price-area",
        required=True,
        choices=sorted(ALLOWED_PRICE_AREAS),
        help="Danish price area filter to apply.",
    )
    parser.add_argument(
        "--limit",
        type=positive_int,
        default=DEFAULT_LIMIT,
        help=f"Maximum raw records to request. Default: {DEFAULT_LIMIT}.",
    )
    return parser


def fetch_body(url: str) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT},
    )

    with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.status, charset, response.read()


def normalize_records(dataset: str, records: list[dict]) -> list[dict]:
    normalizer = NORMALIZERS[dataset]
    normalized: list[dict] = []

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index} must be a JSON object")

        try:
            normalized.append(normalizer(record))
        except Exception as exc:
            raise ValueError(f"Failed to normalize record {index}: {exc}") from exc

    return normalized


def print_json_line(record: dict) -> None:
    print(json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        url = build_eds_url(args.dataset, price_area=args.price_area, limit=args.limit)
    except ValueError as exc:
        print(f"Request configuration failed: {exc}", file=sys.stderr)
        return 2

    print(f"Final request URL: {url}")

    try:
        status, charset, body = fetch_body(url)
    except urllib.error.HTTPError as exc:
        print(f"HTTP status: {exc.code}")
        print(
            f"HTTP request failed: server returned HTTP {exc.code} {exc.reason}",
            file=sys.stderr,
        )
        return 1
    except urllib.error.URLError as exc:
        print("HTTP status: unavailable")
        print(f"HTTP request failed: {exc.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print("HTTP status: unavailable")
        print(
            f"HTTP request failed: timed out after {DEFAULT_TIMEOUT_SECONDS} seconds",
            file=sys.stderr,
        )
        return 1
    except OSError as exc:
        print("HTTP status: unavailable")
        print(f"HTTP request failed: {exc}", file=sys.stderr)
        return 1

    print(f"HTTP status: {status}")
    if status < 200 or status >= 300:
        print(f"HTTP request failed: unexpected HTTP status {status}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(body.decode(charset, errors="replace"))
    except json.JSONDecodeError as exc:
        print(f"Response was not valid JSON: {exc}", file=sys.stderr)
        return 1

    try:
        records = extract_records(payload)
    except ValueError as exc:
        print(f"Records could not be extracted: {exc}", file=sys.stderr)
        return 1

    print(f"Raw record count: {len(records)}")

    try:
        normalized_records = normalize_records(args.dataset, records)
    except ValueError as exc:
        print(f"Normalization failed: {exc}", file=sys.stderr)
        return 1

    print(f"Normalized record count: {len(normalized_records)}")
    for record in normalized_records:
        print_json_line(record)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
