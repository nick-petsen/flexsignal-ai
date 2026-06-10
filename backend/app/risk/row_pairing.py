from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

from app.risk.input_composer import compose_surplus_risk_input
from app.risk.rule_engine import VALID_PRICE_AREAS


@dataclass(frozen=True)
class _TimestampedRow:
    row: dict[str, Any]
    timestamp_utc: dt.datetime
    original_index: int


def pair_rows_by_nearest_timestamp(
    spot_price_rows: list[dict],
    power_balance_rows: list[dict],
    price_area: str,
) -> list[dict]:
    """Compose risk inputs by nearest timestamp without scoring or side effects."""
    _validate_price_area(price_area)

    parsed_spot_rows = _parse_rows(
        rows=spot_price_rows,
        row_name="spot_price_rows",
    )
    parsed_power_rows = _parse_rows(
        rows=power_balance_rows,
        row_name="power_balance_rows",
    )

    if not parsed_power_rows:
        return [
            compose_surplus_risk_input(
                price_area=price_area,
                spot_price_row=spot_row.row,
                power_balance_row=None,
            )
            for spot_row in parsed_spot_rows
        ]

    if not parsed_spot_rows:
        return [
            compose_surplus_risk_input(
                price_area=price_area,
                spot_price_row=None,
                power_balance_row=power_row.row,
            )
            for power_row in parsed_power_rows
        ]

    composed_rows: list[dict] = []
    for power_row in parsed_power_rows:
        nearest_spot_row = _nearest_spot_row(power_row, parsed_spot_rows)
        composed_rows.append(
            compose_surplus_risk_input(
                price_area=price_area,
                spot_price_row=nearest_spot_row.row,
                power_balance_row=power_row.row,
            )
        )

    return composed_rows


def _validate_price_area(price_area: str) -> None:
    if price_area not in VALID_PRICE_AREAS:
        raise ValueError("price_area must be DK1 or DK2")


def _parse_rows(
    *,
    rows: list[dict],
    row_name: str,
) -> list[_TimestampedRow]:
    return [
        _TimestampedRow(
            row=row,
            timestamp_utc=_parse_timestamp(row, row_name, row_index),
            original_index=row_index,
        )
        for row_index, row in enumerate(rows)
    ]


def _parse_timestamp(
    row: dict[str, Any],
    row_name: str,
    row_index: int,
) -> dt.datetime:
    timestamp = row.get("timestamp_utc")
    if timestamp is None:
        raise ValueError(f"{row_name}[{row_index}] timestamp_utc is required")

    if isinstance(timestamp, dt.datetime):
        parsed = timestamp
    elif isinstance(timestamp, str):
        timestamp_text = timestamp.strip()
        if not timestamp_text:
            raise ValueError(f"{row_name}[{row_index}] timestamp_utc is required")

        if timestamp_text.endswith("Z"):
            timestamp_text = f"{timestamp_text[:-1]}+00:00"

        try:
            parsed = dt.datetime.fromisoformat(timestamp_text)
        except ValueError as exc:
            raise ValueError(
                f"{row_name}[{row_index}] timestamp_utc must be a valid ISO "
                "timestamp with timezone"
            ) from exc
    else:
        raise ValueError(
            f"{row_name}[{row_index}] timestamp_utc must be a valid ISO "
            "timestamp with timezone"
        )

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(
            f"{row_name}[{row_index}] timestamp_utc must include timezone"
        )

    return parsed.astimezone(dt.timezone.utc)


def _nearest_spot_row(
    power_row: _TimestampedRow,
    spot_rows: list[_TimestampedRow],
) -> _TimestampedRow:
    return min(
        spot_rows,
        key=lambda spot_row: (
            abs(spot_row.timestamp_utc - power_row.timestamp_utc),
            spot_row.timestamp_utc,
            spot_row.original_index,
        ),
    )
