from __future__ import annotations

import os
from datetime import date, datetime, timezone
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
from app.api.energy_freshness_read import connect_with_psycopg
from app.db.read_queries import (
    build_recent_power_balance_query,
    build_recent_spot_prices_query,
)
from app.db.repositories.energy_freshness_reader import read_energy_freshness_summary
from app.forecast import build_forecast_window_forecast
from app.risk.input_composer import compose_surplus_risk_input
from app.risk.rule_engine import calculate_surplus_risk


PriceArea = Literal["DK1", "DK2"]
StrictNumber = Union[StrictInt, StrictFloat]
NUMERIC_FORECAST_ROW_FIELDS = (
    "price_dkk_per_mwh",
    "production_mw",
    "consumption_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "exchange_net_mw",
)
LOW_PRICE_THRESHOLD_DKK_PER_MWH = 100
DKK_PER_EUR_FOR_DASHBOARD_SIGNAL = 7.45
ECONOMIC_POTENTIAL_MODEL_VERSION = "dashboard-economic-potential-v0"

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

UNAVAILABLE_CURRENT_RISK_WARNING = "current_risk is not_available"
UNAVAILABLE_CONFIDENCE_WARNING = "confidence is not_available"
UNCALCULATED_NEXT_WINDOW_WARNING = "next_surplus_window is not_calculated"
UNCALCULATED_EXPECTED_IMPACT_WARNING = "expected_impact is not_calculated"
UNCALCULATED_ECONOMIC_POTENTIAL_WARNING = "economic_potential is not_calculated"
UNAVAILABLE_FRESHNESS_WARNING = "data_freshness is not_available"


class DashboardDecisionSummaryForecastRow(BaseModel):
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

    @field_validator(*NUMERIC_FORECAST_ROW_FIELDS)
    @classmethod
    def numeric_values_must_be_finite(
        cls,
        value: StrictNumber | None,
    ) -> StrictNumber | None:
        if value is not None and not isfinite(value):
            raise ValueError("numeric values must be finite")
        return value


class DashboardDecisionSummaryPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_area: PriceArea
    forecast_rows: list[DashboardDecisionSummaryForecastRow] | None = None


@router.post("/decision-summary/preview")
def preview_dashboard_decision_summary(
    payload: DashboardDecisionSummaryPreviewRequest,
) -> dict[str, Any]:
    current_risk = _read_current_risk_if_available(payload.price_area)
    data_freshness = _read_data_freshness_if_available(payload.price_area)
    next_surplus_window = _calculate_next_surplus_window_if_available(payload)
    economic_potential = _calculate_economic_potential_if_available(payload)

    warnings = _build_warnings(
        current_risk=current_risk,
        next_surplus_window=next_surplus_window,
        data_freshness=data_freshness,
        economic_potential=economic_potential,
    )

    return {
        "price_area": payload.price_area,
        "decision_support_only": True,
        "human_review_required": True,
        "no_automatic_control": True,
        "no_dispatch": True,
        "no_activation": True,
        "current_risk": current_risk,
        "next_surplus_window": next_surplus_window,
        "confidence": _confidence_from_current_risk(current_risk),
        "expected_impact": {
            "status": "not_calculated",
            "reason": "No existing backend expected-impact calculation is available.",
        },
        "economic_potential": economic_potential,
        "recommended_human_action": _recommended_human_action(current_risk),
        "data_freshness": data_freshness,
        "warnings": warnings,
        "source_notes": _build_source_notes(
            current_risk=current_risk,
            next_surplus_window=next_surplus_window,
            data_freshness=data_freshness,
            economic_potential=economic_potential,
        ),
    }


