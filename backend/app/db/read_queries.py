from __future__ import annotations

from typing import Any

from app.db.repositories.eds_records import (
    POWER_BALANCE_TABLE,
    SPOT_PRICES_TABLE,
    SUPPORTED_PRICE_AREAS,
)


SELECT_OPERATION = "select"
DEFAULT_READ_LIMIT = 100
MAX_READ_LIMIT = 1000

SPOT_PRICE_SELECT_COLUMNS = (
    "id",
    "price_area",
    "timestamp_utc",
    "price_eur_per_mwh",
    "price_dkk_per_mwh",
    "source",
    "source_record_id",
    "ingested_at_utc",
)
POWER_BALANCE_SELECT_COLUMNS = (
    "id",
    "price_area",
    "timestamp_utc",
    "production_mw",
    "consumption_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "exchange_net_mw",
    "source",
    "source_record_id",
    "ingested_at_utc",
)


def build_recent_spot_prices_query(
    *,
    price_area: str,
    limit: int = DEFAULT_READ_LIMIT,
) -> dict[str, Any]:
    """Build a read-only query for recent spot price rows.

    This pure helper only returns SQL text and params. It does not connect to a
    database, execute SQL, read environment variables, or attach to FastAPI.
    """
    return _build_recent_query(
        table=SPOT_PRICES_TABLE,
        columns=SPOT_PRICE_SELECT_COLUMNS,
        price_area=price_area,
        limit=limit,
    )


def build_recent_power_balance_query(
    *,
    price_area: str,
    limit: int = DEFAULT_READ_LIMIT,
) -> dict[str, Any]:
    """Build a read-only query for recent power balance rows."""
    return _build_recent_query(
        table=POWER_BALANCE_TABLE,
        columns=POWER_BALANCE_SELECT_COLUMNS,
        price_area=price_area,
        limit=limit,
    )


def build_spot_prices_time_window_query(
    *,
    price_area: str,
    start_utc: Any,
    end_utc: Any,
    limit: int = DEFAULT_READ_LIMIT,
) -> dict[str, Any]:
    """Build a read-only query for spot price rows in a UTC time window."""
    return _build_time_window_query(
        table=SPOT_PRICES_TABLE,
        columns=SPOT_PRICE_SELECT_COLUMNS,
        price_area=price_area,
        start_utc=start_utc,
        end_utc=end_utc,
        limit=limit,
    )


def build_power_balance_time_window_query(
    *,
    price_area: str,
    start_utc: Any,
    end_utc: Any,
    limit: int = DEFAULT_READ_LIMIT,
) -> dict[str, Any]:
    """Build a read-only query for power balance rows in a UTC time window."""
    return _build_time_window_query(
        table=POWER_BALANCE_TABLE,
        columns=POWER_BALANCE_SELECT_COLUMNS,
        price_area=price_area,
        start_utc=start_utc,
        end_utc=end_utc,
        limit=limit,
    )


def _build_recent_query(
    *,
    table: str,
    columns: tuple[str, ...],
    price_area: str,
    limit: int,
) -> dict[str, Any]:
    _validate_price_area(price_area)
    validated_limit = _validate_limit(limit)

    return {
        "sql": (
            f"SELECT {_column_sql(columns)} "
            f"FROM {table} "
            "WHERE price_area = %(price_area)s "
            "ORDER BY timestamp_utc DESC "
            "LIMIT %(limit)s"
        ),
        "params": {
            "price_area": price_area,
            "limit": validated_limit,
        },
        "table": table,
        "operation": SELECT_OPERATION,
    }


def _build_time_window_query(
    *,
    table: str,
    columns: tuple[str, ...],
    price_area: str,
    start_utc: Any,
    end_utc: Any,
    limit: int,
) -> dict[str, Any]:
    _validate_price_area(price_area)
    _validate_time_window(start_utc=start_utc, end_utc=end_utc)
    validated_limit = _validate_limit(limit)

    return {
        "sql": (
            f"SELECT {_column_sql(columns)} "
            f"FROM {table} "
            "WHERE price_area = %(price_area)s "
            "AND timestamp_utc >= %(start_utc)s "
            "AND timestamp_utc < %(end_utc)s "
            "ORDER BY timestamp_utc ASC "
            "LIMIT %(limit)s"
        ),
        "params": {
            "price_area": price_area,
            "start_utc": start_utc,
            "end_utc": end_utc,
            "limit": validated_limit,
        },
        "table": table,
        "operation": SELECT_OPERATION,
    }


def _column_sql(columns: tuple[str, ...]) -> str:
    return ", ".join(columns)


def _validate_price_area(price_area: Any) -> None:
    if price_area not in SUPPORTED_PRICE_AREAS:
        raise ValueError(f"Unsupported read query price area: {price_area}")


def _validate_limit(limit: Any) -> int:
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("Read query limit must be a positive integer")

    if limit < 1:
        raise ValueError("Read query limit must be a positive integer")

    if limit > MAX_READ_LIMIT:
        raise ValueError(f"Read query limit must be <= {MAX_READ_LIMIT}")

    return limit


def _validate_time_window(*, start_utc: Any, end_utc: Any) -> None:
    if start_utc is None:
        raise ValueError("Read query start_utc is required")

    if end_utc is None:
        raise ValueError("Read query end_utc is required")
