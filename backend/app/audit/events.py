from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any

AUDIT_EVENT_VERSION = "audit-event-v0"

ALLOWED_EVENT_TYPES = frozenset(
    {
        "forecast_preview_requested",
        "current_risk_viewed",
        "report_summary_built",
        "report_markdown_rendered",
        "report_pdf_exported",
    }
)

ALLOWED_ACTOR_TYPES = frozenset(
    {
        "human_user",
        "local_developer",
        "local_user",
        "system_test",
    }
)

ALLOWED_OUTCOMES = frozenset(
    {
        "success",
        "validation_error",
        "refused",
        "failed",
    }
)

SAFETY_BOUNDARY = {
    "read_only_decision_support": True,
    "no_automatic_control": True,
    "no_dispatch": True,
    "no_activation": True,
    "no_operational_energy_system_integration": True,
    "human_review_required": True,
}

SECRET_KEY_MARKERS = (
    "password",
    "secret",
    "token",
    "api_key",
    "key",
    "credential",
)


def build_audit_event(
    *,
    event_type: str,
    actor_type: str,
    occurred_at_utc: datetime,
    resource_type: str,
    resource_id: str,
    action: str,
    outcome: str,
    actor_id: str | None = None,
    decision_support_only: bool = True,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic read-only decision-support audit event."""
    _validate_allowed_value(
        event_type,
        field_name="event_type",
        allowed_values=ALLOWED_EVENT_TYPES,
    )
    _validate_allowed_value(
        actor_type,
        field_name="actor_type",
        allowed_values=ALLOWED_ACTOR_TYPES,
    )
    _validate_allowed_value(
        outcome,
        field_name="outcome",
        allowed_values=ALLOWED_OUTCOMES,
    )
    _validate_required_text(resource_type, field_name="resource_type")
    _validate_required_text(resource_id, field_name="resource_id")
    _validate_required_text(action, field_name="action")
    if actor_id is not None and not isinstance(actor_id, str):
        raise TypeError("actor_id must be a string or None")
    if not isinstance(decision_support_only, bool):
        raise TypeError("decision_support_only must be a boolean")

    occurred_at = _ensure_aware_datetime(
        occurred_at_utc,
        field_name="occurred_at_utc",
    )
    safe_metadata = _normalize_metadata(metadata)

    event = {
        "event_id": _build_event_id(
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            occurred_at_utc=occurred_at,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
        ),
        "event_version": AUDIT_EVENT_VERSION,
        "event_type": event_type,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "occurred_at_utc": occurred_at,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "action": action,
        "outcome": outcome,
        "decision_support_only": decision_support_only,
        "safety_boundary": dict(SAFETY_BOUNDARY),
        "metadata": safe_metadata,
    }
    return event


def _validate_allowed_value(
    value: str,
    *,
    field_name: str,
    allowed_values: frozenset[str],
) -> None:
    _validate_required_text(value, field_name=field_name)
    if value not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise ValueError(f"{field_name} must be one of: {allowed}")


def _validate_required_text(value: str, *, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _ensure_aware_datetime(value: datetime, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _normalize_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}
    if not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping")

    normalized = _normalize_json_value(metadata, path="metadata")
    if not isinstance(normalized, dict):
        raise TypeError("metadata must be a mapping")
    return normalized


def _normalize_json_value(value: Any, *, path: str) -> Any:
    if isinstance(value, Mapping):
        normalized_dict: dict[str, Any] = {}
        for key, nested_value in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} keys must be strings")
            _reject_secret_like_key(key, path=path)
            normalized_dict[key] = _normalize_json_value(
                nested_value,
                path=f"{path}.{key}",
            )
        return normalized_dict

    if isinstance(value, list):
        return [
            _normalize_json_value(item, path=f"{path}[]")
            for item in value
        ]

    if isinstance(value, tuple):
        raise TypeError(f"{path} must use JSON-compatible list values")

    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value

    if isinstance(value, int) and not isinstance(value, bool):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} must be a finite number")
        return value

    raise TypeError(f"{path} must be JSON-compatible")


def _reject_secret_like_key(key: str, *, path: str) -> None:
    normalized_key = key.lower()
    for marker in SECRET_KEY_MARKERS:
        if marker in normalized_key:
            raise ValueError(f"{path} contains a secret-like metadata key")


def _format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_event_id(
    *,
    event_type: str,
    actor_type: str,
    actor_id: str | None,
    occurred_at_utc: datetime,
    resource_type: str,
    resource_id: str,
    action: str,
    outcome: str,
) -> str:
    stable_payload = {
        "event_version": AUDIT_EVENT_VERSION,
        "event_type": event_type,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "occurred_at_utc": _format_utc_timestamp(occurred_at_utc),
        "resource_type": resource_type,
        "resource_id": resource_id,
        "action": action,
        "outcome": outcome,
    }
    stable_key = json.dumps(
        stable_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = sha256(stable_key.encode("utf-8")).hexdigest()[:24]
    return f"audit_evt_{digest}"
