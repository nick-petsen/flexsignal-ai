from __future__ import annotations

import ast
import importlib
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

ENERGY_FRESHNESS_API_PATH = Path("app/api/energy_freshness.py")
FORBIDDEN_SQL_OPERATIONS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "UPSERT",
    "CREATE",
    "ALTER",
    "DROP",
)
SENSITIVE_MARKERS = (
    "DATA" + "BASE_URL",
    "secret",
    "token",
)


def test_endpoint_exists() -> None:
    assert any(
        getattr(route, "path", None) == "/api/energy/freshness"
        for route in app.routes
    )


@pytest.mark.parametrize("price_area", ["DK1", "DK2"])
def test_supported_price_area_returns_dry_run_preview(price_area: str) -> None:
    response = client.get(f"/api/energy/freshness?price_area={price_area}")

    assert response.status_code == 200
    body = response.json()
    assert body["price_area"] == price_area
    assert body["dry_run"] is True
    assert body["database_query_executed"] is False
    assert body["database_write_performed"] is False
    assert body["requires_database_url"] is False
    assert body["freshness_plans"]["price_area"] == price_area
    assert body["spot_price_freshness_plan"]["part"] == "spot_price"
    assert body["power_balance_freshness_plan"]["part"] == "power_balance"
    assert body["freshness_plans"]["queries"]["spot_price"][
        "sql"
    ] == body["spot_price_freshness_plan"]["sql"]
    assert body["freshness_plans"]["queries"]["power_balance"][
        "sql"
    ] == body["power_balance_freshness_plan"]["sql"]


def test_invalid_price_area_returns_400() -> None:
    response = client.get("/api/energy/freshness?price_area=SE3")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported price_area"


def test_plans_are_select_only() -> None:
    response = client.get("/api/energy/freshness?price_area=DK1")

    assert response.status_code == 200
    body = response.json()
    plans = [
        body["spot_price_freshness_plan"],
        body["power_balance_freshness_plan"],
        *body["freshness_plans"]["queries"].values(),
    ]

    for plan in plans:
        assert plan["operation"] == "select"
        assert re.match(r"^SELECT\b", plan["sql"])
        for operation in FORBIDDEN_SQL_OPERATIONS:
            assert not re.search(
                rf"\b{operation}\b",
                plan["sql"],
                flags=re.IGNORECASE,
            )


def test_response_contains_no_database_url_or_secret_markers() -> None:
    response = client.get("/api/energy/freshness?price_area=DK2")

    assert response.status_code == 200
    rendered = repr(response.json())
    for marker in SENSITIVE_MARKERS:
        assert marker not in rendered


def test_safety_boundary_is_explicit() -> None:
    response = client.get("/api/energy/freshness?price_area=DK1")

    assert response.status_code == 200
    boundary = response.json()["safety_boundary"]
    assert boundary == {
        "read_only_decision_support": True,
        "no_automatic_control": True,
        "no_dispatch": True,
        "no_activation": True,
        "no_operational_energy_system_integration": True,
        "human_review_required": True,
    }


def test_app_import_without_database_url_still_exposes_endpoint(
    monkeypatch: Any,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)

    assert any(
        getattr(route, "path", None) == "/api/energy/freshness"
        for route in reloaded_main.app.routes
    )


def test_endpoint_does_not_require_database_url(monkeypatch: Any) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.get("/api/energy/freshness?price_area=DK1")

    assert response.status_code == 200
    assert response.json()["requires_database_url"] is False


def test_no_mutating_database_behavior_is_added() -> None:
    source = ENERGY_FRESHNESS_API_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_names = {
        alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    call_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    route_methods = {
        method
        for route in app.routes
        if getattr(route, "path", None) == "/api/energy/freshness"
        for method in getattr(route, "methods", set())
    }

    assert imported_modules == {
        "__future__",
        "typing",
        "fastapi",
        "app.db.repositories.energy_freshness",
    }
    assert "execute_read_query" not in imported_names
    assert "execute" not in call_attributes
    assert "connect" not in source
    assert "commit" not in source
    assert "rollback" not in source
    assert route_methods == {"GET"}


def test_route_safety_still_allows_no_put_patch_delete_or_extra_posts() -> None:
    mutating_methods = {"PUT", "PATCH", "DELETE"}
    allowed_preview_posts = {
        "/api/risk/preview",
        "/api/forecast/preview",
        "/api/audit/preview",
        "/api/report/summary/preview",
    }

    exposed_mutating_routes = [
        (route.path, sorted(route.methods & mutating_methods))
        for route in app.routes
        if hasattr(route, "methods") and route.methods & mutating_methods
    ]
    unexpected_post_routes = [
        route.path
        for route in app.routes
        if (
            hasattr(route, "methods")
            and "POST" in route.methods
            and route.path not in allowed_preview_posts
        )
    ]

    assert exposed_mutating_routes == []
    assert unexpected_post_routes == []


def test_endpoint_does_not_call_database_or_external_services(
    monkeypatch: Any,
) -> None:
    calls: dict[str, int] = {"db": 0, "http": 0}

    def fake_database_call(query: Mapping[str, Any]) -> list[dict[str, Any]]:
        calls["db"] += 1
        raise AssertionError("Database calls are not allowed")

    def fake_urlopen(*args: Any, **kwargs: Any) -> None:
        calls["http"] += 1
        raise AssertionError("Live HTTP calls are not allowed")

    monkeypatch.setattr("app.api.energy.execute_read_query", fake_database_call)
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    response = client.get("/api/energy/freshness?price_area=DK1")

    assert response.status_code == 200
    assert calls == {"db": 0, "http": 0}
