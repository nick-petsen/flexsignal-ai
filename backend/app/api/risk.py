from __future__ import annotations

from math import isfinite
from typing import Literal, Union

from fastapi import APIRouter
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    field_validator,
)

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


@router.post("/preview", response_model=RiskPreviewResponse)
def preview_surplus_risk(payload: RiskPreviewRequest) -> dict[str, object]:
    return calculate_surplus_risk(payload.to_engine_input())
