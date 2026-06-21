import ast
from pathlib import Path
from typing import Any

import pytest

import app.db.repositories.energy_freshness_reader as reader
from app.db.repositories.energy_freshness_reader import (
    SAFETY_BOUNDARY,
    read_energy_freshness_summary,
    read_power_balance_freshness,
    read_spot_price_freshness,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "db"
    / "repositories"
    / "energy_freshness_reader.py"
)
MODULE_SOURCE = MODULE_PATH.read_text(encoding="utf-8")
FORBIDDEN_SQL_OPERATIONS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "UPSERT",
    "CREATE",
    "ALTER",
    "DROP",
    "TRUNCATE",
    "MERGE",
)


class FakeCursor:
    def __init__(self, rows: list[dict[str, Any]], *, context_manager: bool = True):
        self.rows = rows
        self.context_manager = context_manager
        self.executions: list[tuple[str, dict[str, Any]]] = []
        self.entered = False
        self.closed = False

    def __enter__(self) -> "FakeCursor":
        if not self.context_manager:
            raise AssertionError("Context manager should not be used")
        self.entered = True
        return self

    def __exit__(self, *_args: Any) -> None:
        self.closed = True

    def execute(self, sql: str, params: dict[str, Any]) -> None:
        self.executions.append((sql, params))

    def fetchone(self) -> dict[str, Any] | None:
        if not self.rows:
            return None
        return self.rows.pop(0)


class PlainFakeCursor:
    def __init__(self, rows: list[dict[str, Any]]):
        self.rows = rows
        self.executions: list[tuple[str, dict[str, Any]]] = []
        self.closed = False

    def execute(self, sql: str, params: dict[str, Any]) -> None:
        self.executions.append((sql, params))

    def fetchone(self) -> dict[str, Any] | None:
        if not self.rows:
            return None
        return self.rows.pop(0)

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, cursor: FakeCursor | PlainFakeCursor):
        self.cursor_instance = cursor
        self.cursor_calls = 0

    def cursor(self) -> FakeCursor | PlainFakeCursor:
        self.cursor_calls += 1
        return self.cursor_instance


def freshness_row(
    *,
    price_area: str = "DK1",
    source_label: str = "Energi Data Service:DayAheadPrices",
    row_count: int = 3,
    warning: str | None = None,
) -> dict[str, Any]:
    return {
        "price_area": price_area,
        "earliest_timestamp_utc": "2026-01-01T00:00:00Z",
        "latest_timestamp_utc": "2026-01-01T02:00:00Z",
        "row_count": row_count,
        "data_source_label": source_label,
        "warning": warning,
    }


@pytest.mark.parametrize("price_area", ["DK1", "DK2"])
@pytest.mark.parametrize(
    "read_func",
    [read_spot_price_freshness, read_power_balance_freshness],
)
def test_dk1_and_dk2_are_accepted(read_func: Any, price_area: str) -> None:
    conn = FakeConnection(FakeCursor([freshness_row(price_area=price_area)]))

    result = read_func(conn, price_area)

    assert result["price_area"] == price_area
    assert conn.cursor_calls == 1


def test_summary_accepts_dk1_and_dk2() -> None:
    for price_area in ("DK1", "DK2"):
        conn = FakeConnection(
            FakeCursor(
                [
                    freshness_row(price_area=price_area),
                    freshness_row(
                        price_area=price_area,
                        source_label=(
                            "Energi Data Service:ElectricityProdex5MinRealtime"
                        ),
                    ),
                ]
            )
        )

        result = read_energy_freshness_summary(conn, price_area)

        assert result["price_area"] == price_area
        assert conn.cursor_calls == 2


@pytest.mark.parametrize(
    "read_func",
    [
        read_spot_price_freshness,
        read_power_balance_freshness,
        read_energy_freshness_summary,
    ],
)
def test_invalid_price_area_is_rejected_before_execution(read_func: Any) -> None:
    cursor = FakeCursor([freshness_row()])
    conn = FakeConnection(cursor)

    with pytest.raises(ValueError, match="Unsupported energy freshness price area"):
        read_func(conn, "SE3")

    assert conn.cursor_calls == 0
    assert cursor.executions == []


def test_valid_spot_price_freshness_executes_exactly_one_select_query() -> None:
    cursor = FakeCursor([freshness_row()])
    conn = FakeConnection(cursor)

    result = read_spot_price_freshness(conn, "DK1")

    assert len(cursor.executions) == 1
    sql, params = cursor.executions[0]
    assert sql.startswith("SELECT")
    assert params["price_area"] == "DK1"
    assert result["source_label"] == "Energi Data Service:DayAheadPrices"


def test_valid_power_balance_freshness_executes_exactly_one_select_query() -> None:
    cursor = FakeCursor(
        [
            freshness_row(
                price_area="DK2",
                source_label="Energi Data Service:ElectricityProdex5MinRealtime",
            )
        ]
    )
    conn = FakeConnection(cursor)

    result = read_power_balance_freshness(conn, "DK2")

    assert len(cursor.executions) == 1
    sql, params = cursor.executions[0]
    assert sql.startswith("SELECT")
    assert params["price_area"] == "DK2"
    assert result["source_label"] == (
        "Energi Data Service:ElectricityProdex5MinRealtime"
    )


def test_plain_cursor_pattern_is_supported_and_closed() -> None:
    cursor = PlainFakeCursor([freshness_row()])
    conn = FakeConnection(cursor)

    result = read_spot_price_freshness(conn, "DK1")

    assert result["row_count"] == 3
    assert cursor.closed is True


