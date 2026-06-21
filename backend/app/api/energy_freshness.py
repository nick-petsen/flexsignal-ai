from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.db.repositories.energy_freshness import (
    POWER_BALANCE_FRESHNESS_PART,
    SPOT_PRICE_FRESHNESS_PART,
    build_energy_freshness_summary_plan,
    build_power_balance_freshness_query,
    build_spot_price_freshness_query,
)


router = APIRouter(prefix="/api/energy", tags=["energy"])

SAFETY_BOUNDARY = {
    "read_only_decision_support": True,
    "no_automatic_control": True,
    "no_dispatch": True,
    "no_activation": True,
    "no_operational_energy_system_integration": True,
    "human_review_required": True,
}
WARNINGS = (
    "Preview only: query plans are returned for human review.",
    "No SQL is run and no stored energy data is read by this endpoint.",
)


@router.get("/freshness")
def preview_energy_freshness(price_area: str) -> dict[str, Any]:
    try:
        spot_price_plan = build_spot_price_freshness_query(price_area)
        power_balance_plan = build_power_balance_freshness_query(price_area)
        freshness_plans = build_energy_freshness_summary_plan(price_area)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Unsupported price_area") from exc

    return {
        "price_area": price_area,
        "dry_run": True,
        "database_query_executed": False,
        "database_write_performed": False,
        "requires_database_url": False,
        "freshness_plans": freshness_plans,
        "spot_price_freshness_plan": spot_price_plan,
        "power_balance_freshness_plan": power_balance_plan,
        "warnings": list(WARNINGS),
        "safety_boundary": dict(SAFETY_BOUNDARY),
        "plan_parts": {
            "spot_price": SPOT_PRICE_FRESHNESS_PART,
            "power_balance": POWER_BALANCE_FRESHNESS_PART,
        },
    }
