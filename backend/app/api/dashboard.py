from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from app.api.energy import execute_read_query
from app.api.energy_freshness_read import connect_with_psycopg
from app.db.read_queries import (
    build_recent_power_balance_query,
    build_recent_spot_prices_query,
)
from app.db.repositories.energy_freshness_reader import read_energy_freshness_summary
from app.risk.input_composer import compose_surplus_risk_input
from app.risk.rule_engine import calculate_surplus_risk


PriceArea = Literal["DK1", "DK2"]

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

UNAVAILABLE_CURRENT_RISK_WARNING = "current_risk is not_available"
UNAVAILABLE_CONFIDENCE_WARNING = "confidence is not_available"
UNCALCULATED_NEXT_WINDOW_WARNING = "next_surplus_window is not_calculated"
UNCALCULATED_EXPECTED_IMPACT_WARNING = "expected_impact is not_calculated"
UNCALCULATED_ECONOMIC_POTENTIAL_WARNING = "economic_potential is not_calculated"
UNAVAILABLE_FRESHNESS_WARNING = "data_freshness is not_available"


class DashboardDecisionSummaryPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price_area: PriceArea


@router.post("/decision-summary/preview")
def preview_dashboard_decision_summary(
    payload: DashboardDecisionSummaryPreviewRequest,
) -> dict[str, Any]:
    current_risk = _read_current_risk_if_available(payload.price_area)
    data_freshness = _read_data_freshness_if_available(payload.price_area)

    warnings = _build_warnings(
        current_risk=current_risk,
        data_freshness=data_freshness,
    )

    return {
        "price_area": payload.price_area,
        "decision_support_only": True,
        "human_review_required": True,
        "no_automatic_control": True,
        "no_dispatch": True,
        "no_activation": True,
        "current_risk": current_risk,
        "next_surplus_window": {
            "status": "not_calculated",
            "reason": (
                "Forecast-window preview requires caller-provided forecast rows; "
                "this dashboard summary request only includes price_area."
            ),
        },
        "confidence": _confidence_from_current_risk(current_risk),
        "expected_impact": {
            "status": "not_calculated",
            "reason": "No existing backend expected-impact calculation is available.",
        },
        "economic_potential": {
            "status": "not_calculated",
            "reason": (
                "No existing real backend economic-potential calculation is "
                "available for this preview."
            ),
        },
        "recommended_human_action": _recommended_human_action(current_risk),
        "data_freshness": data_freshness,
        "warnings": warnings,
        "source_notes": _build_source_notes(
            current_risk=current_risk,
            data_freshness=data_freshness,
        ),
    }


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
    data_freshness: dict[str, Any],
) -> list[str]:
    warnings = [
        UNCALCULATED_NEXT_WINDOW_WARNING,
        UNCALCULATED_EXPECTED_IMPACT_WARNING,
        UNCALCULATED_ECONOMIC_POTENTIAL_WARNING,
    ]

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
    data_freshness: dict[str, Any],
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

    return {
        "current_risk": current_risk_note,
        "next_surplus_window": (
            "Not calculated because this preview does not receive forecast rows."
        ),
        "confidence": (
            "Uses current_risk.confidence_score only when current risk is available."
        ),
        "expected_impact": "Not calculated; no existing backend source is available.",
        "economic_potential": (
            "Not calculated; no existing real backend economic source is available."
        ),
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