def test_summary_executes_spot_and_power_balance_reads() -> None:
    cursor = FakeCursor(
        [
            freshness_row(source_label="Energi Data Service:DayAheadPrices"),
            freshness_row(
                source_label="Energi Data Service:ElectricityProdex5MinRealtime"
            ),
        ]
    )
    conn = FakeConnection(cursor)

    result = read_energy_freshness_summary(conn, "DK1")

    assert conn.cursor_calls == 2
    assert len(cursor.executions) == 2
    assert result["database_query_executed"] is True
    assert result["database_write_performed"] is False
    assert result["spot_price_freshness"]["source_label"] == (
        "Energi Data Service:DayAheadPrices"
    )
    assert result["power_balance_freshness"]["source_label"] == (
        "Energi Data Service:ElectricityProdex5MinRealtime"
    )


def test_returned_results_include_timestamps_and_row_count() -> None:
    conn = FakeConnection(FakeCursor([freshness_row(row_count=12)]))

    result = read_spot_price_freshness(conn, "DK1")

    assert result["earliest_timestamp"] == "2026-01-01T00:00:00Z"
    assert result["latest_timestamp"] == "2026-01-01T02:00:00Z"
    assert result["row_count"] == 12


def test_empty_result_creates_warning() -> None:
    conn = FakeConnection(
        FakeCursor(
            [
                {
                    "price_area": "DK1",
                    "earliest_timestamp_utc": None,
                    "latest_timestamp_utc": None,
                    "row_count": 0,
                    "data_source_label": "Energi Data Service:DayAheadPrices",
                    "warning": None,
                }
            ]
        )
    )

    result = read_spot_price_freshness(conn, "DK1")

    assert result["row_count"] == 0
    assert result["warning"] == "No spot price rows are available for this price area."


def test_database_write_performed_is_false() -> None:
    conn = FakeConnection(FakeCursor([freshness_row()]))

    result = read_spot_price_freshness(conn, "DK1")

    assert result["database_write_performed"] is False


def test_safety_boundary_is_preserved() -> None:
    conn = FakeConnection(FakeCursor([freshness_row()]))

    result = read_spot_price_freshness(conn, "DK1")

    assert result["safety_boundary"] == SAFETY_BOUNDARY


def test_summary_collects_warnings() -> None:
    cursor = FakeCursor(
        [
            freshness_row(row_count=0, warning="No spot price rows."),
            freshness_row(row_count=0, warning="No power balance rows."),
        ]
    )
    conn = FakeConnection(cursor)

    result = read_energy_freshness_summary(conn, "DK1")

    assert result["warnings"] == ["No spot price rows.", "No power balance rows."]


def test_unsafe_sql_is_rejected_before_execution(monkeypatch: Any) -> None:
    unsafe_plan = {
        "operation": "select",
        "part": "spot_price",
        "price_area": "DK1",
        "sql": "SELECT * FROM spot_prices; DROP TABLE spot_prices",
        "params": {
            "price_area": "DK1",
            "source_label": "Energi Data Service:DayAheadPrices",
            "empty_warning": "No spot price rows are available for this price area.",
        },
        "expected_result_fields": (),
    }
    monkeypatch.setattr(
        reader,
        "build_spot_price_freshness_query",
        lambda _: unsafe_plan,
    )
    cursor = FakeCursor([freshness_row()])
    conn = FakeConnection(cursor)

    with pytest.raises(ValueError, match="rejected unsafe SQL"):
        read_spot_price_freshness(conn, "DK1")

    assert conn.cursor_calls == 0
    assert cursor.executions == []


def test_non_parameterized_sql_is_rejected_before_execution(monkeypatch: Any) -> None:
    unsafe_plan = {
        "operation": "select",
        "part": "spot_price",
        "price_area": "DK1",
        "sql": "SELECT 'DK1' AS price_area",
        "params": {"price_area": "DK1"},
        "expected_result_fields": (),
    }
    monkeypatch.setattr(
        reader,
        "build_spot_price_freshness_query",
        lambda _: unsafe_plan,
    )
    cursor = FakeCursor([freshness_row()])
    conn = FakeConnection(cursor)

    with pytest.raises(ValueError, match="requires parameterized SQL"):
        read_spot_price_freshness(conn, "DK1")

    assert conn.cursor_calls == 0
    assert cursor.executions == []


def test_reader_does_not_read_database_url() -> None:
    assert "DATA" + "BASE_URL" not in MODULE_SOURCE
    assert "os.environ" not in MODULE_SOURCE
    assert "getenv" not in MODULE_SOURCE


def test_reader_does_not_import_fastapi_or_apirouter() -> None:
    tree = ast.parse(MODULE_SOURCE)
    imported_modules = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert "fastapi" not in imported_modules
    assert "FastAPI" not in MODULE_SOURCE
    assert "APIRouter" not in MODULE_SOURCE


def test_reader_does_not_call_energi_data_service_or_dmi() -> None:
    assert "api.energidataservice" not in MODULE_SOURCE
    assert "DMI" not in MODULE_SOURCE
    assert "requests." not in MODULE_SOURCE
    assert "httpx." not in MODULE_SOURCE


def test_reader_contains_no_mutating_sql_execution_behavior() -> None:
    tree = ast.parse(MODULE_SOURCE)
    call_names = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert "commit" not in call_names
    assert "rollback" not in call_names
    assert "connect" not in MODULE_SOURCE
    for operation in FORBIDDEN_SQL_OPERATIONS:
        assert operation in reader.MUTATING_SQL_TOKENS


def test_query_parts_match_existing_plan_builders() -> None:
    assert reader.SPOT_PRICE_FRESHNESS_PART == "spot_price"
    assert reader.POWER_BALANCE_FRESHNESS_PART == "power_balance"
