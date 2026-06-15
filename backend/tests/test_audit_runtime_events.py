from __future__ import annotations

import ast
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from app.audit.runtime_events import (
    RUNTIME_FACTORY_VERSION,
    build_current_risk_viewed_event,
    build_forecast_preview_requested_event,
    build_report_markdown_rendered_event,
    build_report_pdf_exported_event,
    build_report_summary_built_event,
)


RUNTIME_EVENTS_PATH = Path("app/audit/runtime_events.py")
OCCURRED_AT = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)


Factory = Callable[..., dict[str, Any]]


FACTORY_CASES: tuple[tuple[Factory, str, str, str], ...] = (
    (
        build_current_risk_viewed_event,
        "current_risk_viewed",
        "view_current_risk",
        "risk_snapshot",
    ),
    (
        build_forecast_preview_requested_event,
        "forecast_preview_requested",
        "preview_forecast",
        "forecast_preview",
    ),
    (
        build_report_summary_built_event,
        "report_summary_built",
        "build_report_summary",
        "report_summary",
    ),
    (
        build_report_markdown_rendered_event,
        "report_markdown_rendered",
        "render_report_markdown",
        "report_markdown",
    ),
    (
        build_report_pdf_exported_event,
        "report_pdf_exported",
        "preview_report_pdf_export",
        "report_pdf",
    ),
)


@pytest.mark.parametrize(
    ("factory", "event_type", "action", "resource_type"),
    FACTORY_CASES,
)
def test_each_factory_returns_expected_event_mapping(
    factory: Factory,
    event_type: str,
    action: str,
    resource_type: str,
) -> None:
    event = factory(price_area="DK1", occurred_at_utc=OCCURRED_AT)

    assert event["event_version"] == "audit-event-v0"
    assert event["event_type"] == event_type
    assert event["action"] == action
    assert event["resource_type"] == resource_type
    assert "DK1" in event["resource_id"]
    assert event["outcome"] == "success"
    assert event["actor_type"] == "local_developer"
    assert event["actor_id"] == "unknown-local-user"


@pytest.mark.parametrize(
    ("factory", "event_type", "action", "resource_type"),
    FACTORY_CASES,
)
def test_each_factory_preserves_decision_support_safety_boundary(
    factory: Factory,
    event_type: str,
    action: str,
    resource_type: str,
) -> None:
    event = factory(price_area="DK2", occurred_at_utc=OCCURRED_AT)
    boundary = event["safety_boundary"]

    assert event["decision_support_only"] is True
    assert boundary["read_only_decision_support"] is True
    assert boundary["no_automatic_" + "con" + "trol"] is True
    assert boundary["no_" + "dis" + "patch"] is True
    assert boundary["no_" + "acti" + "vation"] is True
    assert boundary["no_operational_energy_system_integration"] is True
    assert boundary["human_review_required"] is True


@pytest.mark.parametrize(
    ("factory", "event_type", "action", "resource_type"),
    FACTORY_CASES,
)
def test_each_factory_adds_minimal_safe_metadata(
    factory: Factory,
    event_type: str,
    action: str,
    resource_type: str,
) -> None:
    event = factory(
        price_area="DK1",
        actor_id="developer-1",
        occurred_at_utc=OCCURRED_AT,
        request_id="request-123",
        source="unit-test",
    )
    metadata = event["metadata"]

    assert metadata["price_area"] == "DK1"
    assert metadata["request_id"] == "request-123"
    assert metadata["source"] == "unit-test"
    assert metadata["runtime_factory_version"] == RUNTIME_FACTORY_VERSION
    assert "DATA" + "BASE_URL" not in metadata
    assert "secret" not in metadata
    assert "token" not in metadata
    assert "headers" not in metadata
    assert "body" not in metadata


def test_forecast_preview_metadata_and_resource_id_include_window_version() -> None:
    event = build_forecast_preview_requested_event(
        price_area="DK1",
        occurred_at_utc=OCCURRED_AT,
        forecast_window_version="forecast-window-v0",
        model_version="baseline-window-v0",
    )

    assert "forecast-window-v0" in event["resource_id"]
    assert event["metadata"]["forecast_window_version"] == "forecast-window-v0"
    assert event["metadata"]["model_version"] == "baseline-window-v0"


def test_report_events_include_report_version_and_output_format_when_relevant() -> None:
    summary = build_report_summary_built_event(
        price_area="DK1",
        occurred_at_utc=OCCURRED_AT,
    )
    markdown = build_report_markdown_rendered_event(
        price_area="DK1",
        occurred_at_utc=OCCURRED_AT,
    )
    pdf = build_report_pdf_exported_event(
        price_area="DK1",
        occurred_at_utc=OCCURRED_AT,
    )

    assert "report-summary-v0" in summary["resource_id"]
    assert summary["metadata"]["report_version"] == "report-summary-v0"
    assert "report-summary-v0" in markdown["resource_id"]
    assert markdown["metadata"]["report_version"] == "report-summary-v0"
    assert markdown["metadata"]["output_format"] == "markdown"
    assert "report-summary-v0" in pdf["resource_id"]
    assert pdf["metadata"]["report_version"] == "report-summary-v0"
    assert pdf["metadata"]["output_format"] == "pdf"


def test_deterministic_occurred_at_can_be_injected() -> None:
    event = build_current_risk_viewed_event(
        price_area="DK1",
        occurred_at_utc=OCCURRED_AT,
    )

    assert event["occurred_at_utc"] == OCCURRED_AT


@pytest.mark.parametrize(
    ("factory", "event_type", "action", "resource_type"),
    FACTORY_CASES,
)
def test_event_id_is_deterministic_for_same_inputs(
    factory: Factory,
    event_type: str,
    action: str,
    resource_type: str,
) -> None:
    first = factory(price_area="DK1", occurred_at_utc=OCCURRED_AT)
    second = factory(price_area="DK1", occurred_at_utc=OCCURRED_AT)

    assert first["event_id"] == second["event_id"]


def test_optional_actor_id_none_defaults_to_unknown_local_user() -> None:
    event = build_current_risk_viewed_event(
        price_area="DK1",
        actor_id=None,
        occurred_at_utc=OCCURRED_AT,
    )

    assert event["actor_id"] == "unknown-local-user"


@pytest.mark.parametrize("bad_price_area", ["", "   "])
def test_price_area_must_not_be_empty(bad_price_area: str) -> None:
    with pytest.raises(ValueError, match="price_area must not be empty"):
        build_current_risk_viewed_event(price_area=bad_price_area)


def test_runtime_events_module_does_not_import_fastapi_or_router() -> None:
    source = RUNTIME_EVENTS_PATH.read_text(encoding="utf-8")
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


def test_runtime_events_module_does_not_import_audit_writer() -> None:
    source = RUNTIME_EVENTS_PATH.read_text(encoding="utf-8")
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


def test_runtime_events_module_does_not_read_database_url() -> None:
    source = RUNTIME_EVENTS_PATH.read_text(encoding="utf-8")

    assert "DATA" + "BASE_URL" not in source
    assert "getenv" not in source
    assert "environ" not in source


def test_runtime_events_module_has_no_runtime_integration_terms() -> None:
    source = RUNTIME_EVENTS_PATH.read_text(encoding="utf-8")
    forbidden_terms = [
        "api.energi" + "dataservice",
        "D" + "MI",
        "sched" + "uler",
        "Az" + "ure",
        "dis" + "patch",
        "acti" + "vation",
        "con" + "trol",
    ]

    for term in forbidden_terms:
        assert term not in source
