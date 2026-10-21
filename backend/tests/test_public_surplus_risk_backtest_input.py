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


public_surplus_risk_backtest_input = load_script_module(
    "public_surplus_risk_backtest_input.py"
)


def day_ahead_payload(price_area: str) -> dict:
    return {
        "records": [
            {
                "PriceArea": price_area,
                "TimeUTC": "2026-01-01T00:00:00",
                "DayAheadPriceDKK": 512.34,
                "DayAheadPriceEUR": 68.67,
            }
        ]
    }


def production_consumption_payload(price_area: str) -> dict:
    return {
        "records": [
            {
                "PriceArea": price_area,
                "HourUTC": "2026-01-01T00:00:00",
                "GrossConsumptionMWh": 1000,
                "CentralPowerMWh": 100,
                "LocalPowerMWh": 50,
                "OnshoreWindGe50kW_MWh": 200,
                "OnshoreWindLt50kW_MWh": 10,
                "OffshoreWindGe100MW_MWh": 300,
                "OffshoreWindLt100MW_MWh": 20,
                "SolarPowerGe10Lt40kW_MWh": 5,
                "SolarPowerGe40kW_MWh": 15,
                "SolarPowerLt10kW_MWh": 3,
                "SolarPowerSelfConMWh": 2,
                "ExchangeGE_MWh": -25,
                "ExchangeNO_MWh": 10,
                "ExchangeSE_MWh": 5,
                "ExchangeGB_MWh": None,
                "ExchangeNL_MWh": None,
                "ExchangeGreatBelt_MWh": 1,
            }
        ]
    }


def payload_for_url(url: str) -> dict:
    path = urlparse(url).path
    query = parse_qs(urlparse(url).query)
    price_area = json.loads(query["filter"][0])["PriceArea"][0]
    if path.endswith("/DayAheadPrices"):
        return day_ahead_payload(price_area)
    if path.endswith("/ProductionConsumptionSettlement"):
        return production_consumption_payload(price_area)
    raise AssertionError(f"unexpected dataset URL: {url}")


class FakeHeaders:
    def get_content_charset(self) -> str:
        return "utf-8"


class FakeResponse:
    headers = FakeHeaders()

    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def http_error(code: int, *, retry_after: str | None = None) -> urllib.error.HTTPError:
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError(
        "https://api.energidataservice.dk/dataset/ProductionConsumptionSettlement",
        code,
        "Too Many Requests",
        headers,
        io.BytesIO(b""),
    )


def config(**overrides: object):
    values = {
        "start_date": "2026-01-01",
        "end_date": "2026-01-02",
        "resolved_end": "2026-01-02",
        "price_areas": ("DK1",),
        "dry_run": True,
        "eds_request_delay_seconds": 0.0,
        "eds_max_retries": 3,
    }
    values.update(overrides)
    return public_surplus_risk_backtest_input.PublicSurplusRiskInputConfig(**values)


def test_default_config_uses_requested_defaults() -> None:
    loaded = public_surplus_risk_backtest_input.load_config(
        {},
        now_fn=lambda: datetime(2026, 7, 4, 12, 30, tzinfo=timezone.utc),
    )

    assert loaded.start_date == "2026-01-01"
    assert loaded.end_date == "now"
    assert loaded.resolved_end == "2026-07-04T14:30"
    assert loaded.price_areas == ("DK1", "DK2")
    assert loaded.dry_run is True
    assert loaded.eds_request_delay_seconds == 1.0
    assert loaded.eds_max_retries == 3


def test_price_area_validation_is_limited_to_dk1_dk2() -> None:
    with pytest.raises(
        public_surplus_risk_backtest_input.market_input.BacktestInputError,
        match="DK1/DK2",
    ):
        public_surplus_risk_backtest_input.load_config(
            {"BACKTEST_PRICE_AREAS": "DK1,SE3"}
        )


