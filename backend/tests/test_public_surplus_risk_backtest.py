from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
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


public_surplus_risk_backtest = load_script_module(
    "public_surplus_risk_backtest.py"
)


def price_row(price_area: str, timestamp: str, price: float | None) -> dict:
    return {
        "price_area": price_area,
        "timestamp_utc": timestamp,
        "day_ahead_price_eur_per_mwh": price,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": f"DayAheadPrices:{price_area}:{timestamp}",
    }


def settlement_row(
    price_area: str,
    timestamp: str,
    gross_consumption: float | None,
    renewable_generation: float | None,
) -> dict:
    return {
        "price_area": price_area,
        "timestamp_utc": timestamp,
        "gross_consumption_mwh": gross_consumption,
        "renewable_generation_mwh": renewable_generation,
        "source": "Energi Data Service:ProductionConsumptionSettlement",
        "source_record_id": (
            f"ProductionConsumptionSettlement:{price_area}:{timestamp}"
        ),
    }


def day_ahead_payload(price_area: str) -> dict:
    return {
        "records": [
            {
                "PriceArea": price_area,
                "TimeUTC": "2026-01-01T00:00:00",
                "DayAheadPriceDKK": -37.3,
                "DayAheadPriceEUR": -5.0,
            },
            {
                "PriceArea": price_area,
                "TimeUTC": "2026-01-01T01:00:00",
                "DayAheadPriceDKK": 149.2,
                "DayAheadPriceEUR": 20.0,
            },
            {
                "PriceArea": price_area,
                "TimeUTC": "2026-01-01T02:00:00",
                "DayAheadPriceDKK": 373.0,
                "DayAheadPriceEUR": 50.0,
            },
        ]
    }


def settlement_payload(price_area: str) -> dict:
    return {
        "records": [
            {
                "PriceArea": price_area,
                "HourUTC": "2026-01-01T00:00:00",
                "GrossConsumptionMWh": 100,
                "OnshoreWindGe50kW_MWh": 90,
            },
            {
                "PriceArea": price_area,
                "HourUTC": "2026-01-01T01:00:00",
                "GrossConsumptionMWh": 100,
                "OnshoreWindGe50kW_MWh": 70,
            },
            {
                "PriceArea": price_area,
                "HourUTC": "2026-01-01T02:00:00",
                "GrossConsumptionMWh": 100,
                "OnshoreWindGe50kW_MWh": 20,
            },
        ]
    }


def payload_for_url(url: str) -> dict:
    parsed = urlparse(url)
    price_area = json.loads(parse_qs(parsed.query)["filter"][0])["PriceArea"][0]
    if parsed.path.endswith("/DayAheadPrices"):
        return day_ahead_payload(price_area)
    if parsed.path.endswith("/ProductionConsumptionSettlement"):
        return settlement_payload(price_area)
    raise AssertionError(f"unexpected URL: {url}")


def config(**overrides: object):
    values = {
        "start_date": "2026-01-01",
        "end_date": "2026-01-02",
        "resolved_end": "2026-01-02",
        "price_areas": ("DK1",),
        "dry_run": True,
        "eds_request_delay_seconds": 0.0,
        "eds_max_retries": 0,
        "low_price_threshold_eur_per_mwh": 25.0,
        "renewable_share_medium_threshold": 0.65,
        "renewable_share_high_threshold": 0.80,
    }
    values.update(overrides)
    return public_surplus_risk_backtest.PublicSurplusRiskBacktestConfig(**values)


def test_default_config_uses_requested_defaults() -> None:
    loaded = public_surplus_risk_backtest.load_config(
        {},
        now_fn=lambda: datetime(2026, 7, 4, 12, 30, tzinfo=timezone.utc),
    )

    assert loaded.start_date == "2026-01-01"
    assert loaded.end_date == "now"
    assert loaded.resolved_end == "2026-07-04T14:30"
    assert loaded.price_areas == ("DK1", "DK2")
    assert loaded.dry_run is True
    assert loaded.low_price_threshold_eur_per_mwh == 25.0
    assert loaded.renewable_share_medium_threshold == 0.65
    assert loaded.renewable_share_high_threshold == 0.80
    assert loaded.eds_request_delay_seconds == 1.0
    assert loaded.eds_max_retries == 3


