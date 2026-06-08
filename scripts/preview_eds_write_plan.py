#!/usr/bin/env python3
"""Preview Energi Data Service database write-plan entries."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.write_plan import build_eds_write_plan  # noqa: E402
from app.ingestion.eds_dry_run import (  # noqa: E402
    SUPPORTED_DATASETS,
    SUPPORTED_PRICE_AREAS,
    run_eds_dry_run,
)
from app.integrations.energi_data_service import build_eds_url  # noqa: E402


DEFAULT_LIMIT = 5
DEFAULT_TIMEOUT_SECONDS = 15
USER_AGENT = "flexsignal-ai-eds-write-plan-preview/0.1"


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
            "Manually preview Energi Data Service database write-plan entries "
            "with one read-only HTTP GET request."
        )
    )
    parser.add_argument(
        "--dataset",
        required=True,
        choices=sorted(SUPPORTED_DATASETS),
        help="Energi Data Service dataset to preview.",
    )
    parser.add_argument(
        "--price-area",
        required=True,
        choices=sorted(SUPPORTED_PRICE_AREAS),
        help="Danish price area filter to apply.",
    )
    parser.add_argument(
        "--limit",
        type=positive_int,
        default=DEFAULT_LIMIT,
        help=f"Maximum raw records to request. Default: {DEFAULT_LIMIT}.",
    )
    return parser


def fetch_json(url: str) -> tuple[int, Mapping[str, Any]]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT},
    )

    with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read()
        payload = json.loads(body.decode(charset, errors="replace"))

    if not isinstance(payload, dict):
        raise ValueError("Energi Data Service response must be a JSON object")

    return response.status, payload


def print_json_line(entry: Mapping[str, Any]) -> None:
    print(json.dumps(entry, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    http_status: int | None = None

    try:
        request_url = build_eds_url(
            args.dataset,
            price_area=args.price_area,
            limit=args.limit,
        )
    except ValueError as exc:
        print(f"Request configuration failed: {exc}", file=sys.stderr)
        return 2

    print(f"Final request URL: {request_url}")

    def fetch(url: str) -> Mapping[str, Any]:
        nonlocal http_status
        http_status, payload = fetch_json(url)
        return payload

    try:
        summary = run_eds_dry_run(
            dataset=args.dataset,
            price_area=args.price_area,
            limit=args.limit,
            fetch=fetch,
        )
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
    except json.JSONDecodeError as exc:
        if http_status is not None:
            print(f"HTTP status: {http_status}")
        else:
            print("HTTP status: unavailable")
        print(f"Response was not valid JSON: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        if http_status is not None:
            print(f"HTTP status: {http_status}")
        else:
            print("HTTP status: unavailable")
        print(f"Preview failed: {exc}", file=sys.stderr)
        return 1

    print(f"HTTP status: {http_status}")
    print(f"Raw record count: {summary.raw_record_count}")
    print(f"Normalized record count: {summary.normalized_record_count}")

    try:
        write_plan = build_eds_write_plan(
            dataset=args.dataset,
            normalized_records=summary.normalized_records,
        )
    except ValueError as exc:
        print(f"Write plan failed: {exc}", file=sys.stderr)
        return 1

    print(f"Write plan entry count: {len(write_plan)}")
    for entry in write_plan:
        print_json_line(entry)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
