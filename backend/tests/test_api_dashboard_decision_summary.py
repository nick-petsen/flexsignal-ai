from __future__ import annotations

import importlib
import subprocess
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import dashboard
from app.main import app


client = TestClient(app)


def _spot_price_row(price_area: str) -> dict[str, Any]:
    return {
        "id": 1,
        "price_area": price_area,
        "timestamp_utc": datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
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


def _forecast_row(hours: int, *, price_area: str = "DK1") -> dict[str, Any]:
    return {
        "price_area": price_area,
        "timestamp_utc": (
            datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc) + timedelta(hours=hours)
        ).isoformat(),
        "price_dkk_per_mwh": -25,
        "production_mw": 100,
        "consumption_mw": 80,
        "wind_onshore_mw": 50,
        "wind_offshore_mw": 30,
        "solar_mw": 5,
        "exchange_net_mw": -10,
    }


def test_endpoint_exists() -> None:
    assert any(
        getattr(route, "path", None)
        == "/api/dashboard/decision-summary/preview"
        for route in app.routes
    )


def test_dk1_preview_returns_decision_support_safety_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.post(
        "/api/dashboard/decision-summary/preview",
        json={"price_area": "DK1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["price_area"] == "DK1"
    assert body["decision_support_only"] is True
    assert body["human_review_required"] is True
    assert body["no_automatic_control"] is True
    assert body["no_dispatch"] is True
    assert body["no_activation"] is True
    assert body["recommended_human_action"] == "Human review required"


def test_missing_values_are_explicit_not_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.post(
        "/api/dashboard/decision-summary/preview",
        json={"price_area": "DK1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["current_risk"]["status"] == "not_available"
    assert body["next_surplus_window"]["status"] == "not_calculated"
    assert body["confidence"]["status"] == "not_available"
    assert body["expected_impact"]["status"] == "not_calculated"
    assert body["economic_potential"]["status"] == "not_calculated"
    assert body["data_freshness"]["status"] == "not_available"
    assert "current_risk is not_available" in body["warnings"]
    assert "next_surplus_window is not_calculated" in body["warnings"]
    assert "economic_potential is not_calculated" in body["warnings"]


def test_empty_forecast_rows_keep_next_surplus_window_not_calculated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.post(
        "/api/dashboard/decision-summary/preview",
        json={"price_area": "DK1", "forecast_rows": []},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["next_surplus_window"]["status"] == "not_calculated"
    assert "forecast_rows" in body["next_surplus_window"]["reason"]
    assert (
        body["source_notes"]["next_surplus_window"]
        == "Not calculated because this preview did not receive forecast_rows."
    )
    assert "next_surplus_window is not_calculated" in body["warnings"]


def test_forecast_rows_calculate_next_surplus_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.post(
        "/api/dashboard/decision-summary/preview",
        json={
            "price_area": "DK1",
            "forecast_rows": [_forecast_row(0), _forecast_row(25)],
        },
    )

    assert response.status_code == 200
    body = response.json()
    next_window = body["next_surplus_window"]
    assert next_window["status"] == "available"
    assert next_window["value"] == "0-24h"
    assert next_window["window_label"] == "0-24h"
    assert next_window["risk_level"] == "high"
    assert next_window["risk_score"] == 75
    assert next_window["row_count"] == 1
    assert next_window["source"] == "caller_provided_forecast_rows"
    assert next_window["model_version"] == "rule-engine-v0+forecast-window-v0"
    assert next_window["decision_support_only"] is True
    assert "caller-provided forecast row" in next_window["summary"]
    assert "next_surplus_window is not_calculated" not in body["warnings"]
    assert "caller-provided forecast_rows" in body["source_notes"]["next_surplus_window"]
    assert "no forecast rows were invented" in body["source_notes"]["next_surplus_window"]


def test_forecast_rows_without_database_url_still_return_safe_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.post(
        "/api/dashboard/decision-summary/preview",
        json={"price_area": "DK1", "forecast_rows": [_forecast_row(0)]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data_freshness"]["status"] == "not_available"
    assert body["next_surplus_window"]["status"] == "available"
    assert body["decision_support_only"] is True
    assert body["human_review_required"] is True
    assert body["no_automatic_control"] is True
    assert body["no_dispatch"] is True
    assert body["no_activation"] is True


def test_economic_potential_remains_not_calculated_without_real_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.post(
        "/api/dashboard/decision-summary/preview",
        json={"price_area": "DK1"},
    )

    assert response.status_code == 200
    economic_potential = response.json()["economic_potential"]
    assert economic_potential == {
        "status": "not_calculated",
        "reason": (
            "No existing real backend economic-potential calculation is available "
            "for this preview."
        ),
    }


def test_current_risk_and_confidence_use_existing_read_model_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    captured_queries: list[Mapping[str, Any]] = []

    def fake_execute_read_query(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        captured_queries.append(query)
        price_area = query["params"]["price_area"]
        if query["table"] == "spot_prices":
            return [_spot_price_row(price_area)]
        if query["table"] == "power_balance":
            return [_power_balance_row(price_area)]
        raise AssertionError(f"Unexpected table: {query['table']}")

    monkeypatch.setattr(dashboard, "execute_read_query", fake_execute_read_query)

    response = client.post(
        "/api/dashboard/decision-summary/preview",
        json={"price_area": "DK1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["current_risk"]["risk_level"] == "high"
    assert body["current_risk"]["risk_score"] == 75
    assert body["current_risk"]["confidence_score"] == 1.0
    assert body["confidence"] == {
        "value": 1.0,
        "source": "current_risk.confidence_score",
    }
    assert body["recommended_human_action"] == (
        "Human review required before planning; verify source data and keep "
        "any action outside this read-only model."
    )
    assert [query["operation"] for query in captured_queries] == ["select", "select"]


def test_app_imports_without_database_url_and_exposes_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)

    assert any(
        getattr(route, "path", None)
        == "/api/dashboard/decision-summary/preview"
        for route in reloaded_main.app.routes
    )


def test_no_database_write_or_mutating_sql_path_in_dashboard_module() -> None:
    module_source = Path(dashboard.__file__).read_text(encoding="utf-8")

    forbidden_terms = (
        "INSERT",
        "UPDATE",
        "DELETE",
        "UPSERT",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "write_plan",
        "persist",
        "audit",
        "commit(",
    )
    for term in forbidden_terms:
        assert term not in module_source


def test_no_external_api_calls_are_made(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    http_calls = 0

    def fail_live_http_call(*args: Any, **kwargs: Any) -> None:
        nonlocal http_calls
        http_calls += 1
        raise AssertionError("Live HTTP calls are not allowed")

    monkeypatch.setattr("urllib.request.urlopen", fail_live_http_call)

    response = client.post(
        "/api/dashboard/decision-summary/preview",
        json={"price_area": "DK1"},
    )

    assert response.status_code == 200
    assert http_calls == 0


def test_no_frontend_files_changed_for_backend_endpoint() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    diff = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...", "--", "frontend"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        pytest.skip("origin/main is not available for frontend diff check")

    assert diff.stdout.strip() == ""
