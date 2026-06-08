from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from app.db.sql_builder import build_eds_write_plan_entry_upsert_sql


class DbCursor(Protocol):
    """Minimal DB-API cursor boundary required for manual write execution."""

    def execute(self, sql: str, params: Mapping[str, Any]) -> Any: ...


@dataclass(frozen=True)
class EdsWriteExecutionSummary:
    """Summary of statements submitted through the caller-provided cursor."""

    statement_count: int
    table_counts: dict[str, int]


def execute_eds_write_plan(
    *,
    write_plan: Iterable[Mapping[str, Any]],
    cursor: DbCursor,
) -> EdsWriteExecutionSummary:
    """Execute supported EDS write-plan entries through an injected cursor.

    This boundary does not create database connections, read environment
    variables, commit transactions, run migrations, schedule ingestion, or
    connect to FastAPI startup. Transaction handling remains the caller's
    responsibility.
    """
    statements = [
        build_eds_write_plan_entry_upsert_sql(write_plan_entry)
        for write_plan_entry in write_plan
    ]

    table_counts: Counter[str] = Counter()
    for statement in statements:
        cursor.execute(statement["sql"], statement["params"])
        table_counts[statement["table"]] += 1

    return EdsWriteExecutionSummary(
        statement_count=len(statements),
        table_counts=dict(table_counts),
    )
