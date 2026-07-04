#!/usr/bin/env python3
"""Read-only public DK1/DK2 market input preview for backtest preparation."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from zoneinfo import ZoneInfo


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.integrations.energi_data_service import (  # noqa: E402
    ALLOWED_PRICE_AREAS,
    BASE_URL,
    MAX_LIMIT,
    build_eds_url,
    extract_records,
)
from app.integrations.energi_data_service_normalizers import (  # noqa: E402
    normalize_day_ahead_price,
)


DEFAULT_START_DATE = "2026-01-01"
DEFAULT_END_DATE = "now"
DEFAULT_PRICE_AREAS = "DK1,DK2"
DEFAULT_DRY_RUN = "true"
DEFAULT_EDS_REQUEST_DELAY_SECONDS = 1.0
DEFAULT_EDS_MAX_RETRIES = 3
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_CHUNK_DAYS = 31
DAY_AHEAD_PRICES = "DayAheadPrices"
DATASETS = (DAY_AHEAD_PRICES,)
EDS_HOST = "api.energidataservice.dk"
EDS_TIMEZONE = ZoneInfo("Europe/Copenhagen")
USER_AGENT = "flexsignal-ai-public-market-backtest-input/0.1"

JsonPayload = Mapping[str, Any]
FetchFn = Callable[[str], JsonPayload]
SleepFn = Callable[[float], None]


class BacktestInputError(RuntimeError):
    """Expected safe-fail error for public market input preparation."""


@dataclass(frozen=True)
class BacktestInputConfig:
    start_date: str
    end_date: str
    resolved_end: str
    price_areas: tuple[str, ...]
    dry_run: bool
    eds_request_delay_seconds: float
    eds_max_retries: int


@dataclass(frozen=True)
class DatasetAreaResult:
    dataset: str
    price_area: str
    request_urls: tuple[str, ...]
    raw_record_count: int
    normalized_record_count: int
    earliest_timestamp_utc: str
    latest_timestamp_utc: str
    normalized_rows: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class BacktestInputSummary:
    period: str
    price_areas: tuple[str, ...]
    datasets_requested: tuple[str, ...]
    record_counts: Mapping[str, int]
    earliest_timestamp_utc: str
    latest_timestamp_utc: str
    dry_run: bool
    source: str
    note: str
    file_written: bool
    database_write_performed: bool


def load_config(
    env: Mapping[str, str] | None = None,
    *,
    now_fn: Callable[[], datetime] | None = None,
) -> BacktestInputConfig:
    safe_env = os.environ if env is None else env
    now = (now_fn or (lambda: datetime.now(timezone.utc)))()

    start_date = safe_env.get("BACKTEST_START_DATE", DEFAULT_START_DATE).strip()
    end_date = safe_env.get("BACKTEST_END_DATE", DEFAULT_END_DATE).strip()
    price_areas = _parse_price_areas(
        safe_env.get("BACKTEST_PRICE_AREAS", DEFAULT_PRICE_AREAS)
    )
    dry_run = _parse_bool(safe_env.get("BACKTEST_DRY_RUN", DEFAULT_DRY_RUN))
    eds_request_delay_seconds = _parse_nonnegative_float(
        safe_env.get(
            "BACKTEST_EDS_REQUEST_DELAY_SECONDS",
            str(DEFAULT_EDS_REQUEST_DELAY_SECONDS),
        ),
        "BACKTEST_EDS_REQUEST_DELAY_SECONDS",
    )
    eds_max_retries = _parse_nonnegative_int(
        safe_env.get("BACKTEST_EDS_MAX_RETRIES", str(DEFAULT_EDS_MAX_RETRIES)),
        "BACKTEST_EDS_MAX_RETRIES",
    )

    _validate_date(start_date, "BACKTEST_START_DATE")
    if end_date.lower() == "now":
        resolved_end = _format_eds_datetime(_to_eds_timezone(now))
    else:
        _validate_date(end_date, "BACKTEST_END_DATE")
        resolved_end = end_date

    return BacktestInputConfig(
        start_date=start_date,
        end_date=end_date,
        resolved_end=resolved_end,
        price_areas=price_areas,
        dry_run=dry_run,
        eds_request_delay_seconds=eds_request_delay_seconds,
        eds_max_retries=eds_max_retries,
    )


def run_public_market_backtest_input(
    config: BacktestInputConfig,
    *,
    fetch: FetchFn,
    sleep_fn: SleepFn = time.sleep,
) -> BacktestInputSummary:
    results: list[DatasetAreaResult] = []

    for dataset in DATASETS:
        for price_area in config.price_areas:
            if results:
                _sleep_if_needed(config.eds_request_delay_seconds, sleep_fn)
            result = fetch_dataset_area(
                dataset=dataset,
                price_area=price_area,
                start_date=config.start_date,
                end=config.resolved_end,
                fetch=fetch,
                request_delay_seconds=config.eds_request_delay_seconds,
                sleep_fn=sleep_fn,
            )
            results.append(result)

    return build_summary(config, results)


def fetch_dataset_area(
    *,
    dataset: str,
    price_area: str,
    start_date: str,
    end: str,
    fetch: FetchFn,
    request_delay_seconds: float = 0.0,
    sleep_fn: SleepFn = time.sleep,
) -> DatasetAreaResult:
    all_records: list[Any] = []
    request_urls: list[str] = []
    normalized_by_id: dict[str, dict[str, Any]] = {}

    for chunk_start, chunk_end in build_request_chunks(start_date=start_date, end=end):
        if request_urls:
            _sleep_if_needed(request_delay_seconds, sleep_fn)
        request_url = build_backtest_eds_url(
            dataset=dataset,
            price_area=price_area,
            start=chunk_start,
            end=chunk_end,
        )
        request_urls.append(request_url)
        payload = fetch(request_url)
        records = extract_records(dict(payload))
        if not records:
            raise BacktestInputError(
                f"Required EDS records missing for {dataset} {price_area}"
            )
        all_records.extend(records)

        for normalized_row in _normalize_records(dataset, records):
            if normalized_row["price_area"] != price_area:
                raise BacktestInputError(
                    "EDS records did not match requested price area for "
                    f"{dataset} {price_area}"
                )
            normalized_by_id.setdefault(
                str(normalized_row["source_record_id"]),
                normalized_row,
            )

    normalized_rows = list(normalized_by_id.values())
    if not normalized_rows:
        raise BacktestInputError(
            f"Required normalized records missing for {dataset} {price_area}"
        )

    timestamps = sorted(str(row["timestamp_utc"]) for row in normalized_rows)
    return DatasetAreaResult(
        dataset=dataset,
        price_area=price_area,
        request_urls=tuple(request_urls),
        raw_record_count=len(all_records),
        normalized_record_count=len(normalized_rows),
        earliest_timestamp_utc=timestamps[0],
        latest_timestamp_utc=timestamps[-1],
        normalized_rows=tuple(normalized_rows),
    )


def build_backtest_eds_url(
    *,
    dataset: str,
    price_area: str,
    start: str,
    end: str,
    limit: int = MAX_LIMIT,
) -> str:
    base_url = build_eds_url(dataset, price_area=price_area, limit=limit)
    parsed = urlparse(base_url)
    query = dict(parse_qsl(parsed.query))
    query["start"] = start
    query["end"] = end
    query["sort"] = "TimeUTC ASC"
    url = urlunparse(parsed._replace(query=urlencode(query)))
    _require_eds_url(url)
    return url


def build_request_chunks(
    *,
    start_date: str,
    end: str,
    chunk_days: int = DEFAULT_CHUNK_DAYS,
) -> tuple[tuple[str, str], ...]:
    if chunk_days < 1:
        raise BacktestInputError("chunk_days must be positive")

    start_dt = _parse_eds_boundary(start_date)
    end_dt = _parse_eds_boundary(end)
    if end_dt <= start_dt:
        raise BacktestInputError("BACKTEST_END_DATE must be after BACKTEST_START_DATE")

    chunks: list[tuple[str, str]] = []
    chunk_start = start_dt
    while chunk_start < end_dt:
        chunk_end = min(chunk_start + timedelta(days=chunk_days), end_dt)
        chunks.append(
            (
                _format_eds_datetime(chunk_start),
                _format_eds_datetime(chunk_end),
            )
        )
        chunk_start = chunk_end

    return tuple(chunks)


def fetch_json(
    url: str,
    *,
    max_retries: int = DEFAULT_EDS_MAX_RETRIES,
    sleep_fn: SleepFn = time.sleep,
) -> JsonPayload:
    _require_eds_url(url)
    if max_retries < 0:
        raise BacktestInputError("BACKTEST_EDS_MAX_RETRIES must be non-negative")

    for attempt in range(max_retries + 1):
        try:
            return _fetch_json_once(url)
        except urllib.error.HTTPError as exc:
            if not _is_retryable_http_error(exc) or attempt >= max_retries:
                if _is_retryable_http_error(exc):
                    raise BacktestInputError(
                        "EDS request failed after retry limit was exhausted: "
                        f"HTTP {exc.code}"
                    ) from exc
                raise

            sleep_fn(_retry_delay_seconds(exc, attempt))

    raise BacktestInputError("EDS request failed after retry limit was exhausted")


def _fetch_json_once(url: str) -> JsonPayload:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": USER_AGENT},
    )

    with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        payload = json.loads(response.read().decode(charset, errors="replace"))

    if not isinstance(payload, Mapping):
        raise BacktestInputError("Energi Data Service response must be a JSON object")

    return payload


def build_summary(
    config: BacktestInputConfig,
    results: list[DatasetAreaResult],
) -> BacktestInputSummary:
    if not results:
        raise BacktestInputError("No EDS dataset results were produced")

    timestamps = [
        timestamp
        for result in results
        for timestamp in (result.earliest_timestamp_utc, result.latest_timestamp_utc)
    ]
    record_counts = {
        f"{result.dataset}:{result.price_area}": result.normalized_record_count
        for result in results
    }

    return BacktestInputSummary(
        period=f"{config.start_date} to {config.end_date}",
        price_areas=config.price_areas,
        datasets_requested=DATASETS,
        record_counts=record_counts,
        earliest_timestamp_utc=min(timestamps),
        latest_timestamp_utc=max(timestamps),
        dry_run=config.dry_run,
        source="Energi Data Service",
        note=(
            "public market/system-level data only, not customer-specific savings"
        ),
        file_written=False,
        database_write_performed=False,
    )


def print_summary(summary: BacktestInputSummary) -> None:
    print("Public market backtest input summary")
    print(f"period: {summary.period}")
    print(f"price_areas: {','.join(summary.price_areas)}")
    print(f"datasets_requested: {','.join(summary.datasets_requested)}")
    print("record_counts:")
    for key in sorted(summary.record_counts):
        print(f"  {key}: {summary.record_counts[key]}")
    print(f"earliest_timestamp_utc: {summary.earliest_timestamp_utc}")
    print(f"latest_timestamp_utc: {summary.latest_timestamp_utc}")
    print(f"dry_run: {str(summary.dry_run).lower()}")
    print(f"source: {summary.source}")
    print(f"note: {summary.note}")


def main() -> int:
    try:
        config = load_config()

        def fetch(url: str) -> JsonPayload:
            return fetch_json(url, max_retries=config.eds_max_retries)

        summary = run_public_market_backtest_input(config, fetch=fetch)
    except BacktestInputError as exc:
        print(f"Public market backtest input failed: {exc}", file=sys.stderr)
        return 1
    except urllib.error.HTTPError as exc:
        print(
            f"Public market backtest input failed: EDS HTTP {exc.code} {exc.reason}",
            file=sys.stderr,
        )
        return 1
    except urllib.error.URLError as exc:
        print(
            f"Public market backtest input failed: EDS API unreachable: {exc.reason}",
            file=sys.stderr,
        )
        return 1
    except TimeoutError:
        print(
            "Public market backtest input failed: EDS API unreachable: request timed out",
            file=sys.stderr,
        )
        return 1
    except json.JSONDecodeError as exc:
        print(
            f"Public market backtest input failed: invalid JSON from EDS: {exc}",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(f"Public market backtest input failed: {exc}", file=sys.stderr)
        return 1

    print_summary(summary)
    return 0


def _parse_price_areas(raw_value: str | None) -> tuple[str, ...]:
    values = tuple(
        price_area.strip().upper()
        for price_area in (raw_value or "").split(",")
        if price_area.strip()
    )
    if not values:
        raise BacktestInputError("At least one BACKTEST_PRICE_AREAS value is required")

    for price_area in values:
        if price_area not in ALLOWED_PRICE_AREAS:
            raise BacktestInputError(
                "BACKTEST_PRICE_AREAS supports only public DK1/DK2 price areas"
            )

    return values


def _parse_bool(raw_value: str | None) -> bool:
    normalized = (raw_value or "").strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise BacktestInputError("BACKTEST_DRY_RUN must be true or false")


def _parse_nonnegative_float(raw_value: str | None, env_name: str) -> float:
    try:
        parsed = float((raw_value or "").strip())
    except ValueError as exc:
        raise BacktestInputError(f"{env_name} must be a non-negative number") from exc

    if parsed < 0:
        raise BacktestInputError(f"{env_name} must be a non-negative number")

    return parsed


def _parse_nonnegative_int(raw_value: str | None, env_name: str) -> int:
    try:
        parsed = int((raw_value or "").strip())
    except ValueError as exc:
        raise BacktestInputError(f"{env_name} must be a non-negative integer") from exc

    if parsed < 0:
        raise BacktestInputError(f"{env_name} must be a non-negative integer")

    return parsed


def _validate_date(value: str, env_name: str) -> None:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise BacktestInputError(f"{env_name} must use YYYY-MM-DD") from exc


def _to_eds_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=EDS_TIMEZONE)

    return value.astimezone(EDS_TIMEZONE)


def _parse_eds_boundary(value: str) -> datetime:
    for date_format in ("%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            pass

    raise BacktestInputError(
        "EDS request boundaries must use YYYY-MM-DD or YYYY-MM-DDTHH:MM"
    )


def _format_eds_datetime(value: datetime) -> str:
    return value.replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")


def _sleep_if_needed(seconds: float, sleep_fn: SleepFn) -> None:
    if seconds > 0:
        sleep_fn(seconds)


def _is_retryable_http_error(exc: urllib.error.HTTPError) -> bool:
    return exc.code == 429 or 500 <= exc.code <= 599


def _retry_delay_seconds(exc: urllib.error.HTTPError, attempt: int) -> float:
    if exc.code == 429:
        retry_after = _parse_retry_after_seconds(exc)
        if retry_after is not None:
            return retry_after

    return min(60.0, float(2**attempt))


def _parse_retry_after_seconds(exc: urllib.error.HTTPError) -> float | None:
    raw_value = exc.headers.get("Retry-After") if exc.headers is not None else None
    if raw_value is None:
        return None

    try:
        seconds = float(raw_value)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(raw_value)
        except (TypeError, ValueError):
            return None

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        seconds = (retry_at - datetime.now(timezone.utc)).total_seconds()

    if seconds < 0:
        return 0.0

    return seconds


def _normalize_records(dataset: str, records: list[Any]) -> list[dict[str, Any]]:
    if dataset != DAY_AHEAD_PRICES:
        raise BacktestInputError(f"Unsupported dataset for v0 input: {dataset}")

    normalized_rows: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise BacktestInputError(f"EDS record {index} must be a JSON object")
        try:
            normalized_rows.append(normalize_day_ahead_price(record))
        except ValueError as exc:
            raise BacktestInputError(f"EDS record {index} is invalid: {exc}") from exc

    return normalized_rows


def _require_eds_url(url: str) -> None:
    parsed = urlparse(url)
    base_host = urlparse(BASE_URL).hostname
    if parsed.scheme != "https" or parsed.hostname != base_host or base_host != EDS_HOST:
        raise BacktestInputError("Refusing to call non-Energi Data Service URL")


if __name__ == "__main__":
    raise SystemExit(main())
