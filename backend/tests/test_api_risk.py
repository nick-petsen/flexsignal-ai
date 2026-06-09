from __future__ import annotations

import importlib
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import risk
from app.main import app


client = TestClient(app)


HIGH_RISK_PAYLOAD = {
    "price_area": "DK1",
    "timestamp_utc": "2026-01-01T00:00:00Z",
    "price_dkk_per_mwh": -25,
    "production_mw": 100,
    "consumption_mw": 80,
    "wind_onshore_mw": 50,
    "wind_offshore_mw": 30,
    "solar_mw": 5,
    "exchange_net_mw": -10,
}

LOW_RISK_PAYLOAD = {
    "price_area": "DK2",
    "timestamp_utc": "2026-01-01T01:00:00Z",
    "price_dkk_per_mwh": 500,
    "production_mw": 100,
    "consumption_mw": 95,
    "wind_onshore_mw": 10,
    "wind_offshore_mw": 5,
    "solar_mw": 5,
    "exchange_net_mw": 20,
}

EXPECTED_RESPONSE_KEYS = {
    "price_area",
    "timestamp_utc",
    "risk_level",
    "risk_score",
    "confidence_score",
    "reason_codes",
    "explanation",
    "recommended_human_action",
    "model_version",
    "decision_support_only",
}
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


def _spot_price_row(price_area: str) -> dict[str, Any]:
    return {
        "id": 1,
        "price_area": price_area,
        "timestamp_utc": datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        "price_eur_per_mwh": Decimal("-3.35"),
        "price_dkk_per_mwh": Decimal("-25"),
        "source": "energi_data_service:DayAheadPrices",
        "source_record_id": f"spot-{price_area}",
        "ingested_at_utc": datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc),
    }


def _power_balance_row(price_area: str) -> dict[str, Any]:
    return {
        "id": 2,
        "price_area": price_area,
        "timestamp_utc": datetime(2026, 1, 1, 0, 5, tzinfo=timezone.utc),
        "production_mw": Decimal("100"),
        "consumption_mw": Decimal("80"),
        "wind_onshore_mw": Decimal("50"),
        "wind_offshore_mw": Decimal("30"),
        "solar_mw": Decimal("5"),
        "exchange_net_mw": Decimal("-10"),
        "source": "energi_data_service:ElectricityProdex5MinRealtime",
        "source_record_id": f"balance-{price_area}",
        "ingested_at_utc": datetime(2026, 1, 1, 0, 6, tzinfo=timezone.utc),
    }