def _calculate_next_surplus_window_if_available(
    payload: DashboardDecisionSummaryPreviewRequest,
) -> dict[str, Any]:
    if not payload.forecast_rows:
        return {
            "status": "not_calculated",
            "reason": (
                "Forecast-window preview requires caller-provided forecast rows; "
                "this dashboard summary request did not include forecast_rows."
            ),
        }

    matching_rows = [
        row for row in payload.forecast_rows if row.price_area == payload.price_area
    ]
    if not matching_rows:
        return {
            "status": "limited",
            "value": "no_matching_forecast_rows",
            "reason": (
                "Caller-provided forecast_rows were supplied, but none matched "
                f"price_area {payload.price_area}."
            ),
            "source": "caller_provided_forecast_rows",
        }

    generated_at_utc = min(
        row.timestamp_utc.astimezone(timezone.utc) for row in matching_rows
    )

    try:
        forecast = build_forecast_window_forecast(
            price_area=payload.price_area,
            generated_at_utc=generated_at_utc,
            rows=payload.forecast_rows,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    selected_window = _first_populated_forecast_window(forecast["windows"])
    if selected_window is None:
        return {
            "status": "limited",
            "value": "no_populated_forecast_window",
            "reason": (
                "Caller-provided forecast_rows were supplied, but no rows fell "
                "inside the existing 0-72h forecast-window preview range."
            ),
            "source": "caller_provided_forecast_rows",
            "model_version": forecast["model_version"],
        }

    return {
        "status": "available",
        "value": selected_window["window_label"],
        "window_label": selected_window["window_label"],
        "risk_level": selected_window["risk_level"],
        "risk_score": selected_window["max_risk_score"],
        "confidence_score": selected_window["average_confidence_score"],
        "row_count": selected_window["row_count"],
        "start_utc": selected_window["start_utc"],
        "end_utc": selected_window["end_utc"],
        "summary": (
            f"{selected_window['window_label']} "
            f"{selected_window['risk_level']} surplus risk from "
            f"{selected_window['row_count']} caller-provided forecast row(s)."
        ),
        "explanation": selected_window["explanation"],
        "recommended_human_action": selected_window["recommended_human_action"],
        "decision_support_only": selected_window["decision_support_only"],
        "source": "caller_provided_forecast_rows",
        "model_version": forecast["model_version"],
    }


def _first_populated_forecast_window(
    windows: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for window in windows:
        if window.get("row_count", 0) > 0:
            return window
    return None


def _calculate_economic_potential_if_available(
    payload: DashboardDecisionSummaryPreviewRequest,
) -> dict[str, Any]:
    if not payload.forecast_rows:
        return {
            "status": "not_calculated",
            "reason": (
                "Economic potential v0 requires caller-provided forecast_rows "
                "with usable price and surplus-risk signals."
            ),
        }

    matching_rows = [
        row for row in payload.forecast_rows if row.price_area == payload.price_area
    ]
    qualified_rows: list[dict[str, Any]] = []
    for row in matching_rows:
        price = row.price_dkk_per_mwh
        if price is None or price >= LOW_PRICE_THRESHOLD_DKK_PER_MWH:
            continue

        try:
            risk_result = calculate_surplus_risk(
                _normalize_rule_engine_input(row.model_dump())
            )
        except (TypeError, ValueError):
            continue

        if not _has_usable_surplus_risk_signal(risk_result):
            continue

        opportunity_dkk_per_mwh = LOW_PRICE_THRESHOLD_DKK_PER_MWH - float(price)
        qualified_rows.append(
            {
                "row": row,
                "risk_result": risk_result,
                "opportunity_dkk_per_mwh": opportunity_dkk_per_mwh,
            }
        )

    if not qualified_rows:
        return {
            "status": "not_calculated",
            "reason": (
                "Caller-provided forecast_rows did not contain both usable "
                "low or negative price data and surplus-risk signals."
            ),
            "source": "caller_provided_forecast_rows",
        }

    selected = max(
        qualified_rows,
        key=lambda candidate: (
            candidate["opportunity_dkk_per_mwh"],
            candidate["risk_result"]["risk_score"],
        ),
    )
    selected_row = selected["row"]
    selected_risk = selected["risk_result"]
    opportunity_eur_per_mwh = round(
        selected["opportunity_dkk_per_mwh"] / DKK_PER_EUR_FOR_DASHBOARD_SIGNAL,
        2,
    )

    return {
        "status": "calculated",
        "label": "Potential price opportunity",
        "value": f"Potential price opportunity: {opportunity_eur_per_mwh:.2f} EUR/MWh",
        "unit": "EUR/MWh",
        "opportunity_eur_per_mwh": opportunity_eur_per_mwh,
        "basis": (
            "Conservative price-only opportunity signal: deterministic "
            f"{LOW_PRICE_THRESHOLD_DKK_PER_MWH} DKK/MWh low-price threshold "
            "minus a qualifying caller-provided forecast-row price, converted "
            f"with fixed {DKK_PER_EUR_FOR_DASHBOARD_SIGNAL} DKK/EUR."
        ),
        "confidence_note": (
            "Limited deterministic signal from caller-provided forecast rows "
            "only; not a revenue, savings, profit, trading, dispatch, "
            "activation, or control estimate."
        ),
        "source": "caller_provided_forecast_rows",
        "source_notes": (
            "Calculated only from caller-provided forecast_rows for the "
            "requested price_area. No forecast rows, load size, volume, MW, "
            "MWh, tariffs, taxes, fees, site savings, revenue, profit, or "
            "customer assets were invented."
        ),
        "row_count": len(qualified_rows),
        "selected_timestamp_utc": selected_row.timestamp_utc.astimezone(
            timezone.utc
        ).isoformat(),
        "selected_price_dkk_per_mwh": selected_row.price_dkk_per_mwh,
        "risk_level": selected_risk["risk_level"],
        "risk_score": selected_risk["risk_score"],
        "model_version": ECONOMIC_POTENTIAL_MODEL_VERSION,
    }


def _has_usable_surplus_risk_signal(risk_result: dict[str, Any]) -> bool:
    if risk_result.get("risk_level") not in {"medium", "high"}:
        return False

    reason_codes = set(risk_result.get("reason_codes", ()))
    has_price_signal = bool(reason_codes & {"NEGATIVE_PRICE", "LOW_PRICE"})
    has_surplus_signal = bool(
        reason_codes
        & {
            "ELEVATED_RENEWABLE_SHARE",
            "MODERATE_RENEWABLE_SHARE",
            "HIGH_RENEWABLE_SHARE",
        }
    )
    return has_price_signal and has_surplus_signal


def _read_current_risk_if_available(price_area: str) -> dict[str, Any]:
    try:
        spot_price_query = build_recent_spot_prices_query(price_area=price_area, limit=1)
        power_balance_query = build_recent_power_balance_query(
            price_area=price_area,
            limit=1,
        )
        spot_price_row = _first_row_or_none(execute_read_query(spot_price_query))
        power_balance_row = _first_row_or_none(execute_read_query(power_balance_query))

        if spot_price_row is None and power_balance_row is None:
            return _not_available(
                "No spot_prices or power_balance rows are available for price_area."
            )

        risk_input = compose_surplus_risk_input(
            price_area=price_area,
            spot_price_row=spot_price_row,
            power_balance_row=power_balance_row,
        )
        risk_result = calculate_surplus_risk(_normalize_rule_engine_input(risk_input))
    except HTTPException as exc:
        return _not_available(str(exc.detail))
    except (RuntimeError, TypeError, ValueError) as exc:
        return _not_available(str(exc))

    return {
        "risk_level": risk_result["risk_level"],
        "risk_score": risk_result["risk_score"],
        "confidence_score": risk_result["confidence_score"],
        "explanation": risk_result["explanation"],
        "recommended_human_action": risk_result["recommended_human_action"],
        "source": "existing_current_risk_read_model",
    }


def _read_data_freshness_if_available(price_area: str) -> dict[str, Any]:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return _not_available("DATABASE_URL is not configured.")

    connection = None
    try:
        connection = connect_with_psycopg(database_url)
        freshness = read_energy_freshness_summary(connection, price_area)
    except HTTPException as exc:
        return _not_available(str(exc.detail))
    except (RuntimeError, ValueError) as exc:
        return _not_available(str(exc))
    except Exception:  # pragma: no cover - real DB failures are env-specific
        return _not_available("Database freshness read failed.")
    finally:
        if connection is not None:
            close = getattr(connection, "close", None)
            if callable(close):
                close()

    freshness_warnings = list(freshness.get("warnings", ()))
    row_counts = [
        freshness.get("spot_price_freshness", {}).get("row_count", 0),
        freshness.get("power_balance_freshness", {}).get("row_count", 0),
    ]
    status = "available"
    if freshness_warnings or any(row_count == 0 for row_count in row_counts):
        status = "limited"

    return {
        "status": status,
        "source": "existing_energy_freshness_read_model",
        "spot_price_row_count": row_counts[0],
        "power_balance_row_count": row_counts[1],
        "warnings": freshness_warnings,
    }


def _first_row_or_none(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return rows[0]


def _not_available(reason: str) -> dict[str, str]:
    return {
        "status": "not_available",
        "reason": reason,
    }


def _confidence_from_current_risk(current_risk: dict[str, Any]) -> dict[str, Any]:
    confidence_score = current_risk.get("confidence_score")
    if confidence_score is None:
        return {
            "status": "not_available",
            "reason": "No existing forecast or risk confidence value is available.",
        }

    return {
        "value": confidence_score,
        "source": "current_risk.confidence_score",
    }


def _recommended_human_action(current_risk: dict[str, Any]) -> str:
    recommended_action = current_risk.get("recommended_human_action")
    if isinstance(recommended_action, str) and recommended_action:
        return recommended_action
    return "Human review required"


def _build_warnings(
    *,
    current_risk: dict[str, Any],
    next_surplus_window: dict[str, Any],
    data_freshness: dict[str, Any],
    economic_potential: dict[str, Any],
) -> list[str]:
    warnings = [UNCALCULATED_EXPECTED_IMPACT_WARNING]

    if economic_potential.get("status") == "not_calculated":
        warnings.append(UNCALCULATED_ECONOMIC_POTENTIAL_WARNING)

    if next_surplus_window.get("status") == "not_calculated":
        warnings.insert(0, UNCALCULATED_NEXT_WINDOW_WARNING)

    if current_risk.get("status") == "not_available":
        warnings.extend(
            [
                UNAVAILABLE_CURRENT_RISK_WARNING,
                UNAVAILABLE_CONFIDENCE_WARNING,
            ]
        )

    if data_freshness.get("status") == "not_available":
        warnings.append(UNAVAILABLE_FRESHNESS_WARNING)

    return warnings


def _build_source_notes(
    *,
    current_risk: dict[str, Any],
    next_surplus_window: dict[str, Any],
    data_freshness: dict[str, Any],
    economic_potential: dict[str, Any],
) -> dict[str, str]:
    current_risk_note = (
        "Calculated from existing current-risk rule-engine logic when recent "
        "stored energy rows are readable; otherwise unavailable."
    )
    if current_risk.get("status") == "not_available":
        current_risk_note = "Unavailable; no current risk value was invented."

    freshness_note = (
        "Derived from the existing energy freshness read model when a configured "
        "database can be read; otherwise unavailable."
    )
    if data_freshness.get("status") == "not_available":
        freshness_note = "Unavailable; no freshness status was invented."

    next_window_note = (
        "Not calculated because this preview did not receive forecast_rows."
    )
    if next_surplus_window.get("source") == "caller_provided_forecast_rows":
        next_window_note = (
            "Calculated with existing forecast-window preview logic from "
            "caller-provided forecast_rows; no forecast rows were invented."
        )

    economic_potential_note = (
        "Not calculated; caller-provided forecast_rows did not contain usable "
        "price and surplus-risk signals."
    )
    if economic_potential.get("status") == "calculated":
        economic_potential_note = (
            "Calculated only from caller-provided forecast_rows as a "
            "conservative EUR/MWh price opportunity signal; not revenue, "
            "site-specific savings, trading advice, or control advice."
        )

    return {
        "current_risk": current_risk_note,
        "next_surplus_window": next_window_note,
        "confidence": (
            "Uses current_risk.confidence_score only when current risk is available."
        ),
        "expected_impact": "Not calculated; no existing backend source is available.",
        "economic_potential": economic_potential_note,
        "recommended_human_action": (
            "Uses existing risk recommendation when available; otherwise defaults "
            "to Human review required."
        ),
        "data_freshness": freshness_note,
    }


def _normalize_rule_engine_input(input_data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(input_data)

    timestamp_utc = normalized.get("timestamp_utc")
    if isinstance(timestamp_utc, datetime):
        normalized["timestamp_utc"] = timestamp_utc.isoformat()
    elif isinstance(timestamp_utc, date):
        normalized["timestamp_utc"] = timestamp_utc.isoformat()

    for field in (
        "price_dkk_per_mwh",
        "production_mw",
        "consumption_mw",
        "wind_onshore_mw",
        "wind_offshore_mw",
        "solar_mw",
        "exchange_net_mw",
    ):
        value = normalized.get(field)
        if isinstance(value, Decimal):
            normalized[field] = float(value)

    return normalized