def test_hourly_price_aggregation_averages_subhourly_rows() -> None:
    hourly_prices, skipped = public_surplus_risk_backtest.aggregate_hourly_prices(
        [
            price_row("DK1", "2026-01-01T00:00:00", 10.0),
            price_row("DK1", "2026-01-01T00:15:00", 20.0),
            price_row("DK1", "2026-01-01T01:00:00", 30.0),
        ],
        price_area="DK1",
    )

    assert skipped == 0
    assert hourly_prices["2026-01-01T00:00:00"] == pytest.approx(15.0)
    assert hourly_prices["2026-01-01T01:00:00"] == pytest.approx(30.0)


def test_joining_price_and_settlement_rows_calculates_renewable_share() -> None:
    joined_rows, skipped = public_surplus_risk_backtest.join_and_score_hourly_rows(
        price_area="DK1",
        price_rows=[price_row("DK1", "2026-01-01T00:15:00", 10.0)],
        settlement_rows=[settlement_row("DK1", "2026-01-01T00:00:00", 100.0, 75.0)],
        low_price_threshold_eur_per_mwh=25.0,
        renewable_share_medium_threshold=0.65,
        renewable_share_high_threshold=0.80,
    )

    assert skipped == 0
    assert len(joined_rows) == 1
    assert joined_rows[0].timestamp_utc == "2026-01-01T00:00:00"
    assert joined_rows[0].price_eur_per_mwh == 10.0
    assert joined_rows[0].gross_consumption_mwh == 100.0
    assert joined_rows[0].renewable_generation_mwh == 75.0
    assert joined_rows[0].renewable_share == pytest.approx(0.75)


def test_low_medium_high_risk_scoring_is_deterministic() -> None:
    low = public_surplus_risk_backtest.score_joined_row(
        price_eur_per_mwh=50.0,
        gross_consumption_mwh=100.0,
        renewable_generation_mwh=30.0,
        renewable_share=0.30,
        low_price_threshold_eur_per_mwh=25.0,
        renewable_share_medium_threshold=0.65,
        renewable_share_high_threshold=0.80,
    )
    medium = public_surplus_risk_backtest.score_joined_row(
        price_eur_per_mwh=20.0,
        gross_consumption_mwh=100.0,
        renewable_generation_mwh=70.0,
        renewable_share=0.70,
        low_price_threshold_eur_per_mwh=25.0,
        renewable_share_medium_threshold=0.65,
        renewable_share_high_threshold=0.80,
    )
    high = public_surplus_risk_backtest.score_joined_row(
        price_eur_per_mwh=-5.0,
        gross_consumption_mwh=100.0,
        renewable_generation_mwh=90.0,
        renewable_share=0.90,
        low_price_threshold_eur_per_mwh=25.0,
        renewable_share_medium_threshold=0.65,
        renewable_share_high_threshold=0.80,
    )

    assert low == (0, "low", ())
    assert medium == (
        45,
        "medium",
        ("low_price", "medium_renewable_share"),
    )
    assert high == (
        95,
        "high",
        ("negative_price", "low_price", "high_renewable_share"),
    )


def test_renewable_generation_above_gross_consumption_increases_risk() -> None:
    score, risk_level, reason_codes = public_surplus_risk_backtest.score_joined_row(
        price_eur_per_mwh=40.0,
        gross_consumption_mwh=100.0,
        renewable_generation_mwh=110.0,
        renewable_share=1.10,
        low_price_threshold_eur_per_mwh=25.0,
        renewable_share_medium_threshold=0.65,
        renewable_share_high_threshold=0.80,
    )

    assert score == 65
    assert risk_level == "medium"
    assert "renewable_generation_above_consumption" in reason_codes


