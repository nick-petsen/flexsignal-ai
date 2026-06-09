import re
from collections.abc import Mapping
from typing import Any

import pytest

from app.db.read_queries import (
    build_power_balance_time_window_query,
    build_recent_power_balance_query,
    build_recent_spot_prices_query,
    build_spot_prices_time_window_query,
)


FORBIDDEN_SQL_OPERATIONS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "UPSERT",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
)


def test_recent_spot_prices_query_for_dk1_uses_params_and_default_limit() -> None:
    result = build_recent_spot_prices_query(price_area="DK1")

    assert result == {
        "sql": (
            "SELECT id, price_area, timestamp_utc, price_eur_per_mwh, "
            "price_dkk_per_mwh, source, source_record_id, ingested_at_utc "
            "FROM spot_prices "
            "WHERE price_area = %(price_area)s "
            "ORDER BY timestamp_utc DESC "
            "LIMIT %(limit)s"
        ),
        "params": {
            "price_area": "DK1",
            "limit": 100,
        },
        "table": "spot_prices",
        "operation": "select",
    }


def test_recent_power_balance_query_for_dk2_uses_params() -> None:
    result = build_recent_power_balance_query(price_area="DK2", limit=25)

    assert result["table"] == "power_balance"
    assert result["operation"] == "select"
    assert result["params"] == {
        "price_area": "DK2",
        "limit": 25,
    }
    assert result["sql"] == (
        "SELECT id, price_area, timestamp_utc, production_mw, consumption_mw, "
        "wind_onshore_mw, wind_offshore_mw, solar_mw, exchange_net_mw, "
        "source, source_record_id, ingested_at_utc "
        "FROM power_balance "
        "WHERE price_area = %(price_area)s "
        "ORDER BY timestamp_utc DESC "
        "LIMIT %(limit)s"
    )


def test_spot_prices_time_window_query_for_dk1_uses_params() -> None:
    result = build_spot_prices_time_window_query(
        price_area="DK1",
        start_utc="2026-01-01T00:00:00Z",
        end_utc="2026-01-02T00:00:00Z",
        limit=48,
    )

    assert result["table"] == "spot_prices"
    assert result["operation"] == "select"
    assert result["params"] == {
        "price_area": "DK1",
        "start_utc": "2026-01-01T00:00:00Z",
        "end_utc": "2026-01-02T00:00:00Z",
        "limit": 48,
    }
    assert result["sql"] == (
        "SELECT id, price_area, timestamp_utc, price_eur_per_mwh, "
        "price_dkk_per_mwh, source, source_record_id, ingested_at_utc "
        "FROM spot_prices "
        "WHERE price_area = %(price_area)s "
        "AND timestamp_utc >= %(start_utc)s "
        "AND timestamp_utc < %(end_utc)s "
        "ORDER BY timestamp_utc ASC "
        "LIMIT %(limit)s"
    )


def test_power_balance_time_window_query_for_dk2_uses_params() -> None:
    result = build_power_balance_time_window_query(
        price_area="DK2",
        start_utc="2026-01-01T00:00:00Z",
        end_utc="2026-01-02T00:00:00Z",
        limit=288,
    )

    assert result["table"] == "power_balance"
    assert result["operation"] == "select"
    assert result["params"] == {
        "price_area": "DK2",
        "start_utc": "2026-01-01T00:00:00Z",
        "end_utc": "2026-01-02T00:00:00Z",
        "limit": 288,
    }
    assert "FROM power_balance" in result["sql"]
    assert "timestamp_utc >= %(start_utc)s" in result["sql"]
    assert "timestamp_utc < %(end_utc)s" in result["sql"]


@pytest.mark.parametrize(
    "builder,kwargs",
    [
        (build_recent_spot_prices_query, {}),
        (build_recent_power_balance_query, {}),
        (
            build_spot_prices_time_window_query,
            {
                "start_utc": "2026-01-01T00:00:00Z",
                "end_utc": "2026-01-02T00:00:00Z",
            },
        ),
        (
            build_power_balance_time_window_query,
            {
                "start_utc": "2026-01-01T00:00:00Z",
                "end_utc": "2026-01-02T00:00:00Z",
            },
        ),
    ],
)
def test_unsupported_price_area_is_rejected(builder: Any, kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="Unsupported read query price area"):
        builder(price_area="SE3", **kwargs)


@pytest.mark.parametrize("limit", [0, -1, 1.5, "100", True])
def test_invalid_limits_are_rejected(limit: Any) -> None:
    with pytest.raises(ValueError, match="Read query limit"):
        build_recent_spot_prices_query(price_area="DK1", limit=limit)


def test_hard_max_limit_is_enforced() -> None:
    result = build_recent_power_balance_query(price_area="DK2", limit=1000)

    assert result["params"]["limit"] == 1000

    with pytest.raises(ValueError, match="<= 1000"):
        build_recent_power_balance_query(price_area="DK2", limit=1001)


def test_time_window_bounds_are_required() -> None:
    with pytest.raises(ValueError, match="start_utc is required"):
        build_spot_prices_time_window_query(
            price_area="DK1",
            start_utc=None,
            end_utc="2026-01-02T00:00:00Z",
        )

    with pytest.raises(ValueError, match="end_utc is required"):
        build_power_balance_time_window_query(
            price_area="DK2",
            start_utc="2026-01-01T00:00:00Z",
            end_utc=None,
        )


@pytest.mark.parametrize(
    "query",
    [
        build_recent_spot_prices_query(price_area="DK1"),
        build_recent_power_balance_query(price_area="DK2"),
        build_spot_prices_time_window_query(
            price_area="DK1",
            start_utc="2026-01-01T00:00:00Z",
            end_utc="2026-01-02T00:00:00Z",
        ),
        build_power_balance_time_window_query(
            price_area="DK2",
            start_utc="2026-01-01T00:00:00Z",
            end_utc="2026-01-02T00:00:00Z",
        ),
    ],
)
def test_generated_sql_is_read_only(query: Mapping[str, Any]) -> None:
    sql = query["sql"]

    assert query["operation"] == "select"
    assert re.match(r"^SELECT\b", sql)
    for operation in FORBIDDEN_SQL_OPERATIONS:
        assert not re.search(rf"\b{operation}\b", sql, flags=re.IGNORECASE)


def test_params_are_separated_from_sql() -> None:
    query = build_spot_prices_time_window_query(
        price_area="DK1",
        start_utc="2026-01-01T00:00:00Z",
        end_utc="2026-01-02T00:00:00Z",
        limit=48,
    )

    assert "%(price_area)s" in query["sql"]
    assert "%(start_utc)s" in query["sql"]
    assert "%(end_utc)s" in query["sql"]
    assert "%(limit)s" in query["sql"]
    assert "DK1" not in query["sql"]
    assert "2026-01-01T00:00:00Z" not in query["sql"]
    assert "2026-01-02T00:00:00Z" not in query["sql"]
    assert "48" not in query["sql"]
    assert query["params"] == {
        "price_area": "DK1",
        "start_utc": "2026-01-01T00:00:00Z",
        "end_utc": "2026-01-02T00:00:00Z",
        "limit": 48,
    }
