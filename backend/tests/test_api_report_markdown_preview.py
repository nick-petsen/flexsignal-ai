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
PREVIEW_PATH = "/api/report/markdown/preview"
EXPECTED_SAFETY_BOUNDARY = {
    "read_only_decision_support": True,
    "no_automatic_control": True,
    "no_dispatch": True,
    "no_activation": True,
    "no_operational_energy_system_integration": True,
    "human_review_required": True,
}


def test_route_exists() -> None:
    assert any(getattr(route, "path", None) == PREVIEW_PATH for route in app.routes)


def test_preview_returns_http_200_and_required_flags() -> None:
    response = client.post(PREVIEW_PATH, json={})

    assert response.status_code == 200
    body = response.json()
    assert body["markdown_preview_generated"] is True
    assert isinstance(body["markdown"], str)
    assert body["markdown"].strip()
    assert body["pdf_generated"] is False
    assert body["file_written"] is False
    assert body["database_query_executed"] is False
    assert body["database_write_performed"] is False
    assert body["requires_database_url"] is False
    assert body["decision_support_only"] is True
    assert body["safety_boundary"] == EXPECTED_SAFETY_BOUNDARY


def test_preview_returns_report_summary_and_markdown_sections() -> None:
    response = client.post(
        PREVIEW_PATH,
        json={
            "price_area": "DK2",
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "scenario": "high-risk",
            "title": "Read-only Markdown preview",
        },
    )

    assert response.status_code == 200
    body = response.json()
    summary = body["report_summary"]
    markdown = body["markdown"]

    assert summary["price_area"] == "DK2"
    assert summary["report_version"] == "report-summary-v0"
    assert summary["decision_support_only"] is True
    assert summary["human_review_required"] is True
    assert summary["current_risk_summary"]["risk_level"] == "high"
    assert "# Read-only Markdown preview" in markdown
    assert "## Report metadata" in markdown
    assert "| price_area | DK2 |" in markdown
    assert "| generated_at_utc | 2026-01-01T00:00:00Z |" in markdown
    assert "## Current risk summary" in markdown
    assert "## Forecast window summary" in markdown
    assert "## Key findings" in markdown
    assert "## Recommended human actions" in markdown
    assert "## Safety notes" in markdown
    assert "## Limitations" in markdown


def test_markdown_clearly_states_preview_and_safety_boundaries() -> None:
    response = client.post(PREVIEW_PATH, json={})

    assert response.status_code == 200
    markdown = response.json()["markdown"]

    expected_phrases = [
        "JSON/Markdown preview only",
        "no PDF generated",
        "no file written",
        "no database read/write",
        "no live EDS/DMI calls",
        "no control, dispatch, or activation",
        "read-only decision support",
        "human review required",
    ]
    for phrase in expected_phrases:
        assert phrase in markdown


def test_preview_accepts_caller_provided_inputs_only() -> None:
    response = client.post(
        PREVIEW_PATH,
        json={
            "price_area": "DK1",
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "current_risk": {
                "risk_level": "low",
                "risk_score": 10,
                "confidence_score": 0.8,
                "reason_codes": ["NORMAL_PRICE"],
                "recommended_human_action": "Review caller-provided context.",
                "model_version": "caller-risk-v0",
            },
            "forecast": {
                "model_version": "caller-forecast-v0",
                "windows": [
                    {
                        "window_label": "0-24h",
                        "risk_level": "low",
                        "row_count": 1,
                        "max_risk_score": 10,
                        "average_risk_score": 10.0,
                        "top_reason_codes": [
                            {"reason_code": "NORMAL_PRICE", "count": 1}
                        ],
                        "recommended_human_action": (
                            "Continue human monitoring."
                        ),
                    }
                ],
            },
            "source_notes": ["unit-test caller data"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    summary = body["report_summary"]
    markdown = body["markdown"]
    assert summary["current_risk_summary"]["model_version"] == "caller-risk-v0"
    assert (
        summary["forecast_window_summary"]["model_version"]
        == "caller-forecast-v0"
    )
    assert "unit-test caller data" in summary["source_notes"]
    assert "unit-test caller data" in markdown


def test_app_import_works_without_database_url(monkeypatch: Any) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)

    assert any(
        getattr(route, "path", None) == PREVIEW_PATH
        for route in reloaded_main.app.routes
    )


def test_endpoint_does_not_require_database_url(monkeypatch: Any) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.post(PREVIEW_PATH, json={})

    assert response.status_code == 200
    assert response.json()["requires_database_url"] is False


def test_no_mutating_http_methods_beyond_allowed_preview_post_patterns() -> None:
    report_routes = [
        route
        for route in app.routes
        if str(getattr(route, "path", "")).startswith("/api/report")
    ]

    assert report_routes
    assert all(getattr(route, "methods", set()) <= {"POST"} for route in report_routes)
    assert any(
        getattr(route, "path", None) == "/api/report/summary/preview"
        and getattr(route, "methods", set()) == {"POST"}
        for route in report_routes
    )
    assert any(
        getattr(route, "path", None) == PREVIEW_PATH
        and getattr(route, "methods", set()) == {"POST"}
        for route in report_routes
    )
    assert not any(
        getattr(route, "methods", set()) & {"PUT", "PATCH", "DELETE"}
        for route in report_routes
    )


def test_report_api_imports_no_file_pdf_db_sql_or_external_api_modules() -> None:
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
        "app.reporting.pdf",
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
        "render_report_markdown_pdf_bytes",
    }

    assert imported_modules.isdisjoint(forbidden_modules)
    assert imported_names.isdisjoint(forbidden_names)
    assert "DATABASE_URL" not in source


def test_report_api_performs_no_file_pdf_db_sql_external_or_action_calls() -> None:
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
        "save",
        "build",
        "urlopen",
        "request",
    }
    forbidden_direct_calls = {
        "open",
        "print",
        "render_report_markdown_pdf_bytes",
    }
    forbidden_sql_operations = {"INSERT", "UPDATE", "DELETE", "UPSERT", "DROP"}

    assert call_names.isdisjoint(forbidden_attribute_calls)
    assert direct_call_names.isdisjoint(forbidden_direct_calls)
    assert forbidden_sql_operations.isdisjoint(source.upper().split())
    assert all("control" not in path for path in route_paths)
    assert all("dispatch" not in path for path in route_paths)
    assert all("activation" not in path for path in route_paths)


def test_preview_makes_no_file_db_external_api_or_pdf_calls(monkeypatch: Any) -> None:
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

    response = client.post(PREVIEW_PATH, json={})

    assert response.status_code == 200
    body = response.json()
    assert body["pdf_generated"] is False
    assert body["file_written"] is False
    assert body["database_query_executed"] is False
    assert body["database_write_performed"] is False
    assert file_write_calls == 0
    assert open_calls == 0
    assert http_calls == 0
