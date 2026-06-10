from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

SAFETY_WORDING = "must not be used for automatic control, dispatch, or activation"


def _row(hours: int, *, price_area: str = "DK1") -> dict[str, object]:
    return {
        "price_area": price_area,
        "timestamp_utc": (
            datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(hours=hours)
        ).isoformat(),
        "price_dkk_per_mwh": 100,
        "production_mw": 5000,
        "wind_onshore_mw": 2000,
        "wind_offshore_mw": 1000,
        "solar_mw": 100,
        "consumption_mw": 4500,
    }


def _payload(*, rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "price_area": "DK1",
        "generated_at_utc": "2026-01-01T00:00:00+00:00",
        "rows": [_row(1), _row(25), _row(49)] if rows is None else rows,
    }


def test_valid_preview_returns_three_windows() -> None:
    response = client.post("/api/forecast/preview", json=_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["price_area"] == "DK1"
    assert body["model_version"] == "rule-engine-v0+forecast-window-v0"
    assert body["decision_support_only"] is True
    assert [window["window_label"] for window in body["windows"]] == [
        "0-24h",
        "24-48h",
        "48-72h",
    ]
    assert len(body["windows"]) == 3


def test_empty_rows_returns_three_unknown_windows() -> None:
    response = client.post("/api/forecast/preview", json=_payload(rows=[]))

    assert response.status_code == 200
    body = response.json()
    assert len(body["windows"]) == 3
    assert [window["risk_level"] for window in body["windows"]] == [
        "unknown",
        "unknown",
        "unknown",
    ]
    assert [window["row_count"] for window in body["windows"]] == [0, 0, 0]


def test_invalid_price_area_returns_422() -> None:
    response = client.post(
        "/api/forecast/preview",
        json={**_payload(), "price_area": "SE3"},
    )

    assert response.status_code == 422


def test_timezone_naive_generated_at_utc_returns_422() -> None:
    response = client.post(
        "/api/forecast/preview",
        json={**_payload(), "generated_at_utc": "2026-01-01T00:00:00"},
    )

    assert response.status_code == 422
    assert "timezone-aware" in response.text


def test_timezone_naive_row_timestamp_returns_controlled_error() -> None:
    row = {**_row(1), "timestamp_utc": "2026-01-01T01:00:00"}

    response = client.post(
        "/api/forecast/preview",
        json=_payload(rows=[row]),
    )

    assert response.status_code == 422
    assert "timezone-aware" in response.text


def test_forecast_api_module_has_no_fetch_persist_or_job_behavior() -> None:
    module_source = Path("app/api/forecast.py").read_text()

    forbidden_terms = [
        "DATABASE_URL",
        "execute_read_query",
        "psycopg",
        "sqlalchemy",
        "requests",
        "httpx",
        "urllib",
        "app.db",
        "app.integrations",
        "energi_data_service",
        "ingestion",
        "scheduler",
        "jobs",
        "control",
        "dispatch",
        "activation",
    ]
    for term in forbidden_terms:
        assert term not in module_source


def test_preview_makes_no_db_api_network_or_action_calls(monkeypatch: Any) -> None:
    database_calls = 0
    http_calls = 0

    def fail_database_call(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        nonlocal database_calls
        database_calls += 1
        raise AssertionError("Database calls are not allowed")

    def fail_live_http_call(*args: Any, **kwargs: Any) -> None:
        nonlocal http_calls
        http_calls += 1
        raise AssertionError("Live HTTP calls are not allowed")

    monkeypatch.setattr("app.api.energy.execute_read_query", fail_database_call)
    monkeypatch.setattr("urllib.request.urlopen", fail_live_http_call)

    response = client.post("/api/forecast/preview", json=_payload())

    assert response.status_code == 200
    assert database_calls == 0
    assert http_calls == 0


def test_endpoint_does_not_modify_existing_risk_endpoints() -> None:
    response = client.post(
        "/api/risk/preview",
        json={
            "price_area": "DK2",
            "timestamp_utc": "2026-01-01T01:00:00Z",
            "price_dkk_per_mwh": 500,
            "production_mw": 100,
            "consumption_mw": 95,
            "wind_onshore_mw": 10,
            "wind_offshore_mw": 5,
            "solar_mw": 5,
            "exchange_net_mw": 20,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["price_area"] == "DK2"
    assert body["risk_level"] == "low"
    assert body["decision_support_only"] is True


def test_response_includes_decision_support_only_and_safety_wording() -> None:
    response = client.post("/api/forecast/preview", json=_payload(rows=[]))

    assert response.status_code == 200
    body = response.json()
    assert body["decision_support_only"] is True
    assert SAFETY_WORDING in body["safety"]
    for window in body["windows"]:
        assert window["decision_support_only"] is True
        assert SAFETY_WORDING in window["explanation"]
        assert SAFETY_WORDING in window["recommended_human_action"]
