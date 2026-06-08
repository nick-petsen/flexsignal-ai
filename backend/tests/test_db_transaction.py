import pytest

from app.db.transaction import execute_sql_commands_transaction


class RecordingCursor:
    def __init__(self, fail_on_sql: str | None = None) -> None:
        self.fail_on_sql = fail_on_sql
        self.executed: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object]) -> None:
        if sql == self.fail_on_sql:
            raise RuntimeError("execute failed")

        self.executed.append((sql, params))


class RecordingConnection:
    def __init__(self, cursor: RecordingCursor | None = None) -> None:
        self.cursor_obj = cursor or RecordingCursor()
        self.cursor_opened = False
        self.committed = False
        self.rolled_back = False

    def cursor(self) -> RecordingCursor:
        self.cursor_opened = True
        return self.cursor_obj

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_successful_batch_executes_all_commands_and_commits() -> None:
    connection = RecordingConnection()
    commands = [
        _sql_command(
            "INSERT INTO spot_prices VALUES (%(id)s)",
            {"id": 1},
            "spot_prices",
        ),
        _sql_command(
            "INSERT INTO power_balance VALUES (%(id)s)",
            {"id": 2},
            "power_balance",
        ),
    ]

    result = execute_sql_commands_transaction(
        sql_commands=commands,
        connection=connection,
    )

    assert connection.cursor_opened is True
    assert connection.cursor_obj.executed == [
        ("INSERT INTO spot_prices VALUES (%(id)s)", {"id": 1}),
        ("INSERT INTO power_balance VALUES (%(id)s)", {"id": 2}),
    ]
    assert connection.committed is True
    assert connection.rolled_back is False
    assert result == {
        "command_count": 2,
        "executed_count": 2,
        "committed": True,
        "rolled_back": False,
        "tables": ["power_balance", "spot_prices"],
    }


def test_failure_during_execute_rolls_back() -> None:
    cursor = RecordingCursor(fail_on_sql="INSERT INTO power_balance VALUES (%(id)s)")
    connection = RecordingConnection(cursor=cursor)
    commands = [
        _sql_command(
            "INSERT INTO spot_prices VALUES (%(id)s)",
            {"id": 1},
            "spot_prices",
        ),
        _sql_command(
            "INSERT INTO power_balance VALUES (%(id)s)",
            {"id": 2},
            "power_balance",
        ),
    ]

    with pytest.raises(RuntimeError, match="execute failed"):
        execute_sql_commands_transaction(
            sql_commands=commands,
            connection=connection,
        )

    assert cursor.executed == [
        ("INSERT INTO spot_prices VALUES (%(id)s)", {"id": 1}),
    ]
    assert connection.committed is False
    assert connection.rolled_back is True


def test_malformed_command_list_is_rejected_before_any_execute() -> None:
    connection = RecordingConnection()
    commands = [
        _sql_command(
            "INSERT INTO spot_prices VALUES (%(id)s)",
            {"id": 1},
            "spot_prices",
        ),
        {"sql": "INSERT INTO power_balance VALUES (%(id)s)", "table": "power_balance"},
    ]

    with pytest.raises(ValueError, match="Malformed SQL command"):
        execute_sql_commands_transaction(
            sql_commands=commands,
            connection=connection,
        )

    assert connection.cursor_opened is False
    assert connection.cursor_obj.executed == []
    assert connection.committed is False
    assert connection.rolled_back is False


def test_empty_command_list_is_rejected() -> None:
    connection = RecordingConnection()

    with pytest.raises(ValueError, match="must not be empty"):
        execute_sql_commands_transaction(
            sql_commands=[],
            connection=connection,
        )

    assert connection.cursor_opened is False
    assert connection.cursor_obj.executed == []
    assert connection.committed is False
    assert connection.rolled_back is False


def test_database_url_is_not_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    connection = RecordingConnection()

    result = execute_sql_commands_transaction(
        sql_commands=[
            _sql_command(
                "INSERT INTO spot_prices VALUES (%(id)s)",
                {"id": "not-used"},
                "spot_prices",
            ),
        ],
        connection=connection,
    )

    assert result["executed_count"] == 1
    assert connection.committed is True


def _sql_command(
    sql: str,
    params: dict[str, object],
    table: str,
) -> dict[str, object]:
    return {
        "sql": sql,
        "params": params,
        "table": table,
        "operation": "upsert_preview",
    }