def test_day_ahead_prices_normalization() -> None:
    rows, warnings = public_surplus_risk_backtest_input.normalize_records(
        "DayAheadPrices",
        day_ahead_payload("DK1")["records"],
    )

    assert warnings == ()
    assert rows == [
        {
            "timestamp_utc": "2026-01-01T00:00:00",
            "price_area": "DK1",
            "day_ahead_price_eur_per_mwh": 68.67,
            "gross_consumption_mwh": None,
            "renewable_generation_mwh": None,
            "wind_generation_mwh": None,
            "solar_generation_mwh": None,
            "production_total_mwh": None,
            "source": "Energi Data Service:DayAheadPrices",
            "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
        }
    ]


def test_day_ahead_price_requires_time_utc_even_when_time_dk_is_present() -> None:
    record = day_ahead_payload("DK1")["records"][0].copy()
    record.pop("TimeUTC")
    record["TimeDK"] = "2026-07-01T14:00:00+02:00"
    with pytest.raises(ValueError, match="TimeUTC"):
        public_surplus_risk_backtest_input.normalize_day_ahead_price_record(record)


def test_day_ahead_price_uses_time_utc_and_preserves_raw_source_id() -> None:
    record = day_ahead_payload("DK1")["records"][0].copy()
    record["TimeUTC"] = "2026-07-01T14:00:00+02:00"
    record["TimeDK"] = "2026-07-01T15:00:00+02:00"
    normalized = public_surplus_risk_backtest_input.normalize_day_ahead_price_record(
        record
    )
    assert normalized["timestamp_utc"] == "2026-07-01T12:00:00"
    assert normalized["source_record_id"] == "DayAheadPrices:DK1:2026-07-01T14:00:00+02:00"


def test_production_consumption_settlement_normalization() -> None:
    rows, warnings = public_surplus_risk_backtest_input.normalize_records(
        "ProductionConsumptionSettlement",
        production_consumption_payload("DK1")["records"],
    )

    assert rows[0]["timestamp_utc"] == "2026-01-01T00:00:00"
    assert rows[0]["price_area"] == "DK1"
    assert rows[0]["day_ahead_price_eur_per_mwh"] is None
    assert rows[0]["gross_consumption_mwh"] == 1000
    assert rows[0]["wind_generation_mwh"] == 530
    assert rows[0]["solar_generation_mwh"] == 25
    assert rows[0]["renewable_generation_mwh"] == 555
    assert rows[0]["production_total_mwh"] == 705
    assert rows[0]["exchange_ge_mwh"] == -25
    assert rows[0]["exchange_no_mwh"] == 10
    assert rows[0]["exchange_se_mwh"] == 5
    assert rows[0]["exchange_great_belt_mwh"] == 1
    assert rows[0]["exchange_net_mwh"] == -9
    assert "source_record_id" in rows[0]
    assert any("ExchangeGB_MWh" in warning for warning in warnings)


def test_settlement_preserves_raw_source_id_after_utc_normalization() -> None:
    record = production_consumption_payload("DK1")["records"][0].copy()
    record["HourUTC"] = "2026-01-01T13:00:00+01:00"
    normalized, _ = (
        public_surplus_risk_backtest_input.normalize_production_consumption_record(
            record
        )
    )
    assert normalized["timestamp_utc"] == "2026-01-01T12:00:00"
    assert normalized["source_record_id"] == (
        "ProductionConsumptionSettlement:DK1:2026-01-01T13:00:00+01:00"
    )


@pytest.mark.parametrize(
    ("field", "source_timestamp", "expected_utc"),
    [
        ("TimeUTC", "2026-07-01T14:00:00+02:00", "2026-07-01T12:00:00"),
        ("HourUTC", "2026-01-01T13:00:00+01:00", "2026-01-01T12:00:00"),
        ("TimeUTC", "2026-03-29T01:00:00+01:00", "2026-03-29T00:00:00"),
        ("TimeUTC", "2026-03-29T03:00:00+02:00", "2026-03-29T01:00:00"),
        ("HourUTC", "2026-10-25T02:00:00+02:00", "2026-10-25T00:00:00"),
        ("HourUTC", "2026-10-25T02:00:00+01:00", "2026-10-25T01:00:00"),
    ],
)
def test_source_timestamps_preserve_instants(
    field: str, source_timestamp: str, expected_utc: str
) -> None:
    assert (
        public_surplus_risk_backtest_input.normalize_source_timestamp(
            source_timestamp, field
        )
        == expected_utc
    )


