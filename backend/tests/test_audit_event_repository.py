from __future__ import annotations

import ast
from datetime import datetime, timezone
import importlib
import json
from pathlib import Path

import pytest

from app.audit import build_audit_event
from app.audit.repository import (
    AUDIT_EVENTS_TABLE,
    build_audit_event_insert_sql,
    execute_audit_event_insert,
)


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


def test_audit_events_migration_exists_with_table_and_indexes() -> None:
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0002_audit_events.py"
    )

    assert migration_path.is_file()

    migration_text = migration_path.read_text(encoding="utf-8")

    assert 'op.create_table(\n        "audit_events"' in migration_text
    assert 'sa.Column("event_id", sa.Text(), primary_key=True)' in migration_text
    assert 'sa.Column("event_version", sa.Text(), nullable=False)' in migration_text
    assert 'sa.Column("event_type", sa.Text(), nullable=False)' in migration_text
    assert 'sa.Column("actor_type", sa.Text(), nullable=False)' in migration_text
    assert 'sa.Column("actor_id", sa.Text(), nullable=True)' in migration_text
    assert 'sa.Column("occurred_at_utc", sa.DateTime(timezone=True), nullable=False)' in migration_text
    assert 'sa.Column("resource_type", sa.Text(), nullable=False)' in migration_text
    assert 'sa.Column("resource_id", sa.Text(), nullable=False)' in migration_text
    assert 'sa.Column("action", sa.Text(), nullable=False)' in migration_text
    assert 'sa.Column("outcome", sa.Text(), nullable=False)' in migration_text
    assert 'sa.Column("decision_support_only", sa.Boolean(), nullable=False)' in migration_text
    assert '"safety_boundary", postgresql.JSONB' in migration_text
    assert '"metadata",' in migration_text
    assert "server_default=sa.text(\"'{}'::jsonb\")" in migration_text
    assert '"created_at_utc"' in migration_text
    assert 'server_default=sa.text("now()")' in migration_text
    assert '"audit_events_occurred_at_utc_idx"' in migration_text
    assert '"audit_events_event_type_idx"' in migration_text
    assert '"audit_events_resource_idx"' in migration_text
    assert '"audit_events_actor_idx"' in migration_text


def test_repository_builds_parameterized_idempotent_insert_sql() -> None:
    event = _event()

    result = build_audit_event_insert_sql(event)

    assert result["table"] == AUDIT_EVENTS_TABLE
    assert result["operation"] == "insert_audit_event_v0"
    assert result["idempotency_key"] == event["event_id"]
    assert result["sql"] == (
        "INSERT INTO audit_events "
        "(event_id, event_version, event_type, actor_type, actor_id, "
        "occurred_at_utc, resource_type, resource_id, action, outcome, "
        "decision_support_only, safety_boundary, metadata) "
        "VALUES (%(event_id)s, %(event_version)s, %(event_type)s, "
        "%(actor_type)s, %(actor_id)s, %(occurred_at_utc)s, "
        "%(resource_type)s, %(resource_id)s, %(action)s, %(outcome)s, "
        "%(decision_support_only)s, %(safety_boundary)s::jsonb, "
        "%(metadata)s::jsonb) "
        "ON CONFLICT (event_id) DO NOTHING"
    )


def test_event_id_is_primary_idempotency_key() -> None:
    event = _event()

    result = build_audit_event_insert_sql(event)

    assert "ON CONFLICT (event_id) DO NOTHING" in result["sql"]
    assert result["params"]["event_id"] == event["event_id"]
    assert result["idempotency_key"] == event["event_id"]


def test_jsonb_fields_are_serialized_as_parameters() -> None:
    event = _event(metadata={"price_area": "DK1", "nested": {"rows": [1, 2]}})

    result = build_audit_event_insert_sql(event)

    assert "%(safety_boundary)s::jsonb" in result["sql"]
    assert "%(metadata)s::jsonb" in result["sql"]
    assert json.loads(result["params"]["safety_boundary"]) == event["safety_boundary"]
    assert json.loads(result["params"]["metadata"]) == event["metadata"]
    assert "price_area" not in result["sql"]
    assert "DK1" not in result["sql"]


