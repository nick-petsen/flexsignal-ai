from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol


class DbTransactionCursor(Protocol):
    """Minimal cursor boundary for generated SQL command execution."""

    def execute(self, sql: str, params: Mapping[str, Any]) -> Any: ...


class DbTransactionConnection(Protocol):
    """Minimal injected connection boundary for explicit transaction tests."""

    def cursor(self) -> DbTransactionCursor: ...
    def commit(self) -> Any: ...
    def rollback(self) -> Any: ...


def execute_sql_commands_transaction(
    sql_commands: Iterable[Mapping[str, Any]],
    connection: DbTransactionConnection,
) -> dict[str, Any]:
    """Execute generated SQL command dictionaries inside an injected transaction.

    This helper is intentionally limited to caller-provided connection objects.
    It does not create database connections, read environment variables, require
    PostgreSQL, schedule ingestion, or attach to FastAPI startup.
    """
    commands = [_validate_sql_command(command) for command in sql_commands]
    if not commands:
        raise ValueError("SQL command list must not be empty")

    cursor = connection.cursor()
    executed_count = 0
    try:
        for command in commands:
            cursor.execute(command["sql"], command["params"])
            executed_count += 1
    except Exception:
        connection.rollback()
        raise

    connection.commit()
    return {
        "command_count": len(commands),
        "executed_count": executed_count,
        "committed": True,
        "rolled_back": False,
        "tables": sorted({command["table"] for command in commands}),
    }


def _validate_sql_command(command: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(command, Mapping):
        raise ValueError("Malformed SQL command")

    sql = command.get("sql")
    params = command.get("params")
    table = command.get("table")

    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("Malformed SQL command: missing sql")

    if not isinstance(params, Mapping):
        raise ValueError("Malformed SQL command: missing params")

    if not isinstance(table, str) or not table.strip():
        raise ValueError("Malformed SQL command: missing table")

    return {
        "sql": sql,
        "params": params,
        "table": table,
    }
