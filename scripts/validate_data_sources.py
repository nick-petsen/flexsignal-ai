#!/usr/bin/env python3
"""Manually validate candidate public data source API endpoints.

This script performs a single read-only HTTP GET request and prints a compact
summary of the response. It does not store data or integrate with ingestion.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 15


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def valid_date(value: str) -> str:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must use YYYY-MM-DD format") from exc

    if parsed.strftime("%Y-%m-%d") != value:
        raise argparse.ArgumentTypeError("must use YYYY-MM-DD format")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manually validate candidate public data source APIs with read-only GET requests."
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=("energi-data-service", "elprisenligenu", "dmi-url"),
        help="Candidate source to validate.",
    )
    parser.add_argument(
        "--dataset",
        help="Energi Data Service dataset name. Required for --source energi-data-service.",
    )
    parser.add_argument(
        "--limit",
        type=positive_int,
        default=5,
        help="Energi Data Service result limit. Default: 5.",
    )
    parser.add_argument(
        "--date",
        type=valid_date,
        help="Elprisenligenu date in YYYY-MM-DD format. Required for --source elprisenligenu.",
    )
    parser.add_argument(
        "--price-area",
        choices=("DK1", "DK2"),
        help="Elprisenligenu price area. Required for --source elprisenligenu.",
    )
    parser.add_argument(
        "--url",
        help="DMI Open Data URL. Required for --source dmi-url.",
    )
    return parser


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.source == "energi-data-service" and not args.dataset:
        parser.error("--dataset is required when --source is energi-data-service")

    if args.source == "elprisenligenu":
        if not args.date:
            parser.error("--date is required when --source is elprisenligenu")
        if not args.price_area:
            parser.error("--price-area is required when --source is elprisenligenu")

    if args.source == "dmi-url":
        if not args.url:
            parser.error("--url is required when --source is dmi-url")
        url = args.url.strip()
        if not url.startswith("https://opendataapi.dmi.dk/"):
            parser.error(
                "--url must start with https://opendataapi.dmi.dk/ for --source dmi-url"
            )
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "opendataapi.dmi.dk":
            parser.error(
                "--url must use the opendataapi.dmi.dk host for --source dmi-url"
            )
        args.url = url


def build_url(args: argparse.Namespace) -> str:
    if args.source == "energi-data-service":
        dataset = urllib.parse.quote(args.dataset.strip(), safe="")
        return f"https://api.energidataservice.dk/dataset/{dataset}?limit={args.limit}"

    if args.source == "dmi-url":
        return args.url

    year, month, day = args.date.split("-")
    return (
        "https://www.elprisenligenu.dk/api/v1/prices/"
        f"{year}/{month}-{day}_{args.price_area}.json"
    )


def fetch_url(url: str) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "flexsignal-ai-data-source-validator/0.1"},
    )

    with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.status, charset, response.read()


def find_records(payload: Any) -> tuple[int | None, Any | None]:
    if isinstance(payload, list):
        return len(payload), payload[0] if payload else None

    if not isinstance(payload, dict):
        return None, None

    for key in ("records", "data", "results", "items", "features", "observations"):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value), value[0] if value else None

    for value in payload.values():
        if isinstance(value, dict):
            nested_count, nested_sample = find_records(value)
            if nested_count is not None:
                return nested_count, nested_sample

    return None, None


def compact_json(value: Any, max_chars: int = 1200) -> str:
    rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if len(rendered) <= max_chars:
        return rendered
    return f"{rendered[: max_chars - 3]}..."


def print_json_summary(body: bytes, charset: str) -> int:
    text = body.decode(charset, errors="replace")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        print(f"Response body was not valid JSON: {exc}", file=sys.stderr)
        return 1

    if isinstance(payload, dict):
        print(f"Top-level keys: {', '.join(sorted(payload.keys()))}")
    else:
        print(f"Top-level JSON type: {type(payload).__name__}")

    record_count, sample_record = find_records(payload)
    if record_count is not None:
        print(f"Record count: {record_count}")
    else:
        print("Record count: not obvious")

    if sample_record is not None:
        print(f"Sample record: {compact_json(sample_record)}")
    else:
        print("Sample record: not available")

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    validate_args(parser, args)

    url = build_url(args)
    print(f"Testing URL: {url}")

    try:
        status, charset, body = fetch_url(url)
    except urllib.error.HTTPError as exc:
        print(f"HTTP status: {exc.code}")
        print(f"Request failed: server returned HTTP {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print(f"Request failed: timed out after {DEFAULT_TIMEOUT_SECONDS} seconds", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    print(f"HTTP status: {status}")
    if status < 200 or status >= 300:
        print(f"Request failed: unexpected HTTP status {status}", file=sys.stderr)
        return 1

    return print_json_summary(body, charset)


if __name__ == "__main__":
    raise SystemExit(main())
