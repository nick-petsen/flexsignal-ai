#!/usr/bin/env python3
"""Dry-run Energi Data Service source check for public surplus-risk mapping."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


EDS_DATASET_BASE_URL = "https://api.energidataservice.dk/dataset"
EDS_HOST = "api.energidataservice.dk"
DEFAULT_LIMIT = 1
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_REQUEST_DELAY_SECONDS = 1.0
REQUEST_DELAY_ENV = "SURPLUS_SOURCE_CHECK_REQUEST_DELAY_SECONDS"
DEFAULT_PRICE_AREAS = ("DK1", "DK2")
USER_AGENT = "flexsignal-ai-public-surplus-source-check/0.1"
REQUIRED_FOR_HISTORICAL_SURPLUS_RISK_V1 = "required_for_historical_surplus_risk_v1"
OPTIONAL_LATER = "optional_later"
NEAR_LIVE_LATER = "near_live_later"


@dataclass(frozen=True)
class CandidateDataset:
    dataset: str
    purpose: str
    expected_fields: tuple[str, ...]
    timestamp_field: str
    area_field: str
    classification: str


CANDIDATES: tuple[CandidateDataset, ...] = (
    CandidateDataset(
        dataset="DayAheadPrices",
        purpose="Market price opportunity context already used by public market v0.",
        expected_fields=(
            "PriceArea",
            "TimeUTC",
            "TimeDK",
            "DayAheadPriceEUR",
            "DayAheadPriceDKK",
        ),
        timestamp_field="TimeUTC",
        area_field="PriceArea",
        classification=REQUIRED_FOR_HISTORICAL_SURPLUS_RISK_V1,
    ),
    CandidateDataset(
        dataset="ProductionConsumptionSettlement",
        purpose="Historical production, consumption, renewable generation, and exchange context.",
        expected_fields=(
            "PriceArea",
            "HourUTC",
            "HourDK",
            "GrossConsumptionMWh",
            "OnshoreWindGe50kW_MWh",
            "OnshoreWindLt50kW_MWh",
            "OffshoreWindGe100MW_MWh",
            "OffshoreWindLt100MW_MWh",
            "SolarPowerGe10Lt40kW_MWh",
            "SolarPowerGe40kW_MWh",
            "SolarPowerLt10kW_MWh",
            "SolarPowerSelfConMWh",
            "ExchangeGE_MWh",
            "ExchangeNO_MWh",
            "ExchangeSE_MWh",
            "ExchangeGB_MWh",
            "ExchangeNL_MWh",
            "ExchangeGreatBelt_MWh",
        ),
        timestamp_field="HourUTC",
        area_field="PriceArea",
        classification=REQUIRED_FOR_HISTORICAL_SURPLUS_RISK_V1,
    ),
    CandidateDataset(
        dataset="ElectricityProdex5MinRealtime",
        purpose="Near-real-time production, wind, solar, and exchange context.",
        expected_fields=(
            "PriceArea",
            "Minutes5UTC",
            "Minutes5DK",
            "ProductionGe100MW",
            "ProductionLt100MW",
            "OnshoreWindPower",
            "OffshoreWindPower",
            "SolarPower",
            "ExchangeGermany",
            "ExchangeNorway",
            "ExchangeSweden",
            "ExchangeGreatBelt",
            "ExchangeNetherlands",
            "ExchangeGreatBritain",
        ),
        timestamp_field="Minutes5UTC",
        area_field="PriceArea",
        classification=NEAR_LIVE_LATER,
    ),
    CandidateDataset(
        dataset="ElectricityBalanceNonv",
        purpose="Near-real-time non-validated load, generation mix, and balance context.",
        expected_fields=(
            "PriceArea",
            "HourUTC",
            "HourDK",
            "TotalLoad",
            "OnshoreWindPower",
            "OffshoreWindPower",
            "SolarPower",
            "Biomass",
            "FossilGas",
            "FossilHardCoal",
            "FossilOil",
            "HydroPower",
            "Waste",
            "OtherRenewable",
        ),
        timestamp_field="HourUTC",
        area_field="PriceArea",
        classification=OPTIONAL_LATER,
    ),
)


class SourceCheckError(RuntimeError):
    """Expected safe-fail error for the source checker."""


@dataclass(frozen=True)
class CheckResult:
    dataset: str
    price_area: str
    http_status: int
    record_count: int
    total: Any
    fields_present: tuple[str, ...]
    missing_expected_fields: tuple[str, ...]
    timestamp_field_present: bool
    area_field_present: bool
    area_value_matches: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run/read-only Energi Data Service availability and sample-field "
            "check for public surplus-risk source mapping."
        )
    )
    parser.add_argument(
        "--dataset",
        choices=tuple(candidate.dataset for candidate in CANDIDATES) + ("all",),
        default="all",
        help="Candidate EDS dataset to check. Default: all.",
    )
    parser.add_argument(
        "--price-area",
        choices=DEFAULT_PRICE_AREAS + ("all",),
        default="all",
        help="Price area to check. Default: all.",
    )
    parser.add_argument(
        "--limit",
        type=positive_int,
        default=DEFAULT_LIMIT,
        help=f"EDS result limit per request. Default: {DEFAULT_LIMIT}.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=positive_int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"HTTP timeout. Default: {DEFAULT_TIMEOUT_SECONDS}.",
    )
    parser.add_argument(
        "--request-delay-seconds",
        type=nonnegative_float,
        default=None,
        help=(
            "Delay between sequential EDS requests to reduce rate-limit pressure. "
            f"Default: {REQUEST_DELAY_ENV} or {DEFAULT_REQUEST_DELAY_SECONDS}."
        ),
    )
    return parser


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def nonnegative_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc

    if parsed < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return parsed


def env_request_delay_seconds(parser: argparse.ArgumentParser) -> float:
    raw_value = os.environ.get(REQUEST_DELAY_ENV)
    if raw_value is None or not raw_value.strip():
        return DEFAULT_REQUEST_DELAY_SECONDS

    try:
        return nonnegative_float(raw_value.strip())
    except argparse.ArgumentTypeError as exc:
        parser.error(f"{REQUEST_DELAY_ENV} {exc}")


def is_required(candidate: CandidateDataset) -> bool:
    return candidate.classification == REQUIRED_FOR_HISTORICAL_SURPLUS_RISK_V1


def selected_candidates(dataset: str) -> tuple[CandidateDataset, ...]:
    if dataset == "all":
        return CANDIDATES

    return tuple(candidate for candidate in CANDIDATES if candidate.dataset == dataset)


def selected_price_areas(price_area: str) -> tuple[str, ...]:
    if price_area == "all":
        return DEFAULT_PRICE_AREAS

    return (price_area,)


def build_eds_url(dataset: str, price_area: str, limit: int) -> str:
    query = urllib.parse.urlencode(
        {
            "limit": str(limit),
            "filter": json.dumps(
                {"PriceArea": [price_area]},
                separators=(",", ":"),
            ),
        }
    )
    url = f"{EDS_DATASET_BASE_URL}/{urllib.parse.quote(dataset, safe='')}?{query}"
    require_eds_url(url)
    return url


def require_eds_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != EDS_HOST:
        raise SourceCheckError("Refusing to call non-EDS URL")


def fetch_json(url: str, timeout_seconds: int) -> tuple[int, dict[str, Any]]:
    require_eds_url(url)
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT},
    )

    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        status = response.status
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset, errors="replace")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise SourceCheckError(f"EDS response was not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise SourceCheckError("EDS response must be a JSON object")

    return status, payload


def check_candidate(
    candidate: CandidateDataset,
    price_area: str,
    *,
    limit: int,
    timeout_seconds: int,
) -> CheckResult:
    url = build_eds_url(candidate.dataset, price_area, limit)
    status, payload = fetch_json(url, timeout_seconds)
    records = payload.get("records")

    if not isinstance(records, list):
        raise SourceCheckError("EDS payload did not include a records list")

    sample = records[0] if records else {}
    if sample and not isinstance(sample, dict):
        raise SourceCheckError("EDS sample record was not a JSON object")

    fields_present = tuple(sorted(sample.keys()))
    missing_expected = tuple(
        field for field in candidate.expected_fields if field not in sample
    )

    return CheckResult(
        dataset=candidate.dataset,
        price_area=price_area,
        http_status=status,
        record_count=len(records),
        total=payload.get("total"),
        fields_present=fields_present,
        missing_expected_fields=missing_expected,
        timestamp_field_present=candidate.timestamp_field in sample,
        area_field_present=candidate.area_field in sample,
        area_value_matches=sample.get(candidate.area_field) == price_area,
    )


def print_candidate_header(candidate: CandidateDataset) -> None:
    print(f"\nDataset: {candidate.dataset}")
    print(f"Purpose: {candidate.purpose}")
    print(f"Classification: {candidate.classification}")
    print(f"Timestamp field: {candidate.timestamp_field}")
    print(f"Area field: {candidate.area_field}")


def print_result(result: CheckResult) -> None:
    missing = (
        ", ".join(result.missing_expected_fields)
        if result.missing_expected_fields
        else "none"
    )
    fields = ", ".join(result.fields_present) if result.fields_present else "none"
    print(f"- {result.price_area}: HTTP {result.http_status}; records {result.record_count}; total {result.total}")
    print(f"  timestamp field present: {str(result.timestamp_field_present).lower()}")
    print(f"  area field present: {str(result.area_field_present).lower()}")
    print(f"  area value matches filter: {str(result.area_value_matches).lower()}")
    print(f"  missing expected fields: {missing}")
    print(f"  sample fields: {fields}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    request_delay_seconds = (
        args.request_delay_seconds
        if args.request_delay_seconds is not None
        else env_request_delay_seconds(parser)
    )

    required_failures: list[str] = []
    nonrequired_warnings: list[str] = []
    first_request = True

    print("Public surplus-risk EDS source check")
    print("Mode: dry-run/read-only")
    print("No files written: true")
    print("Database writes: false")
    print("External APIs: Energi Data Service only")
    print(
        "Required historical surplus-risk v1 sources: "
        "DayAheadPrices, ProductionConsumptionSettlement"
    )

    for candidate in selected_candidates(args.dataset):
        print_candidate_header(candidate)
        for price_area in selected_price_areas(args.price_area):
            if not first_request and request_delay_seconds:
                time.sleep(request_delay_seconds)
            first_request = False

            try:
                result = check_candidate(
                    candidate,
                    price_area,
                    limit=args.limit,
                    timeout_seconds=args.timeout_seconds,
                )
            except urllib.error.HTTPError as exc:
                message = f"{candidate.dataset} {price_area}: HTTP {exc.code}"
                print(f"- {price_area}: HTTP {exc.code}; check failed")
                if exc.code == 429:
                    print(
                        "  EDS rate limit reached; retry later or increase request delay."
                    )
                if is_required(candidate):
                    required_failures.append(message)
                else:
                    nonrequired_warnings.append(message)
                continue
            except (urllib.error.URLError, TimeoutError, OSError, SourceCheckError) as exc:
                message = f"{candidate.dataset} {price_area}: {exc}"
                print(f"- {price_area}: check failed: {exc}")
                if is_required(candidate):
                    required_failures.append(message)
                else:
                    nonrequired_warnings.append(message)
                continue

            print_result(result)
            if result.missing_expected_fields or not result.area_value_matches:
                message = f"{candidate.dataset} {price_area}: validation gap"
                if is_required(candidate):
                    required_failures.append(message)
                else:
                    nonrequired_warnings.append(message)

    print(
        "\nRequired sources passed: "
        f"{str(not required_failures).lower()}"
    )
    if nonrequired_warnings:
        print("Optional/near-live gaps:")
        for warning in nonrequired_warnings:
            print(f"- warning: {warning}")
    else:
        print("Optional/near-live gaps: none")

    print("No files written: true")
    print("Database writes: false")
    print("External APIs: Energi Data Service only")

    if required_failures:
        print("\nResult: required source validation failed")
        for failure in required_failures:
            print(f"- {failure}")
        return 1

    print("\nResult: required historical surplus-risk v1 sources passed")
    if nonrequired_warnings:
        print("Optional/near-live validation gaps were warnings only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
