from __future__ import annotations

import builtins
import importlib
from collections.abc import Mapping
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import report
from app.main import app


client = TestClient(app)

AUDITED_EXPORT_PATH = "/api/report/pdf/export/audited"
RAW_DATABASE_URL = "postgresql://user:super-secret-token@localhost/flexsignal_ai"
LOCAL_FRONTEND_ORIGIN = "http://localhost:3000"
FORBIDDEN_TABLES = (
    "spot_prices",
    "power_balance",
    "forecast",
    "energy_freshness",
)
EXPECTED_AUDITED_HEADERS = {
    "x-flexsignal-decision-support-only": "true",
    "x-flexsignal-file-written": "false",
    "x-flexsignal-pdf-generated-in-memory": "true",
    "x-flexsignal-audit-event-created": "true",
    "x-flexsignal-audit-event-persisted": "true",
    "x-flexsignal-audit-event-type": "report_pdf_export_requested",
    "x-flexsignal-audit-table": "audit_events",
    "x-flexsignal-database-query-executed": "false",
    "x-flexsignal-database-write-performed": "true",
    "x-flexsignal-database-write-scope": "audit_events_only",
    "x-flexsignal-requires-database-url": "true",
    "x-flexsignal-no-control-dispatch-activation": "true",
}


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
    monkeypatch.setattr(report, "connect_with_psycopg", fake_connect)
    connection.captured_urls = captured_urls  # type: ignore[attr-defined]
    return connection


def test_audited_route_exists() -> None:
    assert any(getattr(route, "path", None) == AUDITED_EXPORT_PATH for route in app.routes)


def test_app_import_works_without_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)

    assert any(
        getattr(route, "path", None) == AUDITED_EXPORT_PATH
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
    monkeypatch.setattr(report, "connect_with_psycopg", fake_connect)

    response = client.post(AUDITED_EXPORT_PATH, json={})

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["requires_database_url"] is True
    assert detail["audit_event_created"] is False
    assert detail["audit_event_persisted"] is False
    assert detail["pdf_generated_in_memory"] is False
    assert detail["server_side_file_written"] is False
    assert detail["database_query_executed"] is False
    assert detail["database_write_performed"] is False
    assert detail["table"] == "audit_events"
    assert RAW_DATABASE_URL not in repr(detail)
    assert "super-secret-token" not in repr(detail)
    assert connect_calls == 0


def test_successful_mocked_persistence_returns_pdf_bytes_and_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = install_fake_connection(monkeypatch)

    response = client.post(
        AUDITED_EXPORT_PATH,
        json={
            "price_area": "DK1",
            "occurred_at_utc": "2026-01-01T12:30:00Z",
            "request_id": "request-123",
            "source": "unit-test",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="flexsignal-report-preview.pdf"'
    )
    assert response.content.startswith(b"%PDF")
    for header_name, expected_value in EXPECTED_AUDITED_HEADERS.items():
        assert response.headers[header_name] == expected_value
    assert response.headers["x-flexsignal-audit-event-id"].startswith("audit_evt_")
    assert connection.cursor_calls == 1
    assert len(connection.cursor_instance.calls) == 1
    assert connection.closed is True
    assert connection.captured_urls == [RAW_DATABASE_URL]  # type: ignore[attr-defined]


def test_audit_event_matches_manual_pdf_export_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = install_fake_connection(monkeypatch)

    response = client.post(
        AUDITED_EXPORT_PATH,
        json={"price_area": "DK1", "occurred_at_utc": "2026-01-01T12:30:00Z"},
    )

    assert response.status_code == 200
    sql, params = connection.cursor_instance.calls[0]
    metadata = params["metadata"]
    assert sql.startswith("INSERT INTO audit_events")
    assert "ON CONFLICT (event_id) DO NOTHING" in sql
    assert params["event_type"] == "report_pdf_export_requested"
    assert params["action"] == "manual_pdf_export"
    assert params["resource_type"] == "report"
    assert params["resource_id"] == "report-summary-v0-DK1-872ff94f403e4ddd"
    assert params["decision_support_only"] is True
    assert '"human_review_required":true' in metadata
    assert '"pdf_generated_in_memory":true' in metadata
    assert '"server_side_file_written":false' in metadata
    assert '"database_query_executed":false' in metadata
    assert '"database_write_performed":false' in metadata
    assert '"no_control_dispatch_activation":true' in metadata


def test_database_write_scope_is_audit_events_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = install_fake_connection(monkeypatch)

    response = client.post(AUDITED_EXPORT_PATH, json={})

    assert response.status_code == 200
    assert response.headers["x-flexsignal-database-write-performed"] == "true"
    assert response.headers["x-flexsignal-database-write-scope"] == "audit_events_only"
    sql, _params = connection.cursor_instance.calls[0]
    for table_name in FORBIDDEN_TABLES:
        assert table_name not in sql


def test_cors_exposes_audited_pdf_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_connection(monkeypatch)

    response = client.post(
        AUDITED_EXPORT_PATH,
        json={},
        headers={"Origin": LOCAL_FRONTEND_ORIGIN},
    )

    exposed_headers = {
        header.strip().lower()
        for header in response.headers["access-control-expose-headers"].split(",")
    }

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == LOCAL_FRONTEND_ORIGIN
    assert set(EXPECTED_AUDITED_HEADERS) <= exposed_headers
    assert "content-disposition" in exposed_headers
    assert "x-flexsignal-audit-event-id" in exposed_headers


def test_no_server_side_file_write_live_api_or_control_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = install_fake_connection(monkeypatch)
    file_write_calls = 0
    open_calls = 0
    http_calls = 0

    def fail_open(*args: Any, **kwargs: Any) -> None:
        nonlocal open_calls
        open_calls += 1
        raise AssertionError("File access is not allowed")

    def fail_write_text(*args: Any, **kwargs: Any) -> None:
        nonlocal file_write_calls
        file_write_calls += 1
        raise AssertionError("File writes are not allowed")

    def fail_live_http_call(*args: Any, **kwargs: Any) -> None:
        nonlocal http_calls
        http_calls += 1
        raise AssertionError("Live HTTP calls are not allowed")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr("pathlib.Path.write_text", fail_write_text)
    monkeypatch.setattr("pathlib.Path.write_bytes", fail_write_text)
    monkeypatch.setattr("urllib.request.urlopen", fail_live_http_call)

    response = client.post(AUDITED_EXPORT_PATH, json={})

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    assert response.headers["x-flexsignal-file-written"] == "false"
    assert response.headers["x-flexsignal-no-control-dispatch-activation"] == "true"
    assert len(connection.cursor_instance.calls) == 1
    assert file_write_calls == 0
    assert open_calls == 0
    assert http_calls == 0


def test_put_patch_delete_are_blocked_for_audited_route() -> None:
    route_methods = {
        method
        for route in app.routes
        if getattr(route, "path", None) == AUDITED_EXPORT_PATH
        for method in getattr(route, "methods", set())
    }

    assert route_methods == {"POST"}
    assert not route_methods & {"PUT", "PATCH", "DELETE"}
