from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api import energy_freshness_read
from app.main import app


client = TestClient(app)

RAW_DATABASE_URL = "postgresql://user:super-secret-token@localhost/flexsignal_ai"
FORBIDDEN_SQL_OPERATIONS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "CREATE",
    "ALTER",
    "DROP",
    "TRUNCATE",
    "MERGE",
)


class FakeCursor:
    def __init__(self, rows: list[dict[str, Any]]):
        self.rows = rows
        self.executions: list[tuple[str, Mapping[str, Any]]] = []

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def execute(self, sql: str, params: Mapping[str, Any]) -> None:
        self.executions.append((sql, params))

    def fetchone(self) -> dict[str, Any]:
        return self.rows.pop(0)


class FakeConnection:
    def __init__(self, rows: list[dict[str, Any]]):
        self.cursor_instance = FakeCursor(rows)
        self.captured_urls: list[str] = []
        self.closed = False

    def cursor(self) -> FakeCursor:
        return self.cursor_instance

    def close(self) -> None:
        self.closed = True


def freshness_row(
    *,
    price_area: str,
    source_label: str,
    row_count: int,
) -> dict[str, Any]:
    return {
        "price_area": price_area,
        "earliest_timestamp_utc": "2026-01-01T00:00:00Z",
        "latest_timestamp_utc": "2026-01-01T02:00:00Z",
        "row_count": row_count,
        "data_source_label": source_label,
        "warning": None,
    }


def fake_connection(price_area: str) -> FakeConnection:
    return FakeConnection(
        [
            freshness_row(
                price_area=price_area,
                source_label="Energi Data Service:DayAheadPrices",
                row_count=3,
            ),
            freshness_row(
                price_area=price_area,
                source_label="Energi Data Service:ElectricityProdex5MinRealtime",
                row_count=4,
            ),
        ]
    )


def install_fake_connection(
    monkeypatch: pytest.MonkeyPatch,
    price_area: str,
) -> FakeConnection:
    connection = fake_connection(price_area)
    captured_urls: list[str] = []

    def fake_connect(database_url: str) -> FakeConnection:
        captured_urls.append(database_url)
        return connection

    monkeypatch.setenv("DATABASE_URL", RAW_DATABASE_URL)
    monkeypatch.setattr(energy_freshness_read, "connect_with_psycopg", fake_connect)
    connection.captured_urls = captured_urls
    return connection


def test_endpoint_exists() -> None:
    assert any(
        getattr(route, "path", None) == "/api/energy/freshness/read"
        for route in app.routes
    )


@pytest.mark.parametrize("price_area", ["DK1", "DK2"])
def test_supported_price_area_returns_db_backed_read(
    monkeypatch: pytest.MonkeyPatch,
    price_area: str,
) -> None:
    connection = install_fake_connection(monkeypatch, price_area)

    response = client.get(f"/api/energy/freshness/read?price_area={price_area}")

    assert response.status_code == 200
    body = response.json()
    assert body["price_area"] == price_area
    assert body["dry_run"] is False
    assert body["database_query_executed"] is True
    assert body["database_write_performed"] is False
    assert body["requires_database_url"] is True
    assert body["freshness_result"]["price_area"] == price_area
    assert body["spot_price_freshness"]["row_count"] == 3
    assert body["power_balance_freshness"]["row_count"] == 4
    assert body["safety_boundary"] == dict(energy_freshness_read.SAFETY_BOUNDARY)
    assert len(connection.cursor_instance.executions) == 2
    assert connection.closed is True
    assert connection.captured_urls == [RAW_DATABASE_URL]


def test_invalid_price_area_returns_400(monkeypatch: pytest.MonkeyPatch) -> None:
    connect_calls = 0

    def fake_connect(database_url: str) -> FakeConnection:
        nonlocal connect_calls
        connect_calls += 1
        return fake_connection("DK1")

    monkeypatch.setenv("DATABASE_URL", RAW_DATABASE_URL)
    monkeypatch.setattr(energy_freshness_read, "connect_with_psycopg", fake_connect)

    response = client.get("/api/energy/freshness/read?price_area=SE3")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported price_area"
    assert connect_calls == 0


def test_missing_database_url_at_request_time_returns_safe_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect_calls = 0

    def fake_connect(database_url: str) -> FakeConnection:
        nonlocal connect_calls
        connect_calls += 1
        return fake_connection("DK1")

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(energy_freshness_read, "connect_with_psycopg", fake_connect)

    response = client.get("/api/energy/freshness/read?price_area=DK1")

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["requires_database_url"] is True
    assert detail["database_query_executed"] is False
    assert detail["database_write_performed"] is False
    assert "required at request time" in detail["warning"]
    assert connect_calls == 0


def test_app_import_without_database_url_still_exposes_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)

    assert any(
        getattr(route, "path", None) == "/api/energy/freshness/read"
        for route in reloaded_main.app.routes
    )


def test_response_contains_no_raw_database_url_or_secret_markers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_connection(monkeypatch, "DK1")

    response = client.get("/api/energy/freshness/read?price_area=DK1")

    assert response.status_code == 200
    rendered = repr(response.json())
    assert RAW_DATABASE_URL not in rendered
    assert "super-secret-token" not in rendered
    assert "token" not in rendered.lower()


def test_no_put_patch_delete_or_post_route_is_added_for_endpoint() -> None:
    route_methods = {
        method
        for route in app.routes
        if getattr(route, "path", None) == "/api/energy/freshness/read"
        for method in getattr(route, "methods", set())
    }

    assert route_methods == {"GET"}
    assert not route_methods & {"POST", "PUT", "PATCH", "DELETE"}


def test_no_mutating_database_behavior_is_added(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = install_fake_connection(monkeypatch, "DK2")

    response = client.get("/api/energy/freshness/read?price_area=DK2")

    assert response.status_code == 200
    assert len(connection.cursor_instance.executions) == 2
    for sql, _params in connection.cursor_instance.executions:
        assert sql.startswith("SELECT")
        for operation in FORBIDDEN_SQL_OPERATIONS:
            assert operation not in sql.upper()
