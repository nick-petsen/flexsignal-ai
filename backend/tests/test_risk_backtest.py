from __future__ import annotations

import inspect

from app.risk import evaluate_risk_backtest
from app.risk import backtest


def _low_risk_row(timestamp: str = "2026-01-01T00:00:00Z") -> dict:
    return {
        "price_area": "DK1",
        "timestamp_utc": timestamp,
        "price_dkk_per_mwh": 500,
        "production_mw": 100,
        "consumption_mw": 95,
        "wind_onshore_mw": 10,
        "wind_offshore_mw": 5,
        "solar_mw": 5,
    }


def _medium_risk_row(timestamp: str = "2026-01-01T01:00:00Z") -> dict:
    return {
        "price_area": "DK2",
        "timestamp_utc": timestamp,
        "price_dkk_per_mwh": 50,
        "production_mw": 100,
        "consumption_mw": 90,
        "wind_onshore_mw": 30,
        "wind_offshore_mw": 25,
        "solar_mw": 5,
    }


def _high_risk_row(timestamp: str = "2026-01-01T02:00:00Z") -> dict:
    return {
        "price_area": "DK1",
        "timestamp_utc": timestamp,
        "price_dkk_per_mwh": -25,
        "production_mw": 100,
        "consumption_mw": 80,
        "wind_onshore_mw": 50,
        "wind_offshore_mw": 30,
        "solar_mw": 5,
    }


def test_empty_input_returns_zero_summary() -> None:
    result = evaluate_risk_backtest([])

    assert result == {
        "total_rows": 0,
        "evaluated_rows": 0,
        "failed_rows": 0,
        "risk_level_counts": {"low": 0, "medium": 0, "high": 0},
        "average_risk_score": 0.0,
        "average_confidence_score": 0.0,
        "reason_code_counts": {},
        "missing_price_count": 0,
        "missing_generation_data_count": 0,
        "failed_row_errors": [],
        "model_version": "rule-engine-v0",
        "decision_support_only": True,
    }


def test_all_low_risk_rows_are_counted() -> None:
    result = evaluate_risk_backtest(
        [
            _low_risk_row("2026-01-01T00:00:00Z"),
            _low_risk_row("2026-01-01T01:00:00Z"),
        ]
    )

    assert result["total_rows"] == 2
    assert result["evaluated_rows"] == 2
    assert result["failed_rows"] == 0
    assert result["risk_level_counts"] == {"low": 2, "medium": 0, "high": 0}


def test_mixed_low_medium_high_rows_are_counted() -> None:
    result = evaluate_risk_backtest(
        [_low_risk_row(), _medium_risk_row(), _high_risk_row()]
    )

    assert result["risk_level_counts"] == {"low": 1, "medium": 1, "high": 1}


def test_average_risk_score_calculation() -> None:
    result = evaluate_risk_backtest(
        [_low_risk_row(), _medium_risk_row(), _high_risk_row()]
    )

    assert result["average_risk_score"] == 40.0


def test_reason_code_counts_are_aggregated() -> None:
    result = evaluate_risk_backtest(
        [_low_risk_row(), _medium_risk_row(), _high_risk_row()]
    )

    assert result["reason_code_counts"]["NORMAL_PRICE"] == 1
    assert result["reason_code_counts"]["LOW_PRICE"] == 1
    assert result["reason_code_counts"]["NEGATIVE_PRICE"] == 1
    assert result["reason_code_counts"]["LOW_RENEWABLE_SHARE"] == 1
    assert result["reason_code_counts"]["MODERATE_RENEWABLE_SHARE"] == 1
    assert result["reason_code_counts"]["HIGH_RENEWABLE_SHARE"] == 1


def test_missing_price_count() -> None:
    row = _low_risk_row()
    row.pop("price_dkk_per_mwh")

    result = evaluate_risk_backtest([row, _low_risk_row()])

    assert result["missing_price_count"] == 1
    assert result["reason_code_counts"]["MISSING_PRICE"] == 1


def test_missing_generation_data_count() -> None:
    row = _low_risk_row()
    row.pop("production_mw")

    result = evaluate_risk_backtest([row, _low_risk_row()])

    assert result["missing_generation_data_count"] == 1
    assert (
        result["reason_code_counts"]["MISSING_PRODUCTION_OR_RENEWABLE_DATA"]
        == 1
    )


def test_invalid_row_is_captured_as_failed_row() -> None:
    result = evaluate_risk_backtest(
        [
            _low_risk_row(),
            {"price_area": "SE3", "timestamp_utc": "2026-01-01T03:00:00Z"},
            _medium_risk_row(),
        ]
    )

    assert result["total_rows"] == 3
    assert result["evaluated_rows"] == 2
    assert result["failed_rows"] == 1
    assert result["failed_row_errors"] == [
        {
            "row_index": 1,
            "error_type": "ValueError",
            "message": "price_area must be DK1 or DK2",
        }
    ]


def test_decision_support_only_true() -> None:
    result = evaluate_risk_backtest([_low_risk_row()])

    assert result["decision_support_only"] is True


def test_no_db_api_network_or_control_behavior() -> None:
    source = inspect.getsource(backtest)

    forbidden_terms = (
        "DATABASE_URL",
        "FastAPI",
        "psycopg",
        "requests",
        "httpx",
        "connect(",
        "execute(",
        "dispatch",
        "activation",
        "control",
    )

    for forbidden_term in forbidden_terms:
        assert forbidden_term not in source
