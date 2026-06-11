from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.audit import build_audit_event


OCCURRED_AT = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)


def _event(**overrides: object) -> dict[str, object]:
    fields: dict[str, object] = {
        "event_type": "forecast_preview_requested",
        "actor_type": "local_developer",
        "actor_id": "developer-1",
        "occurred_at_utc": OCCURRED_AT,
        "resource_type": "forecast_preview",
        "resource_id": "DK1-2026-01-01T12:30:00Z",
        "action": "preview_forecast_window",
        "outcome": "success",
        "metadata": {"price_area": "DK1", "window_count": 3},
    }
    fields.update(overrides)
    return build_audit_event(**fields)


def test_valid_audit_event_returns_expected_fields() -> None:
    event = _event()

    assert event["event_id"].startswith("audit_evt_")
    assert event["event_version"] == "audit-event-v0"
    assert event["event_type"] == "forecast_preview_requested"
    assert event["actor_type"] == "local_developer"
    assert event["actor_id"] == "developer-1"
    assert event["occurred_at_utc"] == OCCURRED_AT
    assert event["resource_type"] == "forecast_preview"
    assert event["resource_id"] == "DK1-2026-01-01T12:30:00Z"
    assert event["action"] == "preview_forecast_window"
    assert event["outcome"] == "success"
    assert event["decision_support_only"] is True
    assert event["metadata"] == {"price_area": "DK1", "window_count": 3}


def test_event_id_is_deterministic() -> None:
    first = _event()
    second = _event()

    assert first["event_id"] == second["event_id"]


def test_different_resource_id_changes_event_id() -> None:
    first = _event(resource_id="DK1-forecast-preview")
    second = _event(resource_id="DK2-forecast-preview")

    assert first["event_id"] != second["event_id"]


def test_invalid_event_type_rejected() -> None:
    with pytest.raises(ValueError, match="event_type must be one of"):
        _event(event_type="unknown_event")


def test_invalid_actor_type_rejected() -> None:
    with pytest.raises(ValueError, match="actor_type must be one of"):
        _event(actor_type="automation")


def test_invalid_outcome_rejected() -> None:
    with pytest.raises(ValueError, match="outcome must be one of"):
        _event(outcome="ignored")


def test_timezone_naive_occurred_at_rejected() -> None:
    with pytest.raises(ValueError, match="occurred_at_utc must be timezone-aware"):
        _event(occurred_at_utc=datetime(2026, 1, 1, 12, 30))


@pytest.mark.parametrize(
    ("field_name", "message"),
    [
        ("event_type", "event_type must not be empty"),
        ("resource_type", "resource_type must not be empty"),
        ("resource_id", "resource_id must not be empty"),
        ("action", "action must not be empty"),
    ],
)
def test_empty_required_fields_rejected(field_name: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _event(**{field_name: "  "})


def test_decision_support_only_defaults_to_true() -> None:
    event = build_audit_event(
        event_type="current_risk_viewed",
        actor_type="human_user",
        actor_id=None,
        occurred_at_utc=OCCURRED_AT,
        resource_type="current_risk",
        resource_id="DK1",
        action="view_current_risk",
        outcome="success",
    )

    assert event["decision_support_only"] is True


def test_decision_support_only_must_be_boolean() -> None:
    with pytest.raises(TypeError, match="decision_support_only must be a boolean"):
        _event(decision_support_only="true")


def test_actor_id_must_be_string_or_none() -> None:
    assert _event(actor_id=None)["actor_id"] is None

    with pytest.raises(TypeError, match="actor_id must be a string or None"):
        _event(actor_id=123)


def test_safety_boundary_contains_no_control_dispatch_activation() -> None:
    boundary = _event()["safety_boundary"]

    assert boundary["read_only_decision_support"] is True
    assert boundary["no_automatic_control"] is True
    assert boundary["no_dispatch"] is True
    assert boundary["no_activation"] is True
    assert boundary["no_operational_energy_system_integration"] is True
    assert boundary["human_review_required"] is True


def test_metadata_is_preserved_when_safe() -> None:
    metadata = {
        "price_area": "DK2",
        "nested": {"reason_codes": ["NEGATIVE_PRICE"]},
        "score": 75.5,
        "missing": None,
        "manual_review": True,
    }

    event = _event(metadata=metadata)

    assert event["metadata"] == metadata
    assert event["metadata"] is not metadata


@pytest.mark.parametrize(
    "metadata",
    [
        {"password_hint": "x"},
        {"clientSecret": "x"},
        {"access_token": "x"},
        {"api_key_name": "x"},
        {"public_key": "x"},
        {"credential_reference": "x"},
        {"nested": {"TokenValue": "x"}},
    ],
)
def test_metadata_with_secret_like_keys_is_rejected(
    metadata: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="secret-like metadata key"):
        _event(metadata=metadata)


@pytest.mark.parametrize(
    "metadata",
    [
        {"rows": ("not", "a", "json", "list")},
        {"timestamp": OCCURRED_AT},
        {"bad_number": float("nan")},
        {1: "non-string key"},
    ],
)
def test_metadata_must_be_basic_json_compatible(
    metadata: dict[object, object],
) -> None:
    with pytest.raises((TypeError, ValueError)):
        _event(metadata=metadata)


def test_all_allowed_event_types_can_be_built() -> None:
    for event_type in [
        "forecast_preview_requested",
        "current_risk_viewed",
        "report_summary_built",
        "report_markdown_rendered",
        "report_pdf_exported",
    ]:
        event = _event(event_type=event_type)
        assert event["event_type"] == event_type


def test_module_has_no_forbidden_runtime_or_output_imports() -> None:
    module_source = Path("app/audit/events.py").read_text()
    forbidden_terms = [
        "Fast" + "API",
        "API" + "Router",
        "psyc" + "opg",
        "sql" + "alchemy",
        "SE" + "LECT",
        "INS" + "ERT",
        "UP" + "DATE",
        "DEL" + "ETE",
        "reque" + "sts",
        "ht" + "tpx",
        "api.energi" + "dataservice",
        "D" + "MI",
        "P" + "DF",
        "report" + "lab",
        "weasy" + "print",
        "sched" + "uler",
        "Az" + "ure",
        "builtins",
        "pathlib",
    ]

    for term in forbidden_terms:
        assert term not in module_source
