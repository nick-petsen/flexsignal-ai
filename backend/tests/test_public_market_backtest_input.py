from __future__ import annotations

import importlib.util
import io
import json
import sys
import urllib.error
from datetime import datetime, timezone
from email.message import Message
from pathlib import Path
from types import ModuleType
from urllib.parse import parse_qs, urlparse

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script_module(script_name: str) -> ModuleType:
    module_path = REPO_ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(
        script_name.removesuffix(".py"),
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


public_market_backtest_input = load_script_module("public_market_backtest_input.py")


def sample_payload(price_area: str, timestamp: str) -> dict:
    return {
        "records": [
            {
                "PriceArea": price_area,
                "TimeUTC": timestamp,
                "DayAheadPriceDKK": 512.34,
                "DayAheadPriceEUR": 68.67,
            }
        ]
    }


class FakeHeaders:
    def get_content_charset(self) -> str:
        return "utf-8"


class FakeResponse:
    headers = FakeHeaders()

    def __init__(self, payload: dict | bytes) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        if isinstance(self.payload, bytes):
            return self.payload

        return json.dumps(self.payload).encode("utf-8")


def http_error(code: int, *, retry_after: str | None = None) -> urllib.error.HTTPError:
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after

    return urllib.error.HTTPError(
        "https://api.energidataservice.dk/dataset/DayAheadPrices",
        code,
        "Too Many Requests",
        headers,
        io.BytesIO(b""),
    )


def test_default_config_uses_2026_01_01_and_dk1_dk2() -> None:
    config = public_market_backtest_input.load_config(
        {},
        now_fn=lambda: datetime(2026, 7, 4, 12, 30, tzinfo=timezone.utc),
    )

    assert config.start_date == "2026-01-01"
    assert config.end_date == "now"
    assert config.resolved_end == "2026-07-04T14:30"
    assert config.price_areas == ("DK1", "DK2")
    assert config.dry_run is True
    assert config.eds_request_delay_seconds == 1.0
    assert config.eds_max_retries == 3


def test_invalid_price_area_is_rejected() -> None:
    with pytest.raises(
        public_market_backtest_input.BacktestInputError,
        match="DK1/DK2",
    ):
        public_market_backtest_input.load_config({"BACKTEST_PRICE_AREAS": "DK1,SE3"})


def test_dry_run_does_not_write_files_or_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    config = public_market_backtest_input.BacktestInputConfig(
        start_date="2026-01-01",
        end_date="now",
        resolved_end="2026-07-04T14:30",
        price_areas=("DK1",),
        dry_run=True,
        eds_request_delay_seconds=0.0,
        eds_max_retries=3,
    )

    summary = public_market_backtest_input.run_public_market_backtest_input(
        config,
        fetch=lambda url: sample_payload("DK1", "2026-01-01T00:00:00"),
    )

    assert list(tmp_path.iterdir()) == []
    assert summary.file_written is False
    assert summary.database_write_performed is False
    assert summary.dry_run is True


def test_eds_response_is_parsed_into_normalized_rows() -> None:
    seen_urls: list[str] = []

    def fetch(url: str) -> dict:
        seen_urls.append(url)
        return sample_payload("DK1", "2026-01-01T00:00:00")

    result = public_market_backtest_input.fetch_dataset_area(
        dataset="DayAheadPrices",
        price_area="DK1",
        start_date="2026-01-01",
        end="2026-01-07",
        fetch=fetch,
    )

    assert result.raw_record_count == 1
    assert result.normalized_record_count == 1
    assert result.earliest_timestamp_utc == "2026-01-01T00:00:00"
    assert result.latest_timestamp_utc == "2026-01-01T00:00:00"
    assert result.normalized_rows == (
        {
            "price_area": "DK1",
            "timestamp_utc": "2026-01-01T00:00:00",
            "price_dkk_per_mwh": 512.34,
            "price_eur_per_mwh": 68.67,
            "source": "Energi Data Service:DayAheadPrices",
            "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
        },
    )
    assert seen_urls[0].startswith(
        "https://api.energidataservice.dk/dataset/DayAheadPrices?"
    )
    query = parse_qs(urlparse(seen_urls[0]).query)
    assert query["start"] == ["2026-01-01T00:00"]
    assert query["end"] == ["2026-01-07T00:00"]


def test_missing_records_fails_safely() -> None:
    with pytest.raises(
        public_market_backtest_input.BacktestInputError,
        match="Required EDS records missing",
    ):
        public_market_backtest_input.fetch_dataset_area(
            dataset="DayAheadPrices",
            price_area="DK1",
            start_date="2026-01-01",
            end="2026-01-07",
            fetch=lambda url: {"records": []},
        )


def test_summary_clearly_says_not_customer_specific_savings(
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = public_market_backtest_input.BacktestInputConfig(
        start_date="2026-01-01",
        end_date="now",
        resolved_end="2026-07-04T14:30",
        price_areas=("DK1", "DK2"),
        dry_run=True,
        eds_request_delay_seconds=1.0,
        eds_max_retries=3,
    )
    results = [
        public_market_backtest_input.DatasetAreaResult(
            dataset="DayAheadPrices",
            price_area="DK1",
            request_urls=(
                "https://api.energidataservice.dk/dataset/DayAheadPrices",
            ),
            raw_record_count=1,
            normalized_record_count=1,
            earliest_timestamp_utc="2026-01-01T00:00:00",
            latest_timestamp_utc="2026-01-01T00:00:00",
            normalized_rows=(),
        ),
        public_market_backtest_input.DatasetAreaResult(
            dataset="DayAheadPrices",
            price_area="DK2",
            request_urls=(
                "https://api.energidataservice.dk/dataset/DayAheadPrices",
            ),
            raw_record_count=1,
            normalized_record_count=1,
            earliest_timestamp_utc="2026-01-01T01:00:00",
            latest_timestamp_utc="2026-01-01T01:00:00",
            normalized_rows=(),
        ),
    ]

    summary = public_market_backtest_input.build_summary(config, results)
    public_market_backtest_input.print_summary(summary)
    output = capsys.readouterr().out

    assert "source: Energi Data Service" in output
    assert "public market/system-level data only" in output
    assert "not customer-specific savings" in output


def test_fetch_json_uses_mocked_http_response_and_rejects_invalid_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(request: object, timeout: int) -> FakeResponse:
        assert timeout == public_market_backtest_input.DEFAULT_TIMEOUT_SECONDS
        return FakeResponse(b"not-json")

    monkeypatch.setattr(
        public_market_backtest_input.urllib.request,
        "urlopen",
        fake_urlopen,
    )
    url = public_market_backtest_input.build_backtest_eds_url(
        dataset="DayAheadPrices",
        price_area="DK1",
        start="2026-01-01T00:00",
        end="2026-07-04T14:30",
    )

    with pytest.raises(json.JSONDecodeError):
        public_market_backtest_input.fetch_json(url)


def test_backtest_end_date_now_is_resolved_before_request() -> None:
    config = public_market_backtest_input.load_config(
        {"BACKTEST_PRICE_AREAS": "DK1"},
        now_fn=lambda: datetime(2026, 7, 4, 12, 30, tzinfo=timezone.utc),
    )
    seen_urls: list[str] = []

    def fetch(url: str) -> dict:
        seen_urls.append(url)
        return sample_payload("DK1", "2026-01-01T00:00:00")

    public_market_backtest_input.run_public_market_backtest_input(
        config,
        fetch=fetch,
        sleep_fn=lambda seconds: None,
    )

    assert seen_urls
    for url in seen_urls:
        query = parse_qs(urlparse(url).query)
        assert query["start"][0] != "now"
        assert query["end"][0] != "now"
        assert not query["end"][0].endswith("Z")
        assert query["end"][0].count(":") == 1


def test_long_date_ranges_are_chunked_safely() -> None:
    chunks = public_market_backtest_input.build_request_chunks(
        start_date="2026-01-01",
        end="2026-03-15",
    )

    assert chunks == (
        ("2026-01-01T00:00", "2026-02-01T00:00"),
        ("2026-02-01T00:00", "2026-03-04T00:00"),
        ("2026-03-04T00:00", "2026-03-15T00:00"),
    )


def test_no_duplicate_rows_are_counted_when_multiple_chunks_are_used() -> None:
    seen_urls: list[str] = []

    def fetch(url: str) -> dict:
        seen_urls.append(url)
        return sample_payload("DK1", "2026-01-01T00:00:00")

    result = public_market_backtest_input.fetch_dataset_area(
        dataset="DayAheadPrices",
        price_area="DK1",
        start_date="2026-01-01",
        end="2026-03-15",
        fetch=fetch,
    )

    assert len(seen_urls) == 3
    assert result.raw_record_count == 3
    assert result.normalized_record_count == 1


def test_default_config_does_not_build_invalid_eds_request_parameters() -> None:
    config = public_market_backtest_input.load_config(
        {},
        now_fn=lambda: datetime(2026, 7, 4, 12, 30, tzinfo=timezone.utc),
    )
    first_start, first_end = public_market_backtest_input.build_request_chunks(
        start_date=config.start_date,
        end=config.resolved_end,
    )[0]
    url = public_market_backtest_input.build_backtest_eds_url(
        dataset="DayAheadPrices",
        price_area="DK1",
        start=first_start,
        end=first_end,
    )
    query = parse_qs(urlparse(url).query)

    assert query["start"] == ["2026-01-01T00:00"]
    assert query["end"] == ["2026-02-01T00:00"]
    assert query["end"][0] != "now"
    assert not query["end"][0].endswith("Z")


def test_429_with_retry_after_is_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    responses: list[object] = [
        http_error(429, retry_after="2.5"),
        FakeResponse(sample_payload("DK1", "2026-01-01T00:00:00")),
    ]
    sleeps: list[float] = []

    def fake_urlopen(request: object, timeout: int) -> object:
        response = responses.pop(0)
        if isinstance(response, urllib.error.HTTPError):
            raise response

        return response

    monkeypatch.setattr(
        public_market_backtest_input.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    payload = public_market_backtest_input.fetch_json(
        "https://api.energidataservice.dk/dataset/DayAheadPrices?limit=1",
        max_retries=1,
        sleep_fn=sleeps.append,
    )

    assert payload["records"][0]["PriceArea"] == "DK1"
    assert sleeps == [2.5]
    assert responses == []


def test_429_without_retry_after_uses_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    responses: list[object] = [
        http_error(429),
        FakeResponse(sample_payload("DK1", "2026-01-01T00:00:00")),
    ]
    sleeps: list[float] = []

    def fake_urlopen(request: object, timeout: int) -> object:
        response = responses.pop(0)
        if isinstance(response, urllib.error.HTTPError):
            raise response

        return response

    monkeypatch.setattr(
        public_market_backtest_input.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    payload = public_market_backtest_input.fetch_json(
        "https://api.energidataservice.dk/dataset/DayAheadPrices?limit=1",
        max_retries=1,
        sleep_fn=sleeps.append,
    )

    assert payload["records"][0]["PriceArea"] == "DK1"
    assert sleeps == [1.0]


def test_exhausted_429_retries_fails_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []

    def fake_urlopen(request: object, timeout: int) -> object:
        raise http_error(429)

    monkeypatch.setattr(
        public_market_backtest_input.urllib.request,
        "urlopen",
        fake_urlopen,
    )

    with pytest.raises(
        public_market_backtest_input.BacktestInputError,
        match="retry limit was exhausted: HTTP 429",
    ):
        public_market_backtest_input.fetch_json(
            "https://api.energidataservice.dk/dataset/DayAheadPrices?limit=1",
            max_retries=2,
            sleep_fn=sleeps.append,
        )

    assert sleeps == [1.0, 2.0]


def test_request_delay_is_applied_between_chunks() -> None:
    sleeps: list[float] = []

    public_market_backtest_input.fetch_dataset_area(
        dataset="DayAheadPrices",
        price_area="DK1",
        start_date="2026-01-01",
        end="2026-03-15",
        fetch=lambda url: sample_payload("DK1", "2026-01-01T00:00:00"),
        request_delay_seconds=0.25,
        sleep_fn=sleeps.append,
    )

    assert sleeps == [0.25, 0.25]
