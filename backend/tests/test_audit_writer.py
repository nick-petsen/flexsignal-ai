from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from app.audit import build_audit_event
from app.audit.writer import CONFLICT_BEHAVIOR, write_audit_event


WRITER_PATH = Path("app/audit/writer.py")
OCCURRED_AT = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)


class FakeCursor:
    def __init__(self, rowcount: int = 1) -> None:
        self.rowcount = rowcount
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, sql: str, params: dict[str, Any]) -> None:
        self.calls.append((sql, params))


class FakeConnection:
    def __init__(self, cursor: FakeCursor | None = None) -> None:
        self.cursor_obj = cursor or FakeCursor()
        self.cursor_calls = 0

    def cursor(self) -> FakeCursor:
        self.cursor_calls += 1
        return self.cursor_obj


def _event(**overrides: object) -> dict[str, Any]:
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


def test_valid_event_executes_one_parameterized_insert() -> None:
    conn = FakeConnection()
    event = _event()

    result = write_audit_event(conn, event)

    assert conn.cursor_calls == 1
    assert len(conn.cursor_obj.calls) == 1
    sql, params = conn.cursor_obj.calls[0]
    assert sql.startswith("INSERT INTO audit_events")
    assert "%(event_id)s" in sql
    assert "ON CONFLICT (event_id) DO NOTHING" in sql
    assert event["event_id"] not in sql
    assert params["event_id"] == event["event_id"]
    assert result["database_write_performed"] is True


def test_invalid_event_version_raises_and_executes_nothing() -> None:
    conn = FakeConnection()
    event = _event()
    event["event_version"] = "audit-event-v1"

    with pytest.raises(ValueError, match="event_version must be audit-event-v0"):
        write_audit_event(conn, event)

    assert conn.cursor_calls == 0
    assert conn.cursor_obj.calls == []


def test_missing_event_id_raises_and_executes_nothing() -> None:
    conn = FakeConnection()
    event = _event()
    del event["event_id"]

    with pytest.raises(ValueError, match="event_id is required"):
        write_audit_event(conn, event)

    assert conn.cursor_calls == 0
    assert conn.cursor_obj.calls == []


def test_decision_support_only_false_raises_and_executes_nothing() -> None:
    conn = FakeConnection()
    event = _event()
    event["decision_support_only"] = False

    with pytest.raises(ValueError, match="decision_support_only must be true"):
        write_audit_event(conn, event)

    assert conn.cursor_calls == 0
    assert conn.cursor_obj.calls == []


@pytest.mark.parametrize(
    "bad_boundary",
    [
        None,
        {},
        {"read_only_decision_support": False},
        {
            "read_only_decision_support": True,
            "no_automatic_control": False,
            "no_dispatch": True,
            "no_activation": True,
            "no_operational_energy_system_integration": True,
            "human_review_required": True,
        },
        {
            "read_only_decision_support": True,
            "no_automatic_control": True,
            "no_dispatch": False,
            "no_activation": True,
            "no_operational_energy_system_integration": True,
            "human_review_required": True,
        },
        {
            "read_only_decision_support": True,
            "no_automatic_control": True,
            "no_dispatch": True,
            "no_activation": False,
            "no_operational_energy_system_integration": True,
            "human_review_required": True,
        },
    ],
)
def test_missing_or_unsafe_safety_boundary_raises_and_executes_nothing(
    bad_boundary: object,
) -> None:
    conn = FakeConnection()
    event = _event()
    if bad_boundary is None:
        del event["safety_boundary"]
    else:
        event["safety_boundary"] = bad_boundary

    with pytest.raises(ValueError):
        write_audit_event(conn, event)

    assert conn.cursor_calls == 0
    assert conn.cursor_obj.calls == []


def test_returned_result_includes_rowcount_and_conflict_behavior() -> None:
    cursor = FakeCursor(rowcount=0)
    conn = FakeConnection(cursor)
    event = _event()

    result = write_audit_event(conn, event)

    assert result == {
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "table": "audit_events",
        "database_write_performed": True,
        "rowcount": 0,
        "conflict_behavior": CONFLICT_BEHAVIOR,
        "safety_boundary_preserved": True,
        "warnings": [],
    }


def test_writer_does_not_read_database_url() -> None:
    source = WRITER_PATH.read_text(encoding="utf-8")

    assert "DATABASE_URL" not in source
    assert "getenv" not in source
    assert "environ" not in source


def test_writer_does_not_import_fastapi_or_router() -> None:
    source = WRITER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_names = {
        alias.name
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert "fastapi" not in imported_names
    assert "FastAPI" not in source
    assert "APIRouter" not in source


def test_writer_does_not_add_operational_behavior() -> None:
    source = WRITER_PATH.read_text(encoding="utf-8")
    forbidden_terms = [
        "send_" + "control",
        "live_" + "control",
        "dispatch_" + "asset",
        "activate_" + "asset",
        "command_" + "device",
        "setpoint",
    ]

    for term in forbidden_terms:
        assert term not in source
