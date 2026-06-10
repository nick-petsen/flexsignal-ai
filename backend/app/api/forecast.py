from __future__ import annotations

from datetime import datetime
from math import isfinite
from typing import Literal, Union

from fastapi import APIRouter, HTTPException
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    field_validator,
)

from app.forecast import build_forecast_window_forecast


PriceArea = Literal["DK1", "DK2"]
StrictNumber = Union[StrictInt, StrictFloat]
RiskLevel = Literal["low", "medium", "high", "unknown"]

NUMERIC_FIELDS = (
    "price_dkk_per_mwh",
    "production_mw",
    "consumption_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "exchange_net_mw",
)

router = APIRouter(prefix="/api/forecast", tags=["forecast"])


class ForecastPreviewRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_area: PriceArea
    timestamp_utc: datetime
    price_dkk_per_mwh: StrictNumber | None = None
    production_mw: StrictNumber | None = Field(default=None, ge=0)
    consumption_mw: StrictNumber | None = Field(default=None, ge=0)
    wind_onshore_mw: StrictNumber | None = Field(default=None, ge=0)
    wind_offshore_mw: StrictNumber | None = Field(default=None, ge=0)
    solar_mw: StrictNumber | None = Field(default=None, ge=0)
    exchange_net_mw: StrictNumber | None = None

    @field_validator("timestamp_utc")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp_utc must be timezone-aware")
        return value

    @field_validator(*NUMERIC_FIELDS)
    @classmethod
    def numeric_values_must_be_finite(
        cls,
        value: StrictNumber | None,
    ) -> StrictNumber | None:
        if value is not None and not isfinite(value):
            raise ValueError("numeric values must be finite")
        return value


class ForecastPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_area: PriceArea
    generated_at_utc: datetime
    rows: list[ForecastPreviewRow]

    @field_validator("generated_at_utc")
    @classmethod
    def generated_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return value


class ForecastReasonCodeCount(BaseModel):
    reason_code: str
    count: int


class ForecastWindowSummary(BaseModel):
    window_label: str
    start_utc: datetime
    end_utc: datetime
    row_count: int
    risk_level: RiskLevel
    max_risk_score: int | None
    average_risk_score: float | None
    average_confidence_score: float
    risk_level_counts: dict[str, int]
    top_reason_codes: list[ForecastReasonCodeCount]
    recommended_human_action: str
    explanation: str
    decision_support_only: bool


class ForecastPreviewResponse(BaseModel):
    price_area: PriceArea
    generated_at_utc: datetime
    model_version: str
    decision_support_only: bool
    safety: str
    windows: list[ForecastWindowSummary]


@router.post("/preview", response_model=ForecastPreviewResponse)
def preview_forecast_windows(
    payload: ForecastPreviewRequest,
) -> dict[str, object]:
    try:
        return build_forecast_window_forecast(
            price_area=payload.price_area,
            generated_at_utc=payload.generated_at_utc,
            rows=payload.rows,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