def test_naive_source_timestamp_uses_documented_utc_field_only() -> None:
    normalize = public_surplus_risk_backtest_input.normalize_source_timestamp
    assert normalize("2026-07-01T12:00:00", "TimeUTC") == "2026-07-01T12:00:00"
    with pytest.raises(ValueError, match="No UTC source contract"):
        normalize("2026-07-01T12:00:00", "TimeDK")


def test_offset_equivalent_source_rows_deduplicate_to_one_utc_instant() -> None:
    rows = [
        {**day_ahead_payload("DK1")["records"][0], "TimeUTC": timestamp}
        for timestamp in ("2026-07-01T14:00:00+02:00", "2026-07-01T12:00:00Z")
    ]
    result = public_surplus_risk_backtest_input.fetch_dataset_area(
        dataset="DayAheadPrices",
        price_area="DK1",
        start_date="2026-07-01",
        end="2026-07-02",
        fetch=lambda url: {"records": rows},
    )
    assert result.normalized_record_count == 1
    assert result.normalized_rows[0]["timestamp_utc"] == "2026-07-01T12:00:00"
    assert result.normalized_rows[0]["source_record_id"] == (
        "DayAheadPrices:DK1:2026-07-01T14:00:00+02:00"
    )


def test_repeated_local_hour_keeps_two_source_record_identities() -> None:
    rows = [
        {**day_ahead_payload("DK1")["records"][0], "TimeUTC": timestamp}
        for timestamp in ("2026-10-25T02:00:00+02:00", "2026-10-25T02:00:00+01:00")
    ]
    result = public_surplus_risk_backtest_input.fetch_dataset_area(
        dataset="DayAheadPrices",
        price_area="DK1",
        start_date="2026-10-25",
        end="2026-10-26",
        fetch=lambda url: {"records": rows},
    )
    assert result.normalized_record_count == 2
    assert [row["timestamp_utc"] for row in result.normalized_rows] == [
        "2026-10-25T00:00:00",
        "2026-10-25T01:00:00",
    ]
    assert len({row["source_record_id"] for row in result.normalized_rows}) == 2


def test_renewable_generation_is_derived_from_available_renewable_fields() -> None:
    record = {
        "PriceArea": "DK2",
        "HourUTC": "2026-01-01T01:00:00",
        "OnshoreWindGe50kW_MWh": 1,
        "SolarPowerGe40kW_MWh": 2,
        "HydroPowerMWh": 3,
    }

    normalized, warnings = (
        public_surplus_risk_backtest_input.normalize_production_consumption_record(
            record
        )
    )

    assert normalized["wind_generation_mwh"] == 1
    assert normalized["solar_generation_mwh"] == 2
    assert normalized["renewable_generation_mwh"] == 6
    assert normalized["production_total_mwh"] is None
    assert any("GrossConsumptionMWh" in warning for warning in warnings)


def test_missing_optional_fields_are_warnings_not_fake_values() -> None:
    record = {
        "PriceArea": "DK1",
        "HourUTC": "2026-01-01T02:00:00",
        "OnshoreWindGe50kW_MWh": 4,
    }

    normalized, warnings = (
        public_surplus_risk_backtest_input.normalize_production_consumption_record(
            record
        )
    )

    assert normalized["gross_consumption_mwh"] is None
    assert normalized["wind_generation_mwh"] == 4
    assert normalized["solar_generation_mwh"] is None
    assert normalized["production_total_mwh"] is None
    assert any("GrossConsumptionMWh" in warning for warning in warnings)
    assert any("SolarPowerGe40kW_MWh" in warning for warning in warnings)


