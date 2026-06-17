from __future__ import annotations

import ast
import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from app.audit.runtime_plan import (
    build_current_risk_viewed_audit_plan,
    build_forecast_preview_requested_audit_plan,
    build_report_markdown_rendered_audit_plan,
    build_report_pdf_exported_audit_plan,
    build_report_summary_built_audit_plan,
)


RUNTIME_PLAN_PATH = Path("app/audit/runtime_plan.py")
OCCURRED_AT = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)
CONFLICT_BEHAVIOR = "ON CONFLICT (event_id) DO NOTHING"


PlanFactory = Callable[..., dict[str, Any]]


PLAN_CASES: tuple[tuple[PlanFactory, str, str, str], ...] = (
    (
        build_current_risk_viewed_audit_plan,
        "current_risk_viewed",
        "view_current_risk",
        "risk_snapshot",
    ),
    (
        build_forecast_preview_requested_audit_plan,
        "forecast_preview_requested",
        "preview_forecast",
        "forecast_preview",
    ),
    (
        build_report_summary_built_audit_plan,
        "report_summary_built",
        "build_report_summary",
        "report_summary",
    ),
    (
        build_report_markdown_rendered_audit_plan,
        "report_markdown_rendered",
        "render_report_markdown",
        "report_markdown",
    ),
    (
        build_report_pdf_exported_audit_plan,
        "report_pdf_exported",
        "preview_report_pdf_export",
        "report_pdf",
    ),
)


@pytest.mark.parametrize(
    ("factory", "event_type", "action", "resource_type"),
    PLAN_CASES,
)
def test_each_runtime_plan_is_dry_run_only(
    factory: PlanFactory,
    event_type: str,
    action: str,
    resource_type: str,
) -> None:
    plan = factory(price_area="DK1", occurred_at_utc=OCCURRED_AT)

    assert plan["dry_run"] is True
    assert plan["database_write_performed"] is False
    assert plan["requires_database_url"] is False
    assert plan["event"]
    assert plan["persistence_plan"]
    assert plan["event_id"] == plan["event"]["event_id"]
    assert plan["event_type"] == event_type
    assert plan["table"] == "audit_events"
    assert plan["conflict_behavior"] == CONFLICT_BEHAVIOR
    assert plan["warnings"]


@pytest.mark.parametrize(
    ("factory", "event_type", "action", "resource_type"),
    PLAN_CASES,
)
def test_event_mapping_matches_runtime_event_factories(
    factory: PlanFactory,
    event_type: str,
    action: str,
    resource_type: str,
) -> None:
    plan = factory(price_area="DK2", occurred_at_utc=OCCURRED_AT)
    event = plan["event"]

    assert event["event_version"] == "audit-event-v0"
    assert event["event_type"] == event_type
    assert event["action"] == action
    assert event["resource_type"] == resource_type
    assert "DK2" in event["resource_id"]
    assert event["outcome"] == "success"


@pytest.mark.parametrize(
    ("factory", "event_type", "action", "resource_type"),
    PLAN_CASES,
)
def test_persistence_plan_uses_repository_insert_builder(
    factory: PlanFactory,
    event_type: str,
    action: str,
    resource_type: str,
) -> None:
    plan = factory(price_area="DK1", occurred_at_utc=OCCURRED_AT)
    persistence_plan = plan["persistence_plan"]

    assert persistence_plan["table"] == "audit_events"
    assert persistence_plan["operation"] == "insert_audit_event_v0"
    assert persistence_plan["event_id"] == plan["event_id"]
    assert persistence_plan["idempotency_key"] == plan["event_id"]
    assert persistence_plan["conflict_behavior"] == CONFLICT_BEHAVIOR
    assert CONFLICT_BEHAVIOR in persistence_plan["sql_preview"]
    assert persistence_plan["execution_performed"] is False
    assert sorted(persistence_plan["params"]) == persistence_plan["param_keys"]
    assert persistence_plan["params"]["event_id"] == plan["event_id"]
    assert persistence_plan["params"]["event_version"] == "audit-event-v0"
    assert persistence_plan["params"]["decision_support_only"] is True


