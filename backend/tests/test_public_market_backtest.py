from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

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


public_market_backtest = load_script_module("public_market_backtest.py")


def normalized_row(
    price_area: str,
    timestamp: str,
    price_eur_per_mwh: float,
) -> dict:
    return {
        "price_area": price_area,
        "timestamp_utc": timestamp,
        "price_dkk_per_mwh": price_eur_per_mwh * 7.46,
        "price_eur_per_mwh": price_eur_per_mwh,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": f"DayAheadPrices:{price_area}:{timestamp}",
    }


def sample_payload(price_area: str) -> dict:
    return {
        "records": [
            {
                "PriceArea": price_area,
                "TimeUTC": "2026-01-01T00:00:00",
                "DayAheadPriceDKK": -74.6,
                "DayAheadPriceEUR": -10.0,
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


def backtest_config(**overrides: object):
    values = {
        "start_date": "2026-01-01",
        "end_date": "2026-01-02",
        "resolved_end": "2026-01-02",
        "price_areas": ("DK1",),
        "dry_run": True,
        "eds_request_delay_seconds": 0.0,
        "eds_max_retries": 0,
        "low_price_threshold_eur_per_mwh": 25.0,
    }
    values.update(overrides)
    return public_market_backtest.PublicMarketBacktestConfig(**values)


def test_negative_low_average_min_max_and_scenario_are_calculated() -> None:
    result = public_market_backtest.calculate_price_area_backtest(
        "DK1",
        (
            normalized_row("DK1", "2026-01-01T00:00:00", -10.0),
            normalized_row("DK1", "2026-01-01T01:00:00", 20.0),
            normalized_row("DK1", "2026-01-01T02:00:00", 50.0),
        ),
        low_price_threshold_eur_per_mwh=25.0,
    )

    assert result.record_count == 3
    assert result.earliest_timestamp_utc == "2026-01-01T00:00:00"
    assert result.latest_timestamp_utc == "2026-01-01T02:00:00"
    assert result.average_price_eur_per_mwh == pytest.approx(20.0)
    assert result.minimum_price_eur_per_mwh == -10.0
    assert result.maximum_price_eur_per_mwh == 50.0
    assert result.negative_price_record_count == 1
    assert result.low_price_record_count == 2
    assert result.low_price_share == pytest.approx(2 / 3)
    assert result.opportunity_eur_per_mwh_signal == pytest.approx(15.0)
    assert result.scenario_value_per_1_mwh == pytest.approx(15.0)
    assert "scenario only" in result.scenario_label
    assert "not revenue, profit, savings" in result.scenario_label


def test_run_uses_mocked_eds_rows_and_keeps_dry_run_no_write_flags(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    summary = public_market_backtest.run_public_market_backtest(
        backtest_config(),
        fetch=lambda url: sample_payload("DK1"),
        sleep_fn=lambda seconds: None,
    )

    assert list(tmp_path.iterdir()) == []
    assert summary.dry_run is True
    assert summary.file_written is False
    assert summary.database_write_performed is False
    assert summary.dataset == "DayAheadPrices"
    assert summary.area_results[0].record_count == 3


def test_summary_notes_exclude_customer_specific_savings_and_state_v0_limit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    summary = public_market_backtest.run_public_market_backtest(
        backtest_config(),
        fetch=lambda url: sample_payload("DK1"),
        sleep_fn=lambda seconds: None,
    )

    public_market_backtest.print_summary(summary)
    output = capsys.readouterr().out

    assert "public market/system-level backtest only" in output
    assert "not customer-specific savings" in output
    assert "customer load, asset, tariff, and operational data" in output
    assert "DayAheadPrices" in output
    assert "not full surplus-production data" in output


def test_invalid_price_area_is_rejected() -> None:
    with pytest.raises(
        public_market_backtest.backtest_input.BacktestInputError,
        match="DK1/DK2",
    ):
        public_market_backtest.load_config({"BACKTEST_PRICE_AREAS": "SE3"})


def test_missing_records_fails_safely() -> None:
    with pytest.raises(
        public_market_backtest.backtest_input.BacktestInputError,
        match="Required EDS records missing",
    ):
        public_market_backtest.run_public_market_backtest(
            backtest_config(),
            fetch=lambda url: {"records": []},
            sleep_fn=lambda seconds: None,
        )


def test_invalid_price_values_fail_safely() -> None:
    with pytest.raises(
        public_market_backtest.PublicMarketBacktestError,
        match="invalid price_eur_per_mwh",
    ):
        public_market_backtest.calculate_price_area_backtest(
            "DK1",
            (
                {
                    "price_area": "DK1",
                    "timestamp_utc": "2026-01-01T00:00:00",
                    "price_eur_per_mwh": "not-a-number",
                },
            ),
            low_price_threshold_eur_per_mwh=25.0,
        )


def test_low_threshold_default_is_25_eur_per_mwh() -> None:
    config = public_market_backtest.load_config(
        {
            "BACKTEST_START_DATE": "2026-01-01",
            "BACKTEST_END_DATE": "2026-01-02",
            "BACKTEST_PRICE_AREAS": "DK1",
            "BACKTEST_DRY_RUN": "true",
        }
    )

    assert config.low_price_threshold_eur_per_mwh == 25.0


def test_invalid_json_from_eds_fails_safely(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def raise_invalid_json(url: str, *, max_retries: int = 0) -> dict:
        raise json.JSONDecodeError("invalid", "not-json", 0)

    monkeypatch.setenv("BACKTEST_START_DATE", "2026-01-01")
    monkeypatch.setenv("BACKTEST_END_DATE", "2026-01-02")
    monkeypatch.setenv("BACKTEST_PRICE_AREAS", "DK1")
    monkeypatch.setenv("BACKTEST_DRY_RUN", "true")
    monkeypatch.setattr(
        public_market_backtest.backtest_input,
        "fetch_json",
        raise_invalid_json,
    )

    exit_code = public_market_backtest.main()
    stderr = capsys.readouterr().err

    assert exit_code == 1
    assert "invalid JSON from EDS" in stderr
