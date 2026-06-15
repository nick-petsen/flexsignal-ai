from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import json
import math
from typing import Any, Protocol

from app.audit.events import AUDIT_EVENT_VERSION, SAFETY_BOUNDARY, SECRET_KEY_MARKERS


AUDIT_EVENTS_TABLE = "audit_events"
AUDIT_EVENT_INSERT_OPERATION = "insert_audit_event_v0"
AUDIT_EVENT_INSERT_COLUMNS = (
    "event_id",
    "event_version",
    "event_type",
    "actor_type",
    "actor_id",
    "occurred_at_utc",
    "resource_type",
    "resource_id",
    "action",
    "outcome",
    "decision_support_only",
    "safety_boundary",
    "metadata",
)
AUDIT_EVENT_REQUIRED_FIELDS = AUDIT_EVENT_INSERT_COLUMNS
AUDIT_EVENT_REQUIRED_TEXT_FIELDS = (
    "event_id",
    "event_version",
    "event_type",
    "actor_type",
    "resource_type",
    "resource_id",
    "action",
    "outcome",
)


class AuditEventCursor(Protocol):
    """Minimal DB-API cursor boundary for explicit audit-event insertion."""

    def execute(self, sql: str, params: Mapping[str, Any]) -> Any: ...


def build_audit_event_insert_sql(
    audit_event: Mapping[str, Any],
) -> dict[str, Any]:
    """Build parameterized PostgreSQL insert SQL for one audit-event-v0.

    This pure helper does not open database connections, read environment
    variables, register API routes, fetch external data, or execute SQL.
    """
    validated_event = _validate_audit_event(audit_event)
    params = {
        column: validated_event[column]
        for column in AUDIT_EVENT_INSERT_COLUMNS
        if column not in {"safety_boundary", "metadata"}
    }
    params["safety_boundary"] = _serialize_jsonb_param(
        validated_event["safety_boundary"],
        field_name="safety_boundary",
    )
    params["metadata"] = _serialize_jsonb_param(
        validated_event["metadata"],
        field_name="metadata",
    )

    return {
        "sql": _build_insert_sql(),
        "params": params,
        "table": AUDIT_EVENTS_TABLE,
        "operation": AUDIT_EVENT_INSERT_OPERATION,
        "idempotency_key": validated_event["event_id"],
    }


def execute_audit_event_insert(
    *,
    audit_event: Mapping[str, Any],
    cursor: AuditEventCursor,
) -> dict[str, Any]:
    """Execute one audit-event insert through a caller-provided cursor only."""
    statement = build_audit_event_insert_sql(audit_event)
    cursor.execute(statement["sql"], statement["params"])
    return {
        "statement_count": 1,
        "table": statement["table"],
        "operation": statement["operation"],
        "idempotency_key": statement["idempotency_key"],
    }


def _build_insert_sql() -> str:
    column_sql = ", ".join(AUDIT_EVENT_INSERT_COLUMNS)
    placeholders = []
    for column in AUDIT_EVENT_INSERT_COLUMNS:
        placeholder = f"%({column})s"
        if column in {"safety_boundary", "metadata"}:
            placeholder = f"{placeholder}::jsonb"
        placeholders.append(placeholder)
    placeholder_sql = ", ".join(placeholders)

    return (
        f"INSERT INTO {AUDIT_EVENTS_TABLE} ({column_sql}) "
        f"VALUES ({placeholder_sql}) "
        "ON CONFLICT (event_id) DO NOTHING"
    )


def _validate_audit_event(audit_event: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(audit_event, Mapping):
        raise TypeError("audit_event must be a mapping")

    for field_name in AUDIT_EVENT_REQUIRED_FIELDS:
        if field_name not in audit_event:
            raise ValueError(f"Missing required audit event field: {field_name}")
        if field_name != "actor_id" and audit_event[field_name] is None:
            raise ValueError(f"Missing required audit event field: {field_name}")

    for field_name in AUDIT_EVENT_REQUIRED_TEXT_FIELDS:
        _validate_required_text(audit_event[field_name], field_name=field_name)

    if audit_event["event_version"] != AUDIT_EVENT_VERSION:
        raise ValueError(f"Unsupported audit event version: {audit_event['event_version']}")

    actor_id = audit_event["actor_id"]
    if actor_id is not None and not isinstance(actor_id, str):
        raise TypeError("actor_id must be a string or None")

    occurred_at_utc = audit_event["occurred_at_utc"]
    if not isinstance(occurred_at_utc, datetime):
        raise TypeError("occurred_at_utc must be a datetime")
    if occurred_at_utc.tzinfo is None or occurred_at_utc.utcoffset() is None:
        raise ValueError("occurred_at_utc must be timezone-aware")

    if audit_event["decision_support_only"] is not True:
        raise ValueError("decision_support_only must be true")

    safety_boundary = audit_event["safety_boundary"]
    if not isinstance(safety_boundary, Mapping):
        raise TypeError("safety_boundary must be a mapping")
    for key, expected_value in SAFETY_BOUNDARY.items():
        if safety_boundary.get(key) is not expected_value:
            raise ValueError(f"safety_boundary.{key} must be true")

    metadata = audit_event["metadata"]
    if not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping")

    return dict(audit_event)


def _validate_required_text(value: Any, *, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _serialize_jsonb_param(value: Mapping[str, Any], *, field_name: str) -> str:
    normalized = _normalize_json_value(value, path=field_name)
    if not isinstance(normalized, dict):
        raise TypeError(f"{field_name} must be a mapping")
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), allow_nan=False)


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
        return [_normalize_json_value(item, path=f"{path}[]") for item in value]

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
