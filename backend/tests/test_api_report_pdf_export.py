from __future__ import annotations

import ast
import builtins
import importlib
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

REPORT_API_PATH = Path("app/api/report.py")
EXPORT_PATH = "/api/report/pdf/export"
EXPECTED_REPORT_ROUTES = {
    "/api/report/summary/preview",
    "/api/report/markdown/preview",
    "/api/report/pdf/preview",
    EXPORT_PATH,
}


def test_route_exists() -> None:
    assert any(getattr(route, "path", None) == EXPORT_PATH for route in app.routes)


def test_export_returns_http_200_pdf_and_required_headers() -> None:
    response = client.post(EXPORT_PATH, json={})

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="flexsignal-report-preview.pdf"'
    )
    assert response.headers["x-flexsignal-decision-support-only"] == "true"
    assert response.headers["x-flexsignal-file-written"] == "false"
    assert response.headers["x-flexsignal-database-query-executed"] == "false"
    assert response.headers["x-flexsignal-database-write-performed"] == "false"
    assert response.headers["x-flexsignal-requires-database-url"] == "false"
    assert response.content
    assert response.content.startswith(b"%PDF")


def test_export_pdf_uses_report_summary_markdown_content() -> None:
    response = client.post(
        EXPORT_PATH,
        json={
            "price_area": "DK2",
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "scenario": "high-risk",
            "title": "Read-only PDF export preview",
            "source_notes": ["unit-test export data"],
        },
    )

    assert response.status_code == 200
    pdf = response.content
    expected_phrases = [
        b"Read-only PDF export preview",
        b"price_area: DK2",
        b"generated_at_utc: 2026-01-01T00:00:00Z",
        b"Current risk summary",
        b"Forecast window summary",
        b"Key findings",
        b"Recommended human actions",
        b"Safety notes",
        b"Limitations",
        b"read-only decision support",
        b"human review required",
        b"no control, dispatch, or activation",
        b"unit-test export data",
    ]

    for phrase in expected_phrases:
        assert phrase in pdf


def test_app_import_works_without_database_url(monkeypatch: Any) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)

    assert any(
        getattr(route, "path", None) == EXPORT_PATH
        for route in reloaded_main.app.routes
    )


def test_endpoint_does_not_require_database_url(monkeypatch: Any) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.post(EXPORT_PATH, json={})

    assert response.status_code == 200
    assert response.headers["x-flexsignal-requires-database-url"] == "false"
    assert response.content.startswith(b"%PDF")


def test_no_mutating_http_methods_beyond_allowed_preview_and_export_posts() -> None:
    report_routes = [
        route
        for route in app.routes
        if str(getattr(route, "path", "")).startswith("/api/report")
    ]
    route_paths = {getattr(route, "path", None) for route in report_routes}

    assert report_routes
    assert all(getattr(route, "methods", set()) <= {"POST"} for route in report_routes)
    assert EXPECTED_REPORT_ROUTES <= route_paths
    assert not any(
        getattr(route, "methods", set()) & {"PUT", "PATCH", "DELETE"}
        for route in report_routes
    )


def test_report_api_imports_no_file_db_sql_or_external_api_modules() -> None:
    source = REPORT_API_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    forbidden_modules = {
        "app.db",
        "app.db.executor",
        "app.db.transaction",
        "app.integrations",
        "app.integrations.energi_data_service",
        "pathlib",
        "requests",
        "httpx",
        "urllib.request",
        "psycopg",
        "sqlalchemy",
    }
    forbidden_names = {
        "Path",
        "open",
    }

    assert imported_modules.isdisjoint(forbidden_modules)
    assert imported_names.isdisjoint(forbidden_names)
    assert "DATABASE_URL" not in source


def test_report_api_performs_no_file_db_sql_external_or_action_route_calls() -> None:
    source = REPORT_API_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    call_names = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    direct_call_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    route_paths = [
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"get", "post", "put", "patch", "delete"}
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    ]

    forbidden_attribute_calls = {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "open",
        "write",
        "write_text",
        "write_bytes",
        "build",
        "urlopen",
        "request",
    }
    forbidden_direct_calls = {
        "open",
        "print",
    }
    forbidden_sql_operations = {"INSERT", "UPDATE", "DELETE", "UPSERT", "DROP"}

    assert call_names.isdisjoint(forbidden_attribute_calls)
    assert direct_call_names.isdisjoint(forbidden_direct_calls)
    assert forbidden_sql_operations.isdisjoint(source.upper().split())
    assert all("control" not in path for path in route_paths)
    assert all("dispatch" not in path for path in route_paths)
    assert all("activation" not in path for path in route_paths)


def test_export_makes_no_file_db_or_external_api_calls(monkeypatch: Any) -> None:
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

    response = client.post(EXPORT_PATH, json={})

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")
    assert response.headers["x-flexsignal-file-written"] == "false"
    assert response.headers["x-flexsignal-database-query-executed"] == "false"
    assert response.headers["x-flexsignal-database-write-performed"] == "false"
    assert file_write_calls == 0
    assert open_calls == 0
    assert http_calls == 0