def test_required_dataset_failure_fails_safely() -> None:
    with pytest.raises(
        public_surplus_risk_backtest_input.PublicSurplusRiskInputError,
        match="Required EDS records missing",
    ):
        public_surplus_risk_backtest_input.fetch_dataset_area(
            dataset="ProductionConsumptionSettlement",
            price_area="DK1",
            start_date="2026-01-01",
            end="2026-01-02",
            fetch=lambda url: {"records": []},
        )


def test_dry_run_does_not_write_files_or_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    summary = public_surplus_risk_backtest_input.run_public_surplus_risk_backtest_input(
        config(),
        fetch=payload_for_url,
        sleep_fn=lambda seconds: None,
    )

    assert list(tmp_path.iterdir()) == []
    assert summary.file_written is False
    assert summary.database_write_performed is False
    assert summary.dry_run is True


def test_no_customer_specific_savings_are_calculated(
    capsys: pytest.CaptureFixture[str],
) -> None:
    summary = public_surplus_risk_backtest_input.run_public_surplus_risk_backtest_input(
        config(price_areas=("DK1", "DK2")),
        fetch=payload_for_url,
        sleep_fn=lambda seconds: None,
    )

    public_surplus_risk_backtest_input.print_summary(summary)
    output = capsys.readouterr().out

    assert "not customer-specific savings" in output
    assert "full surplus-risk scoring comes next" in output
    for key in summary.normalized_row_counts:
        assert "savings" not in key.lower()
    for result_range in summary.dataset_timestamp_ranges.values():
        assert "savings" not in "".join(result_range).lower()


def test_fetches_both_required_datasets_for_dk1_and_dk2() -> None:
    seen_urls: list[str] = []

    def fetch(url: str) -> dict:
        seen_urls.append(url)
        return payload_for_url(url)

    summary = public_surplus_risk_backtest_input.run_public_surplus_risk_backtest_input(
        config(price_areas=("DK1", "DK2")),
        fetch=fetch,
        sleep_fn=lambda seconds: None,
    )

    assert summary.datasets_requested == (
        "DayAheadPrices",
        "ProductionConsumptionSettlement",
    )
    assert set(summary.record_counts) == {
        "DayAheadPrices:DK1",
        "DayAheadPrices:DK2",
        "ProductionConsumptionSettlement:DK1",
        "ProductionConsumptionSettlement:DK2",
    }
    assert any("/DayAheadPrices?" in url for url in seen_urls)
    assert any("/ProductionConsumptionSettlement?" in url for url in seen_urls)
    for url in seen_urls:
        assert url.startswith("https://api.energidataservice.dk/dataset/")


def test_production_consumption_settlement_url_uses_hour_utc_sort() -> None:
    url = public_surplus_risk_backtest_input.build_backtest_eds_url(
        dataset="ProductionConsumptionSettlement",
        price_area="DK1",
        start="2026-01-01T00:00",
        end="2026-01-02T00:00",
    )
    query = parse_qs(urlparse(url).query)

    assert query["start"] == ["2026-01-01T00:00"]
    assert query["end"] == ["2026-01-02T00:00"]
    assert query["sort"] == ["HourUTC ASC"]


def test_eds_429_retries_are_handled_by_shared_fetcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    sleeps: list[float] = []

    def fake_urlopen(request: object, timeout: int) -> FakeResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise http_error(429, retry_after="0.25")
        return FakeResponse(day_ahead_payload("DK1"))

    monkeypatch.setattr(
        public_surplus_risk_backtest_input.market_input.urllib.request,
        "urlopen",
        fake_urlopen,
    )
    url = public_surplus_risk_backtest_input.build_backtest_eds_url(
        dataset="DayAheadPrices",
        price_area="DK1",
        start="2026-01-01T00:00",
        end="2026-01-02T00:00",
    )

    payload = public_surplus_risk_backtest_input.market_input.fetch_json(
        url,
        max_retries=1,
        sleep_fn=sleeps.append,
    )

    assert payload == day_ahead_payload("DK1")
    assert calls == 2
    assert sleeps == [0.25]
