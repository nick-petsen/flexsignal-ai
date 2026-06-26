from __future__ import annotations

import importlib
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

CONFLICT_BEHAVIOR = "ON CONFLICT (event_id) DO NOTHING"
SUPPORTED_EVENT_TYPES = (
    "current_risk_viewed",
    "forecast_preview_requested",
    "report_summary_built",
    "report_markdown_rendered",
    "report_pdf_export_requested",
    "report_pdf_exported",
)
BASE_PAYLOAD = {
    "price_area": "DK1",
    "occurred_at_utc": "2026-01-01T12:30:00Z",
    "request_id": "request-123",
    "source": "unit-test",
}


def _payload(event_type: str, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        **BASE_PAYLOAD,
        "event_type": event_type,
    }
    payload.update(overrides)
    return payload


def test_endpoint_exists() -> None:
    assert any(
        getattr(route, "path", None) == "/api/audit/preview"
        for route in app.routes
    )


@pytest.mark.parametrize("event_type", SUPPORTED_EVENT_TYPES)
def test_each_supported_event_type_returns_dry_run_plan(event_type: str) -> None:
    response = client.post("/api/audit/preview", json=_payload(event_type))

    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert body["audit_event_created"] is True
    assert body["audit_event_persisted"] is False
    assert body["database_write_performed"] is False
    assert body["requires_database_url"] is False
    assert body["event"]
    assert body["persistence_plan"]
    assert body["event_id"] == body["event"]["event_id"]
    assert body["event_type"] == event_type
    assert body["table"] == "audit_events"
    assert body["conflict_behavior"] == CONFLICT_BEHAVIOR
    assert body["persistence_plan"]["table"] == "audit_events"
    assert body["persistence_plan"]["execution_performed"] is False
    assert CONFLICT_BEHAVIOR in body["persistence_plan"]["sql_preview"]


def test_default_actor_fields_are_safe_local_values() -> None:
    response = client.post(
        "/api/audit/preview",
        json={"event_type": "current_risk_viewed", "price_area": "DK1"},
    )

    assert response.status_code == 200
    event = response.json()["event"]
    assert event["actor_type"] == "local_user"
    assert event["actor_id"] == "unknown-local-user"


def test_report_pdf_export_requested_defaults_to_dk1_manual_dry_run_event() -> None:
    response = client.post(
        "/api/audit/preview",
        json={
            "event_type": "report_pdf_export_requested",
            "occurred_at_utc": "2026-01-01T12:30:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    event = body["event"]
    metadata = event["metadata"]
    assert body["dry_run"] is True
    assert body["audit_event_created"] is True
    assert body["audit_event_persisted"] is False
    assert body["database_write_performed"] is False
    assert body["requires_database_url"] is False
    assert event["event_version"] == "audit-event-v0"
    assert event["event_type"] == "report_pdf_export_requested"
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
    assert metadata["database_write_performed"] is False
    assert metadata["requires_database_url"] is False
    assert metadata["no_control_dispatch_activation"] is True


def test_optional_fields_are_used_where_relevant() -> None:
    response = client.post(
        "/api/audit/preview",
        json=_payload(
            "report_pdf_exported",
            price_area="DK2",
            actor_type="human_user",
            actor_id="reviewer-1",
            report_version="report-summary-v-test",
            output_format="pdf",
        ),
    )

    assert response.status_code == 200
    event = response.json()["event"]
    assert event["actor_type"] == "human_user"
    assert event["actor_id"] == "reviewer-1"
    assert event["metadata"]["price_area"] == "DK2"
    assert event["metadata"]["report_version"] == "report-summary-v-test"
    assert event["metadata"]["output_format"] == "pdf"


def test_forecast_window_version_is_used_for_forecast_event() -> None:
    response = client.post(
        "/api/audit/preview",
        json=_payload(
            "forecast_preview_requested",
            forecast_window_version="forecast-window-v-test",
        ),
    )

    assert response.status_code == 200
    event = response.json()["event"]
    assert event["metadata"]["forecast_window_version"] == "forecast-window-v-test"
    assert "forecast-window-v-test" in event["resource_id"]


def test_invalid_event_type_returns_400() -> None:
    response = client.post(
        "/api/audit/preview",
        json=_payload("unsupported_event"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported event_type"


def test_invalid_price_area_returns_400() -> None:
    response = client.post(
        "/api/audit/preview",
        json=_payload("current_risk_viewed", price_area="SE3"),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported price_area"


def test_response_contains_no_sensitive_runtime_context() -> None:
    response = client.post(
        "/api/audit/preview",
        json=_payload("current_risk_viewed"),
    )

    assert response.status_code == 200
    rendered = repr(response.json())
    assert "DATA" + "BASE_URL" not in rendered
    assert "secret" not in rendered.lower()
    assert "token" not in rendered.lower()
    assert "headers" not in rendered.lower()
    assert "body" not in rendered.lower()


def test_safety_boundary_is_preserved() -> None:
    response = client.post(
        "/api/audit/preview",
        json=_payload("report_summary_built"),
    )

    assert response.status_code == 200
    body = response.json()
    boundary = body["safety_boundary"]
    event_boundary = body["event"]["safety_boundary"]
    assert body["event"]["decision_support_only"] is True
    assert boundary["decision_support_only"] is True
    assert boundary["read_only_decision_support"] is True
    assert boundary["no_automatic_control"] is True
    assert boundary["no_dispatch"] is True
    assert boundary["no_activation"] is True
    assert boundary["no_operational_energy_system_integration"] is True
    assert boundary["human_review_required"] is True
    assert event_boundary["read_only_decision_support"] is True
    assert event_boundary["no_automatic_control"] is True
    assert event_boundary["no_dispatch"] is True
    assert event_boundary["no_activation"] is True
    assert event_boundary["no_operational_energy_system_integration"] is True
    assert event_boundary["human_review_required"] is True


def test_app_import_without_database_url_still_exposes_endpoint(
    monkeypatch: Any,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)

    assert any(
        getattr(route, "path", None) == "/api/audit/preview"
        for route in reloaded_main.app.routes
    )


def test_endpoint_does_not_require_database_url(monkeypatch: Any) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.post(
        "/api/audit/preview",
        json=_payload("current_risk_viewed"),
    )

    assert response.status_code == 200
    assert response.json()["requires_database_url"] is False


def test_preview_endpoint_does_not_call_persistence_route_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.api import audit

    def forbidden_connect(_database_url: str) -> object:
        raise AssertionError("preview must not create a database connection")

    def forbidden_write(_connection: object, _event: object) -> object:
        raise AssertionError("preview must not write an audit event")

    monkeypatch.setattr(audit, "connect_with_psycopg", forbidden_connect)
    monkeypatch.setattr(audit, "write_audit_event", forbidden_write)
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/flexsignal_ai")

    response = client.post(
        "/api/audit/preview",
        json=_payload("report_pdf_export_requested"),
    )

    assert response.status_code == 200
    assert response.json()["audit_event_persisted"] is False