def test_repository_params_include_safe_serialized_jsonb_fields() -> None:
    plan = build_forecast_preview_requested_audit_plan(
        price_area="DK1",
        actor_id="developer-1",
        occurred_at_utc=OCCURRED_AT,
        request_id="request-123",
        source="unit-test",
        model_version="baseline-window-v0",
    )
    params = plan["persistence_plan"]["params"]
    metadata = json.loads(params["metadata"])
    boundary = json.loads(params["safety_boundary"])

    assert metadata == {
        "forecast_window_version": "forecast-window-v0",
        "model_version": "baseline-window-v0",
        "price_area": "DK1",
        "request_id": "request-123",
        "runtime_factory_version": "audit-runtime-event-factory-v0",
        "source": "unit-test",
    }
    assert boundary == plan["event"]["safety_boundary"]


@pytest.mark.parametrize(
    ("factory", "event_type", "action", "resource_type"),
    PLAN_CASES,
)
def test_metadata_remains_safe_and_minimal(
    factory: PlanFactory,
    event_type: str,
    action: str,
    resource_type: str,
) -> None:
    plan = factory(
        price_area="DK1",
        occurred_at_utc=OCCURRED_AT,
        request_id="request-123",
        source="unit-test",
    )
    metadata = plan["event"]["metadata"]
    rendered_plan = repr(plan)

    assert metadata["price_area"] == "DK1"
    assert metadata["request_id"] == "request-123"
    assert metadata["source"] == "unit-test"
    assert "DATA" + "BASE_URL" not in rendered_plan
    assert "secret" not in rendered_plan.lower()
    assert "token" not in rendered_plan.lower()
    assert "headers" not in rendered_plan.lower()
    assert "body" not in rendered_plan.lower()
    assert "claims" not in rendered_plan.lower()


@pytest.mark.parametrize(
    ("factory", "event_type", "action", "resource_type"),
    PLAN_CASES,
)
def test_safety_boundary_is_preserved(
    factory: PlanFactory,
    event_type: str,
    action: str,
    resource_type: str,
) -> None:
    plan = factory(price_area="DK1", occurred_at_utc=OCCURRED_AT)
    boundary = plan["safety_boundary"]
    event_boundary = plan["event"]["safety_boundary"]

    assert boundary["event_version"] == "audit-event-v0"
    assert boundary["decision_support_only"] is True
    assert event_boundary["read_only_decision_support"] is True
    assert event_boundary["no_automatic_control"] is True
    assert event_boundary["no_dispatch"] is True
    assert event_boundary["no_activation"] is True
    assert event_boundary["no_operational_energy_system_integration"] is True
    assert event_boundary["human_review_required"] is True
    assert boundary["read_only_decision_support"] is True
    assert boundary["no_automatic_control"] is True
    assert boundary["no_dispatch"] is True
    assert boundary["no_activation"] is True
    assert boundary["no_operational_energy_system_integration"] is True
    assert boundary["human_review_required"] is True


def test_deterministic_occurred_at_can_be_injected() -> None:
    first = build_report_pdf_exported_audit_plan(
        price_area="DK1",
        occurred_at_utc=OCCURRED_AT,
    )
    second = build_report_pdf_exported_audit_plan(
        price_area="DK1",
        occurred_at_utc=OCCURRED_AT,
    )

    assert first["event"]["occurred_at_utc"] == OCCURRED_AT
    assert first["event_id"] == second["event_id"]


def test_runtime_plan_module_does_not_import_fastapi_or_router() -> None:
    source = RUNTIME_PLAN_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_names = {
        alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert "fastapi" not in imported_names
    assert "Fast" + "API" not in source
    assert "API" + "Router" not in source


def test_runtime_plan_module_does_not_import_audit_writer() -> None:
    source = RUNTIME_PLAN_PATH.read_text(encoding="utf-8")
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

    assert "app.audit." + "writer" not in imported_modules
    assert "write_" + "audit_event" not in imported_names
    assert "execute_" + "audit_event_insert" not in source


def test_runtime_plan_module_does_not_read_database_url() -> None:
    source = RUNTIME_PLAN_PATH.read_text(encoding="utf-8")

    assert "DATA" + "BASE_URL" not in source
    assert "getenv" not in source
    assert "environ" not in source


def test_runtime_plan_module_does_not_execute_sql() -> None:
    source = RUNTIME_PLAN_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    call_names = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert "execute" not in call_names
    assert "connect" not in source
    assert "execute" + "(" not in source


def test_runtime_plan_module_has_no_external_or_operational_integration_terms() -> None:
    source = RUNTIME_PLAN_PATH.read_text(encoding="utf-8")
    forbidden_terms = [
        "api.energi" + "dataservice",
        "D" + "MI",
        "sched" + "uler",
        "Az" + "ure",
    ]

    for term in forbidden_terms:
        assert term not in source