def _fake_current_risk_read(
    captured_queries: list[Mapping[str, Any]],
) -> Any:
    def fake_execute_read_query(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        captured_queries.append(query)
        price_area = query["params"]["price_area"]
        if query["table"] == "spot_prices":
            return [_spot_price_row(price_area)]
        if query["table"] == "power_balance":
            return [_power_balance_row(price_area)]
        raise AssertionError(f"Unexpected table: {query['table']}")

    return fake_execute_read_query


def test_valid_high_risk_payload_returns_high_risk() -> None:
    response = client.post("/api/risk/preview", json=HIGH_RISK_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == EXPECTED_RESPONSE_KEYS
    assert body["price_area"] == "DK1"
    assert body["risk_level"] == "high"
    assert body["risk_score"] == 75
    assert "NEGATIVE_PRICE" in body["reason_codes"]
    assert "HIGH_RENEWABLE_SHARE" in body["reason_codes"]


def test_valid_low_risk_payload_returns_low_risk() -> None:
    response = client.post("/api/risk/preview", json=LOW_RISK_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == EXPECTED_RESPONSE_KEYS
    assert body["price_area"] == "DK2"
    assert body["risk_level"] == "low"
    assert body["risk_score"] == 0
    assert "NORMAL_PRICE" in body["reason_codes"]
    assert "LOW_RENEWABLE_SHARE" in body["reason_codes"]


def test_decision_support_only_is_true() -> None:
    response = client.post("/api/risk/preview", json=LOW_RISK_PAYLOAD)

    assert response.status_code == 200
    assert response.json()["decision_support_only"] is True


def test_valid_current_risk_endpoint_returns_decision_support_only(
    monkeypatch: Any,
) -> None:
    captured_queries: list[Mapping[str, Any]] = []
    monkeypatch.setattr(
        risk,
        "execute_read_query",
        _fake_current_risk_read(captured_queries),
    )

    response = client.get("/api/risk/current?price_area=DK1")

    assert response.status_code == 200
    body = response.json()
    assert body["price_area"] == "DK1"
    assert body["risk_level"] == "high"
    assert body["risk_score"] == 75
    assert body["decision_support_only"] is True
    assert body["metadata"] == {
        "source_tables_used": ["spot_prices", "power_balance"],
        "spot_price_row_found": True,
        "power_balance_row_found": True,
    }
    assert [query["table"] for query in captured_queries] == [
        "spot_prices",
        "power_balance",
    ]
    assert all(
        query["params"] == {"price_area": "DK1", "limit": 1}
        for query in captured_queries
    )


@pytest.mark.parametrize("price_area", ["DK1", "DK2"])
def test_current_risk_endpoint_accepts_supported_price_areas(
    monkeypatch: Any,
    price_area: str,
) -> None:
    captured_queries: list[Mapping[str, Any]] = []
    monkeypatch.setattr(
        risk,
        "execute_read_query",
        _fake_current_risk_read(captured_queries),
    )

    response = client.get(f"/api/risk/current?price_area={price_area}")

    assert response.status_code == 200
    assert response.json()["price_area"] == price_area
    assert all(
        query["params"]["price_area"] == price_area
        for query in captured_queries
    )


def test_current_risk_endpoint_rejects_unsupported_price_area(monkeypatch: Any) -> None:
    execute_calls = 0

    def fake_execute_read_query(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        nonlocal execute_calls
        execute_calls += 1
        return []

    monkeypatch.setattr(risk, "execute_read_query", fake_execute_read_query)

    response = client.get("/api/risk/current?price_area=SE3")

    assert response.status_code == 422
    assert execute_calls == 0


def test_invalid_price_area_rejected() -> None:
    response = client.post(
        "/api/risk/preview",
        json={**LOW_RISK_PAYLOAD, "price_area": "SE3"},
    )

    assert response.status_code == 422


def test_negative_production_rejected() -> None:
    response = client.post(
        "/api/risk/preview",
        json={**LOW_RISK_PAYLOAD, "production_mw": -1},
    )

    assert response.status_code == 422


def test_endpoint_does_not_require_database_url(monkeypatch: Any) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)
    response = TestClient(reloaded_main.app).post(
        "/api/risk/preview",
        json=LOW_RISK_PAYLOAD,
    )

    assert response.status_code == 200
    assert response.json()["risk_level"] == "low"


def test_app_import_without_database_url_still_exposes_current_risk_route(
    monkeypatch: Any,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)

    assert any(
        getattr(route, "path", None) == "/api/risk/current"
        for route in reloaded_main.app.routes
    )


def test_current_risk_endpoint_missing_database_url_returns_controlled_error(
    monkeypatch: Any,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.get("/api/risk/current?price_area=DK1")

    assert response.status_code == 503
    assert response.json()["detail"] == "DATABASE_URL is required for this endpoint"


def test_current_risk_endpoint_no_rows_returns_not_found(monkeypatch: Any) -> None:
    captured_queries: list[Mapping[str, Any]] = []

    def fake_execute_read_query(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        captured_queries.append(query)
        return []

    monkeypatch.setattr(risk, "execute_read_query", fake_execute_read_query)

    response = client.get("/api/risk/current?price_area=DK2")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "No spot_prices or power_balance rows found for requested price_area"
    )
    assert [query["table"] for query in captured_queries] == [
        "spot_prices",
        "power_balance",
    ]


def test_current_risk_endpoint_generates_select_only_sql(monkeypatch: Any) -> None:
    captured_queries: list[Mapping[str, Any]] = []
    monkeypatch.setattr(
        risk,
        "execute_read_query",
        _fake_current_risk_read(captured_queries),
    )

    response = client.get("/api/risk/current?price_area=DK1")

    assert response.status_code == 200
    assert len(captured_queries) == 2
    for query in captured_queries:
        assert query["operation"] == "select"
        assert re.match(r"^SELECT\b", query["sql"])
        for operation in FORBIDDEN_SQL_OPERATIONS:
            assert not re.search(
                rf"\b{operation}\b",
                query["sql"],
                flags=re.IGNORECASE,
            )


def test_no_database_or_live_http_calls_are_made(monkeypatch: Any) -> None:
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

    response = client.post("/api/risk/preview", json=HIGH_RISK_PAYLOAD)

    assert response.status_code == 200
    assert database_calls == 0
    assert http_calls == 0


def test_current_risk_endpoint_does_not_call_live_http(monkeypatch: Any) -> None:
    captured_queries: list[Mapping[str, Any]] = []
    http_calls = 0

    def fail_live_http_call(*args: Any, **kwargs: Any) -> None:
        nonlocal http_calls
        http_calls += 1
        raise AssertionError("Live HTTP calls are not allowed")

    monkeypatch.setattr(
        risk,
        "execute_read_query",
        _fake_current_risk_read(captured_queries),
    )
    monkeypatch.setattr("urllib.request.urlopen", fail_live_http_call)

    response = client.get("/api/risk/current?price_area=DK1")

    assert response.status_code == 200
    assert len(captured_queries) == 2
    assert http_calls == 0


def test_endpoint_calls_rule_engine_with_caller_payload_only(monkeypatch: Any) -> None:
    captured_payloads: list[dict[str, object]] = []
    payload_with_null = {**LOW_RISK_PAYLOAD, "exchange_net_mw": None}

    def fake_calculate_surplus_risk(input_data: dict[str, object]) -> dict[str, object]:
        captured_payloads.append(input_data)
        return {
            "price_area": input_data["price_area"],
            "timestamp_utc": input_data["timestamp_utc"],
            "risk_level": "low",
            "risk_score": 0,
            "confidence_score": 1.0,
            "reason_codes": ["TEST_ONLY"],
            "explanation": "Test-only deterministic preview.",
            "recommended_human_action": "Human review only.",
            "model_version": "rule-engine-v0",
            "decision_support_only": True,
        }

    monkeypatch.setattr(risk, "calculate_surplus_risk", fake_calculate_surplus_risk)

    response = client.post(
        "/api/risk/preview",
        json=payload_with_null,
    )

    assert response.status_code == 200
    assert captured_payloads == [
        {key: value for key, value in payload_with_null.items() if value is not None}
    ]


def test_no_control_dispatch_or_activation_fields_exist() -> None:
    response = client.post("/api/risk/preview", json=LOW_RISK_PAYLOAD)

    assert response.status_code == 200
    forbidden_terms = ("control", "dispatch", "activation")
    assert all(
        term not in key.lower()
        for key in response.json()
        for term in forbidden_terms
    )

    rejected_response = client.post(
        "/api/risk/preview",
        json={**LOW_RISK_PAYLOAD, "dispatch_mw": 1},
    )
    assert rejected_response.status_code == 422


def test_current_risk_has_no_control_dispatch_or_activation_fields(
    monkeypatch: Any,
) -> None:
    captured_queries: list[Mapping[str, Any]] = []
    monkeypatch.setattr(
        risk,
        "execute_read_query",
        _fake_current_risk_read(captured_queries),
    )

    response = client.get("/api/risk/current?price_area=DK1")

    assert response.status_code == 200
    forbidden_terms = ("control", "dispatch", "activation")
    body = response.json()
    top_level_keys = set(body)
    metadata_keys = set(body["metadata"])
    assert all(
        term not in key.lower()
        for key in top_level_keys | metadata_keys
        for term in forbidden_terms
    )