@pytest.mark.parametrize(
    "missing_field",
    [
        "event_id",
        "event_version",
        "event_type",
        "actor_type",
        "occurred_at_utc",
        "resource_type",
        "resource_id",
        "action",
        "outcome",
        "decision_support_only",
        "safety_boundary",
        "metadata",
    ],
)
def test_missing_required_fields_are_rejected(missing_field: str) -> None:
    event = _event()
    del event[missing_field]

    with pytest.raises(ValueError, match="Missing required audit event field"):
        build_audit_event_insert_sql(event)


def test_secret_like_metadata_keys_are_rejected_by_builder_and_repository() -> None:
    with pytest.raises(ValueError, match="secret-like metadata key"):
        _event(metadata={"api_key": "not allowed"})

    event = _event()
    event["metadata"] = {"nested": {"access_token": "not allowed"}}
    with pytest.raises(ValueError, match="secret-like metadata key"):
        build_audit_event_insert_sql(event)


def test_repository_import_does_not_require_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    module = importlib.import_module("app.audit.repository")

    assert module.AUDIT_EVENTS_TABLE == "audit_events"


def test_repository_does_not_call_external_apis_or_add_fastapi_routes() -> None:
    source = Path("app/audit/repository.py").read_text(encoding="utf-8")
    forbidden_terms = [
        "Fast" + "API",
        "API" + "Router",
        "reque" + "sts",
        "ht" + "tpx",
        "api.energi" + "dataservice",
        "D" + "MI",
        "report" + "lab",
        "weasy" + "print",
        "sched" + "uler",
        "Az" + "ure",
    ]

    for term in forbidden_terms:
        assert term not in source


def test_no_automatic_persistence_happens_on_import() -> None:
    source = Path("app/audit/repository.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    top_level_calls = [
        node
        for node in tree.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
    ]

    assert top_level_calls == []


def test_repository_preserves_read_only_safety_boundary() -> None:
    event = _event()

    result = build_audit_event_insert_sql(event)
    boundary = json.loads(result["params"]["safety_boundary"])

    assert result["params"]["decision_support_only"] is True
    assert boundary["read_only_decision_support"] is True
    assert boundary["no_automatic_control"] is True
    assert boundary["no_dispatch"] is True
    assert boundary["no_activation"] is True
    assert boundary["no_operational_energy_system_integration"] is True
    assert boundary["human_review_required"] is True


def test_invalid_safety_boundary_is_rejected() -> None:
    event = _event()
    event["safety_boundary"] = {
        **event["safety_boundary"],
        "no_dispatch": False,
    }

    with pytest.raises(ValueError, match="safety_boundary.no_dispatch must be true"):
        build_audit_event_insert_sql(event)


def test_decision_support_only_must_remain_true() -> None:
    event = _event()
    event["decision_support_only"] = False

    with pytest.raises(ValueError, match="decision_support_only must be true"):
        build_audit_event_insert_sql(event)


def test_execute_helper_uses_only_injected_cursor() -> None:
    class FakeCursor:
        def __init__(self) -> None:
            self.calls: list[tuple[str, object]] = []

        def execute(self, sql: str, params: object) -> None:
            self.calls.append((sql, params))

    cursor = FakeCursor()
    event = _event()

    result = execute_audit_event_insert(audit_event=event, cursor=cursor)

    assert result == {
        "statement_count": 1,
        "table": "audit_events",
        "operation": "insert_audit_event_v0",
        "idempotency_key": event["event_id"],
    }
    assert len(cursor.calls) == 1
    sql, params = cursor.calls[0]
    assert "ON CONFLICT (event_id) DO NOTHING" in sql
    assert params["event_id"] == event["event_id"]