def test_consecutive_medium_and_high_rows_are_grouped_into_windows() -> None:
    rows = (
        public_surplus_risk_backtest.JoinedHourlyRiskRow(
            "DK1",
            "2026-01-01T00:00:00",
            -5.0,
            100.0,
            90.0,
            0.90,
            95,
            "high",
            ("negative_price",),
        ),
        public_surplus_risk_backtest.JoinedHourlyRiskRow(
            "DK1",
            "2026-01-01T01:00:00",
            20.0,
            100.0,
            70.0,
            0.70,
            45,
            "medium",
            ("low_price",),
        ),
        public_surplus_risk_backtest.JoinedHourlyRiskRow(
            "DK1",
            "2026-01-01T03:00:00",
            20.0,
            100.0,
            70.0,
            0.70,
            45,
            "medium",
            ("low_price",),
        ),
    )

    windows = public_surplus_risk_backtest.group_risk_windows(rows)

    assert len(windows) == 2
    assert windows[0].start_timestamp_utc == "2026-01-01T00:00:00"
    assert windows[0].end_timestamp_utc == "2026-01-01T01:00:00"
    assert windows[0].hour_count == 2
    assert windows[0].highest_risk_score == 95
    assert windows[1].start_timestamp_utc == "2026-01-01T03:00:00"


def test_skipped_unjoinable_rows_are_reported() -> None:
    joined_rows, skipped = public_surplus_risk_backtest.join_and_score_hourly_rows(
        price_area="DK1",
        price_rows=[
            price_row("DK1", "2026-01-01T00:00:00", 10.0),
            price_row("DK1", "2026-01-01T02:00:00", 10.0),
        ],
        settlement_rows=[
            settlement_row("DK1", "2026-01-01T00:00:00", 100.0, 75.0),
            settlement_row("DK1", "2026-01-01T01:00:00", 100.0, 75.0),
            settlement_row("DK1", "2026-01-01T03:00:00", 100.0, None),
        ],
        low_price_threshold_eur_per_mwh=25.0,
        renewable_share_medium_threshold=0.65,
        renewable_share_high_threshold=0.80,
    )

    assert len(joined_rows) == 1
    assert skipped == 3


def test_missing_optional_values_do_not_create_fake_data() -> None:
    joined_rows, skipped = public_surplus_risk_backtest.join_and_score_hourly_rows(
        price_area="DK1",
        price_rows=[price_row("DK1", "2026-01-01T00:00:00", 10.0)],
        settlement_rows=[settlement_row("DK1", "2026-01-01T00:00:00", None, 75.0)],
        low_price_threshold_eur_per_mwh=25.0,
        renewable_share_medium_threshold=0.65,
        renewable_share_high_threshold=0.80,
    )

    assert joined_rows == ()
    assert skipped == 1


def test_run_uses_mocked_rows_and_dry_run_does_not_write_files_or_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    summary = public_surplus_risk_backtest.run_public_surplus_risk_backtest(
        config(),
        fetch=payload_for_url,
        sleep_fn=lambda seconds: None,
    )

    assert list(tmp_path.iterdir()) == []
    assert summary.dry_run is True
    assert summary.file_written is False
    assert summary.database_write_performed is False
    assert summary.datasets == (
        "DayAheadPrices",
        "ProductionConsumptionSettlement",
    )
    assert summary.area_summaries[0].joined_hour_count == 3
    assert summary.area_summaries[0].high_risk_hour_count == 1
    assert summary.area_summaries[0].medium_risk_hour_count == 1
    assert summary.area_summaries[0].risk_window_count == 1


def test_no_customer_specific_savings_are_calculated(
    capsys: pytest.CaptureFixture[str],
) -> None:
    summary = public_surplus_risk_backtest.run_public_surplus_risk_backtest(
        config(),
        fetch=payload_for_url,
        sleep_fn=lambda seconds: None,
    )

    public_surplus_risk_backtest.print_summary(summary)
    output = capsys.readouterr().out

    assert "not customer-specific savings" in output
    assert "customer-specific results require customer load, asset, tariff" in output
    reason_text = " ".join(
        reason_code
        for row in summary.joined_rows
        for reason_code in row.reason_codes
    )
    assert "savings" not in reason_text
    assert not hasattr(summary.area_summaries[0], "customer_savings")


def test_notes_include_not_customer_specific_savings_and_no_control() -> None:
    notes = public_surplus_risk_backtest.NOTES

    assert "not customer-specific savings" in notes
    assert "no automatic control, dispatch, or activation" in notes
    assert "read-only decision support" in notes
