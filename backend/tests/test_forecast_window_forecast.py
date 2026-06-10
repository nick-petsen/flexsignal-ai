from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.forecast import build_forecast_window_forecast


GENERATED_AT = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
SAFETY_WORDING = "must not be used for automatic control, dispatch, or activation"


def _row(
    hours: int,
    *,
    price_area: str = "DK1",
    price: float = 500,
    production: float = 100,
    wind_onshore: float = 10,
    wind_offshore: float = 5,
    solar: float = 5,
) -> dict[str, object]:
    return {
        "price_area": price_area,
        "timestamp_utc": GENERATED_AT + timedelta(hours=hours),
        "price_dkk_per_mwh": price,
        "production_mw": production,
        "consumption_mw": 90,
        "wind_onshore_mw": wind_onshore,
        "wind_offshore_mw": wind_offshore,
        "solar_mw": solar,
    }


def _high_risk_row(hours: int) -> dict[str, object]:
    return _row(
        hours,
        price=-25,
        production=100,
        wind_onshore=50,
        wind_offshore=30,
        solar=5,
    )


def test_three_windows_always_returned() -> None:
    forecast = build_forecast_window_forecast(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        rows=[],
    )

    assert [window["window_label"] for window in forecast["windows"]] == [
        "0-24h",
        "24-48h",
        "48-72h",
    ]
    assert forecast["decision_support_only"] is True
    assert forecast["model_version"] == "rule-engine-v0+forecast-window-v0"


def test_rows_are_assigned_to_correct_windows() -> None:
    forecast = build_forecast_window_forecast(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        rows=[_row(0), _row(24), _row(48), _row(71)],
    )

    assert [window["row_count"] for window in forecast["windows"]] == [1, 1, 2]


def test_rows_before_generated_at_are_ignored() -> None:
    forecast = build_forecast_window_forecast(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        rows=[_row(-1), _row(1)],
    )

    assert forecast["windows"][0]["row_count"] == 1


def test_rows_at_plus_72_hours_are_ignored() -> None:
    forecast = build_forecast_window_forecast(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        rows=[_row(71), _row(72)],
    )

    assert forecast["windows"][2]["row_count"] == 1


def test_wrong_price_area_rows_are_ignored() -> None:
    forecast = build_forecast_window_forecast(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        rows=[_row(1, price_area="DK2"), _row(2, price_area="DK1")],
    )

    assert forecast["windows"][0]["row_count"] == 1


def test_empty_window_returns_unknown() -> None:
    forecast = build_forecast_window_forecast(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        rows=[_row(1)],
    )
    empty_window = forecast["windows"][1]

    assert empty_window["risk_level"] == "unknown"
    assert empty_window["max_risk_score"] is None
    assert empty_window["average_risk_score"] is None
    assert empty_window["average_confidence_score"] == 0
    assert "not enough caller-provided data" in empty_window["explanation"]


def test_high_risk_in_any_row_makes_window_high_even_if_average_is_lower() -> None:
    forecast = build_forecast_window_forecast(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        rows=[_high_risk_row(1), _row(2), _row(3)],
    )
    window = forecast["windows"][0]

    assert window["risk_level"] == "high"
    assert window["max_risk_score"] == 75
    assert window["average_risk_score"] == 25
    assert "Human review required" in window["recommended_human_action"]


def test_top_reason_codes_have_deterministic_ordering() -> None:
    forecast = build_forecast_window_forecast(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        rows=[
            _high_risk_row(1),
            _row(
                2,
                price=50,
                production=100,
                wind_onshore=30,
                wind_offshore=25,
                solar=5,
            ),
        ],
    )

    top_reason_codes = forecast["windows"][0]["top_reason_codes"]

    assert top_reason_codes == [
        {"reason_code": "HIGH_RENEWABLE_SHARE", "count": 1},
        {"reason_code": "LOW_PRICE", "count": 1},
        {"reason_code": "MODERATE_RENEWABLE_SHARE", "count": 1},
        {"reason_code": "NEGATIVE_PRICE", "count": 1},
    ]


def test_timezone_naive_timestamps_are_rejected_safely() -> None:
    row = _row(1)
    row["timestamp_utc"] = datetime(2026, 1, 1, 1, 0)

    with pytest.raises(ValueError, match="timestamp_utc must be timezone-aware"):
        build_forecast_window_forecast(
            price_area="DK1",
            generated_at_utc=GENERATED_AT,
            rows=[row],
        )


def test_invalid_row_price_area_is_rejected() -> None:
    with pytest.raises(ValueError, match="row price_area must be DK1 or DK2"):
        build_forecast_window_forecast(
            price_area="DK1",
            generated_at_utc=GENERATED_AT,
            rows=[_row(1, price_area="SE3")],
        )


def test_object_rows_and_aware_iso_strings_are_supported() -> None:
    @dataclass(frozen=True)
    class ForecastInputRow:
        price_area: str
        timestamp_utc: str
        price_dkk_per_mwh: float
        production_mw: float
        consumption_mw: float
        wind_onshore_mw: float
        wind_offshore_mw: float
        solar_mw: float

    forecast = build_forecast_window_forecast(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        rows=[
            ForecastInputRow(
                price_area="DK1",
                timestamp_utc="2026-01-01T01:00:00+00:00",
                price_dkk_per_mwh=500,
                production_mw=100,
                consumption_mw=90,
                wind_onshore_mw=10,
                wind_offshore_mw=5,
                solar_mw=5,
            )
        ],
    )

    assert forecast["windows"][0]["row_count"] == 1


def test_no_db_api_network_or_control_behavior_in_forecast_module() -> None:
    module_source = Path("app/forecast/window_forecast.py").read_text()

    forbidden_terms = [
        "FastAPI",
        "APIRouter",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlalchemy",
        "DATABASE_URL",
        "app.db",
        "app.api",
    ]
    for term in forbidden_terms:
        assert term not in module_source


def test_output_includes_decision_support_flags_and_safety_wording() -> None:
    forecast = build_forecast_window_forecast(
        price_area="DK1",
        generated_at_utc=GENERATED_AT,
        rows=[_row(1)],
    )

    assert forecast["decision_support_only"] is True
    assert SAFETY_WORDING in forecast["safety"]

    for window in forecast["windows"]:
        assert window["decision_support_only"] is True
        assert SAFETY_WORDING in window["explanation"]
        assert SAFETY_WORDING in window["recommended_human_action"]
