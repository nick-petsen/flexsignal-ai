from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from app.audit.events import AUDIT_EVENT_VERSION
from app.audit.repository import build_audit_event_insert_sql


CONFLICT_BEHAVIOR = "ON CONFLICT (event_id) DO NOTHING"
REQUIRED_SAFETY_FLAGS = (
    "read_only_decision_support",
    "no_automatic_control",
    "no_dispatch",
    "no_activation",
    "no_operational_energy_system_integration",
    "human_review_required",
)


class AuditWriterCursor(Protocol):
    rowcount: int

    def execute(self, sql: str, params: Mapping[str, Any]) -> Any: ...


class AuditWriterConnection(Protocol):
    def cursor(self) -> AuditWriterCursor: ...


def write_audit_event(
    conn: AuditWriterConnection,
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """Write one validated audit-event-v0 through an explicit connection."""
    _validate_writer_boundary(event)
    statement = build_audit_event_insert_sql(event)

    cursor = conn.cursor()
    cursor.execute(statement["sql"], statement["params"])

    return {
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "table": statement["table"],
        "database_write_performed": True,
        "rowcount": cursor.rowcount,
        "conflict_behavior": CONFLICT_BEHAVIOR,
        "safety_boundary_preserved": True,
        "warnings": [],
    }


execute_audit_event_insert = write_audit_event


def _validate_writer_boundary(event: Mapping[str, Any]) -> None:
    if not isinstance(event, Mapping):
        raise TypeError("audit event must be a mapping")

    _require_present(event, "event_version")
    if event["event_version"] != AUDIT_EVENT_VERSION:
        raise ValueError("event_version must be audit-event-v0")

    _require_present(event, "decision_support_only")
    if event["decision_support_only"] is not True:
        raise ValueError("decision_support_only must be true")

    _require_present(event, "event_id")
    _require_present(event, "event_type")
    _require_present(event, "safety_boundary")

    safety_boundary = event["safety_boundary"]
    if not isinstance(safety_boundary, Mapping):
        raise ValueError("safety_boundary must be a mapping")

    for flag_name in REQUIRED_SAFETY_FLAGS:
        if safety_boundary.get(flag_name) is not True:
            raise ValueError(f"safety_boundary.{flag_name} must be true")


def _require_present(event: Mapping[str, Any], field_name: str) -> None:
    if field_name not in event or event[field_name] in (None, ""):
        raise ValueError(f"{field_name} is required")
