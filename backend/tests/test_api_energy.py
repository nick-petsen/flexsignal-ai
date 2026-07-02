from __future__ import annotations

import importlib
import re
from collections.abc import Mapping
from typing import Any

from fastapi.testclient import TestClient

from app.api import energy
from app.main import app


client = TestClient(app)

FORBIDDEN_SQL_OPERATIONS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "UPSERT",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
)


def test_spot_prices_endpoint_returns_expected_shape(monkeypatch: Any) -> None:
    captured_queries: list[Mapping[str, Any]] = []

    def fake_execute_read_query(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        captured_queries.append(query)
        return [
            {
                "id": 1,
                "price_area": "DK1",
                "timestamp_utc": "2026-01-01T00:00:00Z",
                "price_eur_per_mwh": "45.10",
                "price_dkk_per_mwh": "336.60",
                "source": "energi_data_service:DayAheadPrices",
                "source_record_id": "sample-1",
                "ingested_at_utc": "2026-01-01T00:05:00Z",
            }
        ]

    monkeypatch.setattr(energy, "execute_read_query", fake_execute_read_query)

    response = client.get("/api/energy/spot-prices?price_area=DK1")

    assert response.status_code == 200
    assert response.json() == {
        "table": "spot_prices",
        "price_area": "DK1",
        "row_count": 1,
        "rows": [
            {
                "id": 1,
                "price_area": "DK1",
                "timestamp_utc": "2026-01-01T00:00:00Z",
                "price_eur_per_mwh": "45.10",
                "price_dkk_per_mwh": "336.60",
                "source": "energi_data_service:DayAheadPrices",
                "source_record_id": "sample-1",
                "ingested_at_utc": "2026-01-01T00:05:00Z",
            }
        ],
    }
    assert captured_queries[0]["table"] == "spot_prices"
    assert captured_queries[0]["params"] == {"price_area": "DK1", "limit": 100}


def test_power_balance_endpoint_returns_expected_shape(monkeypatch: Any) -> None:
    captured_queries: list[Mapping[str, Any]] = []

    def fake_execute_read_query(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        captured_queries.append(query)
        return [
            {
                "id": 2,
                "price_area": "DK2",
                "timestamp_utc": "2026-01-01T00:00:00Z",
                "production_mw": "1200.0",
                "consumption_mw": "1100.0",
                "wind_onshore_mw": "400.0",
                "wind_offshore_mw": "300.0",
                "solar_mw": "50.0",
                "exchange_net_mw": "-20.0",
                "source": "energi_data_service:ElectricityProdex5MinRealtime",
                "source_record_id": "sample-2",
                "ingested_at_utc": "2026-01-01T00:05:00Z",
            }
        ]

    monkeypatch.setattr(energy, "execute_read_query", fake_execute_read_query)

    response = client.get("/api/energy/power-balance?price_area=DK2&limit=25")

    assert response.status_code == 200
    assert response.json()["table"] == "power_balance"
    assert response.json()["price_area"] == "DK2"
    assert response.json()["row_count"] == 1
    assert response.json()["rows"][0]["source_record_id"] == "sample-2"
    assert captured_queries[0]["table"] == "power_balance"
    assert captured_queries[0]["params"] == {"price_area": "DK2", "limit": 25}


def test_invalid_price_area_is_rejected(monkeypatch: Any) -> None:
    execute_calls = 0

    def fake_execute_read_query(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        nonlocal execute_calls
        execute_calls += 1
        return []

    monkeypatch.setattr(energy, "execute_read_query", fake_execute_read_query)

    response = client.get("/api/energy/spot-prices?price_area=SE3")

    assert response.status_code == 422
    assert execute_calls == 0


def test_invalid_limit_is_rejected(monkeypatch: Any) -> None:
    execute_calls = 0

    def fake_execute_read_query(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        nonlocal execute_calls
        execute_calls += 1
        return []

    monkeypatch.setattr(energy, "execute_read_query", fake_execute_read_query)

    response = client.get("/api/energy/power-balance?price_area=DK1&limit=1001")

    assert response.status_code == 422
    assert execute_calls == 0


def test_endpoint_submits_select_only_query(monkeypatch: Any) -> None:
    captured_queries: list[Mapping[str, Any]] = []

    def fake_execute_read_query(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        captured_queries.append(query)
        return []

    monkeypatch.setattr(energy, "execute_read_query", fake_execute_read_query)

    response = client.get("/api/energy/spot-prices?price_area=DK1&limit=10")

    assert response.status_code == 200
    assert len(captured_queries) == 1
    assert captured_queries[0]["operation"] == "select"
    assert re.match(r"^SELECT\b", captured_queries[0]["sql"])
    for operation in FORBIDDEN_SQL_OPERATIONS:
        assert not re.search(
            rf"\b{operation}\b",
            captured_queries[0]["sql"],
            flags=re.IGNORECASE,
        )


def test_app_exposes_no_mutating_write_methods() -> None:
    mutating_methods = {"PUT", "PATCH", "DELETE"}
    allowed_safe_post_routes = {
        "/api/risk/preview",
        "/api/forecast/preview",
        "/api/audit/preview",
        "/api/audit/pdf-export/persist",
        "/api/report/summary/preview",
        "/api/report/markdown/preview",
        "/api/report/pdf/preview",
        "/api/report/pdf/export",
        "/api/report/pdf/export/audited",
        "/api/dashboard/decision-summary/preview",
    }

    exposed_mutating_routes = [
        (route.path, sorted(route.methods & mutating_methods))
        for route in app.routes
        if hasattr(route, "methods") and route.methods & mutating_methods
    ]
    preview_routes = [
        route
        for route in app.routes
        if getattr(route, "path", None) in allowed_safe_post_routes
    ]
    unexpected_post_routes = [
        route.path
        for route in app.routes
        if (
            hasattr(route, "methods")
            and "POST" in route.methods
            and route.path not in allowed_safe_post_routes
        )
    ]

    assert exposed_mutating_routes == []
    assert unexpected_post_routes == []
    assert {route.path for route in preview_routes} == allowed_safe_post_routes


def test_read_helper_rejects_write_queries() -> None:
    response_error = None
    try:
        energy.execute_read_query(
            {
                "sql": "UPDATE spot_prices SET source = %(source)s",
                "params": {"source": "test"},
                "table": "spot_prices",
                "operation": "update",
            }
        )
    except Exception as exc:  # FastAPI raises HTTPException before DB access.
        response_error = exc

    assert response_error is not None
    assert getattr(response_error, "status_code") == 500


def test_endpoint_does_not_call_live_http(monkeypatch: Any) -> None:
    execute_calls = 0
    http_calls = 0

    def fake_execute_read_query(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        nonlocal execute_calls
        execute_calls += 1
        return []

    def fake_urlopen(*args: Any, **kwargs: Any) -> None:
        nonlocal http_calls
        http_calls += 1
        raise AssertionError("Live HTTP calls are not allowed")

    monkeypatch.setattr(energy, "execute_read_query", fake_execute_read_query)
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    response = client.get("/api/energy/power-balance?price_area=DK2")

    assert response.status_code == 200
    assert execute_calls == 1
    assert http_calls == 0


def test_app_import_does_not_require_database_url(monkeypatch: Any) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)

    assert reloaded_main.app.title == "FlexSignal AI API"
