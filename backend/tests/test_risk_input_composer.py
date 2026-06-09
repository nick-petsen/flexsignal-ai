from __future__ import annotations

import importlib
import socket
import urllib.request
from typing import Any

import pytest

from app.risk import calculate_surplus_risk, compose_surplus_risk_input


SPOT_ROW = {
    "id": 1,
    "price_area": "DK1",
    "timestamp_utc": "2026-01-01T00:00:00Z",
    "price_eur_per_mwh": -3.35,
    "price_dkk_per_mwh": -25,
    "source": "Energi Data Service:DayAheadPrices",
}

POWER_ROW = {
    "id": 2,
    "price_area": "DK1",
    "timestamp_utc": "2026-01-01T00:05:00Z",
    "production_mw": 100,
    "consumption_mw": 80,
    "wind_onshore_mw": 50,
    "wind_offshore_mw": 30,
    "solar_mw": 5,
    "exchange_net_mw": -10,
    "source": "Energi Data Service:ElectricityProdex5MinRealtime",
}


def test_both_rows_present_maps_rule_engine_input() -> None:
    result = compose_surplus_risk_input(
        price_area="DK1",
        spot_price_row=SPOT_ROW,
        power_balance_row=POWER_ROW,
    )

    assert result == {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:05:00Z",
        "price_dkk_per_mwh": -25,
        "production_mw": 100,
        "consumption_mw": 80,
        "wind_onshore_mw": 50,
        "wind_offshore_mw": 30,
        "solar_mw": 5,
        "exchange_net_mw": -10,
    }


def test_only_spot_row_present_maps_price_context() -> None:
    result = compose_surplus_risk_input(
        price_area="DK1",
        spot_price_row=SPOT_ROW,
        power_balance_row=None,
    )

    assert result == {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00Z",
        "price_dkk_per_mwh": -25,
    }


def test_only_power_row_present_maps_balance_context() -> None:
    result = compose_surplus_risk_input(
        price_area="DK1",
        spot_price_row=None,
        power_balance_row=POWER_ROW,
    )

    assert result == {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:05:00Z",
        "production_mw": 100,
        "consumption_mw": 80,
        "wind_onshore_mw": 50,
        "wind_offshore_mw": 30,
        "solar_mw": 5,
        "exchange_net_mw": -10,
    }


def test_mismatched_row_price_area_is_rejected() -> None:
    with pytest.raises(ValueError, match="must match requested price_area"):
        compose_surplus_risk_input(
            price_area="DK1",
            spot_price_row={**SPOT_ROW, "price_area": "DK2"},
            power_balance_row=POWER_ROW,
        )


def test_invalid_requested_price_area_is_rejected() -> None:
    with pytest.raises(ValueError, match="price_area must be DK1 or DK2"):
        compose_surplus_risk_input(
            price_area="SE3",
            spot_price_row=SPOT_ROW,
            power_balance_row=POWER_ROW,
        )


def test_at_least_one_row_is_required() -> None:
    with pytest.raises(ValueError, match="At least one energy row"):
        compose_surplus_risk_input(
            price_area="DK1",
            spot_price_row=None,
            power_balance_row=None,
        )


def test_missing_all_timestamps_is_rejected() -> None:
    spot_without_timestamp = {
        key: value for key, value in SPOT_ROW.items() if key != "timestamp_utc"
    }
    power_without_timestamp = {
        key: value for key, value in POWER_ROW.items() if key != "timestamp_utc"
    }

    with pytest.raises(ValueError, match="timestamp_utc"):
        compose_surplus_risk_input(
            price_area="DK1",
            spot_price_row=spot_without_timestamp,
            power_balance_row=power_without_timestamp,
        )


def test_output_can_be_passed_to_calculate_surplus_risk() -> None:
    composed = compose_surplus_risk_input(
        price_area="DK1",
        spot_price_row=SPOT_ROW,
        power_balance_row=POWER_ROW,
    )

    result = calculate_surplus_risk(composed)

    assert result["risk_level"] == "high"
    assert result["risk_score"] == 75
    assert result["model_version"] == "rule-engine-v0"
    assert result["decision_support_only"] is True


def test_no_db_api_network_or_control_behavior(monkeypatch: Any) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    imported_modules: list[str] = []

    original_import_module = importlib.import_module

    def track_import(name: str, package: str | None = None) -> Any:
        imported_modules.append(name)
        return original_import_module(name, package)

    def fail_socket_connect(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Network calls are not allowed")

    def fail_urlopen(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Live API calls are not allowed")

    monkeypatch.setattr(importlib, "import_module", track_import)
    monkeypatch.setattr(socket.socket, "connect", fail_socket_connect)
    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    result = compose_surplus_risk_input(
        price_area="DK1",
        spot_price_row=SPOT_ROW,
        power_balance_row=POWER_ROW,
    )

    assert result["price_area"] == "DK1"
    assert imported_modules == []
    assert "dispatch_mw" not in result
    assert "activation_signal" not in result
    assert "control_signal" not in result
