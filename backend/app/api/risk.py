from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from math import isfinite
from typing import Any, Literal, Union

from fastapi import APIRouter, HTTPException
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    field_validator,
)

from app.api.energy import execute_read_query
from app.db.read_queries import (
    build_recent_power_balance_query,
    build_recent_spot_prices_query,
)
from app.risk.input_composer import compose_surplus_risk_input
from app.risk.rule_engine import calculate_surplus_risk


PriceArea = Literal["DK1", "DK2"]
StrictNumber = Union[StrictInt, StrictFloat]

NUMERIC_FIELDS = (
    "price_dkk_per_mwh",
    "production_mw",
    "consumption_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "exchange_net_mw",
)

router = APIRouter(prefix="/api/risk", tags=["risk"])


class RiskPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_area: PriceArea
    timestamp_utc: str = Field(min_length=1)
    price_dkk_per_mwh: StrictNumber | None = None
    production_mw: StrictNumber | None = Field(default=None, ge=0)
    consumption_mw: StrictNumber | None = Field(default=None, ge=0)
    wind_onshore_mw: StrictNumber | None = Field(default=None, ge=0)
    wind_offshore_mw: StrictNumber | None = Field(default=None, ge=0)
    solar_mw: StrictNumber | None = Field(default=None, ge=0)
    exchange_net_mw: StrictNumber | None = None

    @field_validator(*NUMERIC_FIELDS)
    @classmethod
    def numeric_values_must_be_finite(
        cls,
        value: StrictNumber | None,
    ) -> StrictNumber | None:
        if value is not None and not isfinite(value):
            raise ValueError("numeric values must be finite")
        return value

    def to_engine_input(self) -> dict[str, object]:
        return self.model_dump(exclude_none=True)


class RiskPreviewResponse(BaseModel):
    price_area: PriceArea
    timestamp_utc: str
    risk_level: Literal["low", "medium", "high"]
    risk_score: int
    confidence_score: float
    reason_codes: list[str]
    explanation: str
    recommended_human_action: str
    model_version: str
    decision_support_only: bool


class RiskCurrentMetadata(BaseModel):
    source_tables_used: list[str]
    spot_price_row_found: bool
    power_balance_row_found: bool


class RiskCurrentResponse(RiskPreviewResponse):
    metadata: RiskCurrentMetadata


@router.post("/preview", response_model=RiskPreviewResponse)
def preview_surplus_risk(payload: RiskPreviewRequest) -> dict[str, object]:
    return calculate_surplus_risk(payload.to_engine_input())


@router.get("/current", response_model=RiskCurrentResponse)
def get_current_surplus_risk(price_area: PriceArea) -> dict[str, object]:
    spot_price_query = build_recent_spot_prices_query(price_area=price_area, limit=1)
    power_balance_query = build_recent_power_balance_query(
        price_area=price_area,
        limit=1,
    )

    spot_price_rows = execute_read_query(spot_price_query)
    power_balance_rows = execute_read_query(power_balance_query)

    spot_price_row = _first_row_or_none(spot_price_rows)
    power_balance_row = _first_row_or_none(power_balance_rows)

    if spot_price_row is None and power_balance_row is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No spot_prices or power_balance rows found for requested price_area"
            ),
        )

    try:
        risk_input = compose_surplus_risk_input(
            price_area=price_area,
            spot_price_row=spot_price_row,
            power_balance_row=power_balance_row,
        )
        risk_result = calculate_surplus_risk(_normalize_rule_engine_input(risk_input))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=500,
            detail="Current risk source data could not be scored",
        ) from exc

    return {
        **risk_result,
        "metadata": {
            "source_tables_used": [
                query["table"]
                for row, query in (
                    (spot_price_row, spot_price_query),
                    (power_balance_row, power_balance_query),
                )
                if row is not None
            ],
            "spot_price_row_found": spot_price_row is not None,
            "power_balance_row_found": power_balance_row is not None,
        },
    }


def _first_row_or_none(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return rows[0]


def _normalize_rule_engine_input(input_data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(input_data)

    timestamp_utc = normalized.get("timestamp_utc")
    if isinstance(timestamp_utc, datetime):
        normalized["timestamp_utc"] = timestamp_utc.isoformat()
    elif isinstance(timestamp_utc, date):
        normalized["timestamp_utc"] = timestamp_utc.isoformat()

    for field in NUMERIC_FIELDS:
        value = normalized.get(field)
        if isinstance(value, Decimal):
            normalized[field] = float(value)

    return normalized
