from __future__ import annotations

import ast
import importlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import audit
from app.main import app


client = TestClient(app)

RAW_DATABASE_URL = "postgresql://user:super-secret-token@localhost/flexsignal_ai"
CONFLICT_BEHAVIOR = "ON CONFLICT (event_id) DO NOTHING"
FORBIDDEN_TABLES = (
    "spot_prices",
    "power_balance",
    "forecast",
    "energy_freshness",
)


class FakeCursor:
    def __init__(self) -> None:
        self.rowcount = 1
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    def execute(self, sql: str, params: Mapping[str, Any]) -> None:
        self.calls.append((sql, params))


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()
        self.cursor_calls = 0
        self.closed = False

    def cursor(self) -> FakeCursor:
        self.cursor_calls += 1
        return self.cursor_instance

    def close(self) -> None:
        self.closed = True


def install_fake_connection(monkeypatch: pytest.MonkeyPatch) -> FakeConnection:
    connection = FakeConnection()
    captured_urls: list[str] = []

    def fake_connect(database_url: str) -> FakeConnection:
        captured_urls.append(database_url)
        return connection

    monkeypatch.setenv("DATABASE_URL", RAW_DATABASE_URL)
    monkeypatch.setattr(audit, "connect_with_psycopg", fake_connect)
    connection.captured_urls = captured_urls  # type: ignore[attr-defined]
    return connection


def test_endpoint_exists() -> None:
    assert any(
        getattr(route, "path", None) == "/api/audit/pdf-export/persist"
        for route in app.routes
    )


def test_app_import_without_database_url_still_exposes_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)

    assert any(
        getattr(route, "path", None) == "/api/audit/pdf-export/persist"
        for route in reloaded_main.app.routes
    )


def test_missing_database_url_returns_safe_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect_calls = 0

    def fake_connect(_database_url: str) -> FakeConnection:
        nonlocal connect_calls
        connect_calls += 1
        return FakeConnection()

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(audit, "connect_with_psycopg", fake_connect)

    response = client.post("/api/audit/pdf-export/persist", json={})

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["requires_database_url"] is True
    assert detail["audit_event_created"] is False
    assert detail["audit_event_persisted"] is False
    assert detail["database_query_executed"] is False
    assert detail["database_write_performed"] is False
    assert detail["table"] == "audit_events"
    assert RAW_DATABASE_URL not in repr(detail)
    assert "super-secret-token" not in repr(detail)
    assert connect_calls == 0


def test_invalid_price_area_returns_safe_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = install_fake_connection(monkeypatch)

    response = client.post(
        "/api/audit/pdf-export/persist",
        json={"price_area": "SE3"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported price_area"
    assert connection.cursor_calls == 0
    assert connection.cursor_instance.calls == []


def test_successful_persistence_inserts_one_pdf_export_event_to_audit_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = install_fake_connection(monkeypatch)

    response = client.post(
        "/api/audit/pdf-export/persist",
        json={
            "price_area": "DK1",
            "occurred_at_utc": "2026-01-01T12:30:00Z",
            "request_id": "request-123",
            "source": "unit-test",
        },
    )

    assert response.status_code == 200
    body = response.json()
    event = body["event"]
    metadata = event["metadata"]
    assert body["audit_event_created"] is True
    assert body["audit_event_persisted"] is True
    assert body["database_query_executed"] is False
    assert body["database_write_performed"] is True
    assert body["requires_database_url"] is True
    assert body["event_id"] == event["event_id"]
    assert body["event_type"] == "report_pdf_export_requested"
    assert body["table"] == "audit_events"
    assert body["conflict_behavior"] == CONFLICT_BEHAVIOR
    assert event["event_version"] == "audit-event-v0"
    assert event["action"] == "manual_pdf_export"
    assert event["resource_type"] == "report"
    assert event["resource_id"] == "report-summary-v0-DK1-872ff94f403e4ddd"
    assert event["decision_support_only"] is True
    assert event["safety_boundary"]["human_review_required"] is True
    assert metadata["price_area"] == "DK1"
    assert metadata["human_review_required"] is True
    assert metadata["pdf_generated_in_memory"] is True
    assert metadata["server_side_file_written"] is False
    assert metadata["database_query_executed"] is False
    assert metadata["no_control_dispatch_activation"] is True
    assert connection.cursor_calls == 1
    assert len(connection.cursor_instance.calls) == 1
    assert connection.closed is True
    assert connection.captured_urls == [RAW_DATABASE_URL]  # type: ignore[attr-defined]


def test_persistence_call_writes_only_audit_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = install_fake_connection(monkeypatch)

    response = client.post("/api/audit/pdf-export/persist", json={})

    assert response.status_code == 200
    sql, params = connection.cursor_instance.calls[0]
    assert sql.startswith("INSERT INTO audit_events")
    assert "ON CONFLICT (event_id) DO NOTHING" in sql
    assert params["event_type"] == "report_pdf_export_requested"
    assert params["resource_type"] == "report"
    assert params["action"] == "manual_pdf_export"
    for table_name in FORBIDDEN_TABLES:
        assert table_name not in sql


def test_database_write_flag_is_true_only_on_audit_events_write_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = install_fake_connection(monkeypatch)

    response = client.post("/api/audit/pdf-export/persist", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["table"] == "audit_events"
    assert body["database_write_performed"] is True
    assert len(connection.cursor_instance.calls) == 1


def test_no_pdf_generation_file_writing_external_api_or_control_behavior() -> None:
    source = Path("app/api/audit.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert "app.reporting.pdf" not in imported_modules
    assert "requests" not in imported_modules
    assert "httpx" not in imported_modules
    assert "render_report_markdown_pdf_bytes" not in source
    assert "open(" not in source
    assert ".write(" not in source
    assert "spot_prices" not in source
    assert "power_balance" not in source
    assert "send_" + "control" not in source
    assert "live_" + "control" not in source
    assert "dispatch_" + "asset" not in source
    assert "activate_" + "asset" not in source


def test_only_specific_audit_persistence_post_route_is_allowed() -> None:
    audit_post_paths = {
        getattr(route, "path", None)
        for route in app.routes
        if "POST" in getattr(route, "methods", set())
        and str(getattr(route, "path", "")).startswith("/api/audit")
    }

    assert audit_post_paths == {
        "/api/audit/preview",
        "/api/audit/pdf-export/persist",
    }


def test_put_patch_delete_are_blocked_for_persistence_route() -> None:
    route_methods = {
        method
        for route in app.routes
        if getattr(route, "path", None) == "/api/audit/pdf-export/persist"
        for method in getattr(route, "methods", set())
    }

    assert route_methods == {"POST"}
    assert not route_methods & {"PUT", "PATCH", "DELETE"}
