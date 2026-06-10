from __future__ import annotations

import inspect

import pytest

from app.risk import evaluate_risk_backtest, pair_rows_by_nearest_timestamp
from app.risk import row_pairing


def _spot_row(timestamp: str, price: float = -25) -> dict:
    return {
        "price_area": "DK1",
        "timestamp_utc": timestamp,
        "price_dkk_per_mwh": price,
    }


def _power_row(timestamp: str) -> dict:
    return {
        "price_area": "DK1",
        "timestamp_utc": timestamp,
        "production_mw": 100,
        "consumption_mw": 80,
        "wind_onshore_mw": 50,
        "wind_offshore_mw": 30,
        "solar_mw": 5,
        "exchange_net_mw": -10,
    }


def test_nearest_timestamp_match_uses_power_timeline_order() -> None:
    result = pair_rows_by_nearest_timestamp(
        spot_price_rows=[
            _spot_row("2026-01-01T00:00:00Z", price=10),
            _spot_row("2026-01-01T00:10:00+00:00", price=20),
        ],
        power_balance_rows=[
            _power_row("2026-01-01T00:06:00Z"),
            _power_row("2026-01-01T00:01:00Z"),
        ],
        price_area="DK1",
    )

    assert [row["timestamp_utc"] for row in result] == [
        "2026-01-01T00:06:00Z",
        "2026-01-01T00:01:00Z",
    ]
    assert [row["price_dkk_per_mwh"] for row in result] == [20, 10]


def test_deterministic_tie_break_prefers_earlier_timestamp_then_original_order() -> None:
    earlier_timestamp_result = pair_rows_by_nearest_timestamp(
        spot_price_rows=[
            _spot_row("2026-01-01T00:00:00Z", price=10),
            _spot_row("2026-01-01T00:10:00Z", price=20),
        ],
        power_balance_rows=[_power_row("2026-01-01T00:05:00Z")],
        price_area="DK1",
    )

    same_timestamp_result = pair_rows_by_nearest_timestamp(
        spot_price_rows=[
            _spot_row("2026-01-01T00:00:00Z", price=30),
            _spot_row("2026-01-01T00:00:00Z", price=40),
        ],
        power_balance_rows=[_power_row("2026-01-01T00:01:00Z")],
        price_area="DK1",
    )

    assert earlier_timestamp_result[0]["price_dkk_per_mwh"] == 10
    assert same_timestamp_result[0]["price_dkk_per_mwh"] == 30


def test_no_spot_rows_creates_power_only_composed_rows() -> None:
    result = pair_rows_by_nearest_timestamp(
        spot_price_rows=[],
        power_balance_rows=[
            _power_row("2026-01-01T00:00:00Z"),
            _power_row("2026-01-01T00:05:00Z"),
        ],
        price_area="DK1",
    )

    assert len(result) == 2
    assert "price_dkk_per_mwh" not in result[0]
    assert result[0]["production_mw"] == 100
    assert result[1]["timestamp_utc"] == "2026-01-01T00:05:00Z"


def test_no_power_rows_creates_spot_only_composed_rows() -> None:
    result = pair_rows_by_nearest_timestamp(
        spot_price_rows=[
            _spot_row("2026-01-01T00:00:00Z", price=10),
            _spot_row("2026-01-01T01:00:00Z", price=20),
        ],
        power_balance_rows=[],
        price_area="DK1",
    )

    assert result == [
        {
            "price_area": "DK1",
            "timestamp_utc": "2026-01-01T00:00:00Z",
            "price_dkk_per_mwh": 10,
        },
        {
            "price_area": "DK1",
            "timestamp_utc": "2026-01-01T01:00:00Z",
            "price_dkk_per_mwh": 20,
        },
    ]


@pytest.mark.parametrize(
    "bad_row",
    [
        {"price_area": "DK1", "timestamp_utc": "not-a-timestamp"},
        {"price_area": "DK1"},
        {"price_area": "DK1", "timestamp_utc": "2026-01-01T00:00:00"},
    ],
)
def test_invalid_timestamp_rejected(bad_row: dict) -> None:
    with pytest.raises(ValueError, match="timestamp_utc"):
        pair_rows_by_nearest_timestamp(
            spot_price_rows=[bad_row],
            power_balance_rows=[_power_row("2026-01-01T00:00:00Z")],
            price_area="DK1",
        )


def test_invalid_price_area_rejected() -> None:
    with pytest.raises(ValueError, match="price_area must be DK1 or DK2"):
        pair_rows_by_nearest_timestamp(
            spot_price_rows=[_spot_row("2026-01-01T00:00:00Z")],
            power_balance_rows=[_power_row("2026-01-01T00:00:00Z")],
            price_area="SE3",
        )


def test_helper_output_can_feed_evaluate_risk_backtest() -> None:
    rows = pair_rows_by_nearest_timestamp(
        spot_price_rows=[_spot_row("2026-01-01T00:00:00Z")],
        power_balance_rows=[_power_row("2026-01-01T00:05:00Z")],
        price_area="DK1",
    )

    result = evaluate_risk_backtest(rows)

    assert result["total_rows"] == 1
    assert result["evaluated_rows"] == 1
    assert result["failed_rows"] == 0
    assert result["risk_level_counts"]["high"] == 1


def test_no_db_api_network_or_control_behavior() -> None:
    source = inspect.getsource(row_pairing)

    forbidden_terms = (
        "DATABASE_URL",
        "FastAPI",
        "psycopg",
        "requests",
        "httpx",
        "connect(",
        "execute(",
        "calculate_surplus_risk",
        "evaluate_risk_backtest",
        "dispatch",
        "activation",
        "control",
    )

    for forbidden_term in forbidden_terms:
        assert forbidden_term not in source
