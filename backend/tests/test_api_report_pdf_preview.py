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
PREVIEW_PATH = "/api/report/pdf/preview"
EXPECTED_SAFETY_BOUNDARY = {
    "read_only_decision_support": True,
    "no_automatic_control": True,
    "no_dispatch": True,
    "no_activation": True,
    "no_operational_energy_system_integration": True,
    "human_review_required": True,
}
EXPECTED_WARNINGS = [
    "dry-run preview only",
    "no PDF generated",
    "no file written",
    "no database read/write",
    "no live EDS/DMI calls",
    "no control, dispatch, or activation",
]


def test_route_exists() -> None:
    assert any(getattr(route, "path", None) == PREVIEW_PATH for route in app.routes)


def test_preview_returns_http_200_and_required_flags() -> None:
    response = client.post(PREVIEW_PATH, json={})

    assert response.status_code == 200
    body = response.json()
    assert body["pdf_preview_planned"] is True
    assert body["pdf_generated"] is False
    assert body["file_written"] is False
    assert body["markdown_preview_generated"] is True
    assert body["database_query_executed"] is False
    assert body["database_write_performed"] is False
    assert body["requires_database_url"] is False
    assert body["decision_support_only"] is True
    assert body["planned_source"] == "report-summary-v0 + markdown preview"
    assert body["planned_output_format"] == "pdf"
    assert body["safety_boundary"] == EXPECTED_SAFETY_BOUNDARY
    assert body["warnings"] == EXPECTED_WARNINGS


def test_preview_returns_report_summary_and_markdown_excerpt() -> None:
    response = client.post(
        PREVIEW_PATH,
        json={
            "price_area": "DK2",
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "scenario": "high-risk",
            "title": "Read-only PDF dry-run preview",
        },
    )

    assert response.status_code == 200
    body = response.json()
    summary = body["report_summary"]
    markdown_excerpt = body["markdown_excerpt"]

    assert summary["price_area"] == "DK2"
    assert summary["report_version"] == "report-summary-v0"
    assert summary["decision_support_only"] is True
    assert summary["human_review_required"] is True
    assert summary["current_risk_summary"]["risk_level"] == "high"
    assert "# Read-only PDF dry-run preview" in markdown_excerpt
    assert "## Report metadata" in markdown_excerpt
    assert "| price_area | DK2 |" in markdown_excerpt
    assert body["markdown_character_count"] >= len(markdown_excerpt)


def test_preview_warnings_clearly_state_dry_run_boundaries() -> None:
    response = client.post(PREVIEW_PATH, json={})

    assert response.status_code == 200
    body = response.json()
    warning_text = " ".join(body["warnings"])
    source_notes = body["report_summary"]["source_notes"]

    for phrase in EXPECTED_WARNINGS:
        assert phrase in warning_text
        assert phrase in source_notes
    assert "planned source: report-summary-v0 + markdown preview" in source_notes
    assert "planned output format: pdf" in source_notes


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
    assert summary["current_risk_summary"]["model_version"] == "caller-risk-v0"
    assert (
        summary["forecast_window_summary"]["model_version"]
        == "caller-forecast-v0"
    )
    assert "unit-test caller data" in summary["source_notes"]


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
    route_paths = {getattr(route, "path", None) for route in report_routes}

    assert report_routes
    assert all(getattr(route, "methods", set()) <= {"POST"} for route in report_routes)
    assert {
        "/api/report/summary/preview",
        "/api/report/markdown/preview",
        PREVIEW_PATH,
        "/api/report/pdf/export",
    } <= route_paths
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
    assert body["markdown_preview_generated"] is True
    assert not response.content.startswith(b"%PDF")
    assert "%PDF" not in body["markdown_excerpt"]
    assert file_write_calls == 0
    assert open_calls == 0
    assert http_calls == 0
