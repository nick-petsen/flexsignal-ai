from __future__ import annotations

from typing import Any

from app.risk.rule_engine import VALID_PRICE_AREAS


SPOT_PRICE_FIELDS = ("price_dkk_per_mwh",)
POWER_BALANCE_FIELDS = (
    "production_mw",
    "consumption_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "exchange_net_mw",
)


def compose_surplus_risk_input(
    price_area: str,
    spot_price_row: dict | None,
    power_balance_row: dict | None,
) -> dict:
    """Map existing energy rows into rule-engine-v0 input.

    This is deterministic mapping only. It does not calculate risk, connect to
    databases, execute SQL, call APIs, or trigger operational behavior.
    """
    _validate_price_area(price_area)
    _validate_rows_present(spot_price_row, power_balance_row)
    _validate_row_price_area(
        row=spot_price_row,
        requested_price_area=price_area,
        row_name="spot_price_row",
    )
    _validate_row_price_area(
        row=power_balance_row,
        requested_price_area=price_area,
        row_name="power_balance_row",
    )

    timestamp_utc = _timestamp_from_rows(
        spot_price_row=spot_price_row,
        power_balance_row=power_balance_row,
    )

    composed: dict[str, Any] = {
        "price_area": price_area,
        "timestamp_utc": timestamp_utc,
    }

    if spot_price_row is not None:
        _copy_present_fields(
            source=spot_price_row,
            destination=composed,
            fields=SPOT_PRICE_FIELDS,
        )

    if power_balance_row is not None:
        _copy_present_fields(
            source=power_balance_row,
            destination=composed,
            fields=POWER_BALANCE_FIELDS,
        )

    return composed


def _validate_price_area(price_area: str) -> None:
    if price_area not in VALID_PRICE_AREAS:
        raise ValueError("price_area must be DK1 or DK2")


def _validate_rows_present(
    spot_price_row: dict | None,
    power_balance_row: dict | None,
) -> None:
    if spot_price_row is None and power_balance_row is None:
        raise ValueError("At least one energy row must be provided")


def _validate_row_price_area(
    *,
    row: dict | None,
    requested_price_area: str,
    row_name: str,
) -> None:
    if row is None or "price_area" not in row:
        return

    if row["price_area"] != requested_price_area:
        raise ValueError(f"{row_name} price_area must match requested price_area")


def _timestamp_from_rows(
    *,
    spot_price_row: dict | None,
    power_balance_row: dict | None,
) -> Any:
    if power_balance_row is not None and power_balance_row.get("timestamp_utc"):
        return power_balance_row["timestamp_utc"]

    if spot_price_row is not None and spot_price_row.get("timestamp_utc"):
        return spot_price_row["timestamp_utc"]

    raise ValueError("timestamp_utc must exist in at least one energy row")


def _copy_present_fields(
    *,
    source: dict,
    destination: dict[str, Any],
    fields: tuple[str, ...],
) -> None:
    for field in fields:
        if field in source:
            destination[field] = source[field]
