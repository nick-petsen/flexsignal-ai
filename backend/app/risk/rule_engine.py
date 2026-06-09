from __future__ import annotations

from math import isfinite
from typing import Any

MODEL_VERSION = "rule-engine-v0"
VALID_PRICE_AREAS = {"DK1", "DK2"}

NUMERIC_FIELDS = {
    "price_dkk_per_mwh",
    "production_mw",
    "consumption_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
    "exchange_net_mw",
}

NON_NEGATIVE_FIELDS = {
    "production_mw",
    "consumption_mw",
    "wind_onshore_mw",
    "wind_offshore_mw",
    "solar_mw",
}

RENEWABLE_FIELDS = ("wind_onshore_mw", "wind_offshore_mw", "solar_mw")


def calculate_surplus_risk(input_data: dict[str, Any]) -> dict[str, Any]:
    """Calculate deterministic read-only surplus-risk support for DK1/DK2."""
    _validate_input(input_data)

    price_area = input_data["price_area"]
    timestamp_utc = input_data["timestamp_utc"]
    reason_codes: list[str] = []

    score = 0
    confidence = 1.0

    price = input_data.get("price_dkk_per_mwh")
    if price is None:
        reason_codes.append("MISSING_PRICE")
        confidence -= 0.25
    elif price < 0:
        score += 40
        reason_codes.append("NEGATIVE_PRICE")
    elif price < 100:
        score += 25
        reason_codes.append("LOW_PRICE")
    elif price < 250:
        score += 10
        reason_codes.append("MODERATE_PRICE")
    else:
        reason_codes.append("NORMAL_PRICE")

    renewable_share = _calculate_renewable_share(input_data)
    if renewable_share is None:
        reason_codes.append("MISSING_PRODUCTION_OR_RENEWABLE_DATA")
        confidence -= 0.30
    elif renewable_share >= 0.80:
        score += 35
        reason_codes.append("HIGH_RENEWABLE_SHARE")
    elif renewable_share >= 0.60:
        score += 20
        reason_codes.append("MODERATE_RENEWABLE_SHARE")
    elif renewable_share >= 0.40:
        score += 10
        reason_codes.append("ELEVATED_RENEWABLE_SHARE")
    else:
        reason_codes.append("LOW_RENEWABLE_SHARE")

    if "exchange_net_mw" in input_data:
        reason_codes.append("EXCHANGE_NET_NOT_USED_V0")

    risk_score = min(score, 100)
    confidence_score = round(max(confidence, 0.2), 2)
    risk_level = _risk_level_for_score(risk_score)

    return {
        "price_area": price_area,
        "timestamp_utc": timestamp_utc,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "confidence_score": confidence_score,
        "reason_codes": reason_codes,
        "explanation": _build_explanation(risk_level, risk_score, reason_codes),
        "recommended_human_action": _recommended_human_action(risk_level),
        "model_version": MODEL_VERSION,
        "decision_support_only": True,
    }


def _validate_input(input_data: dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise TypeError("input_data must be a dictionary")

    if input_data.get("price_area") not in VALID_PRICE_AREAS:
        raise ValueError("price_area must be DK1 or DK2")

    timestamp_utc = input_data.get("timestamp_utc")
    if not isinstance(timestamp_utc, str) or not timestamp_utc:
        raise ValueError("timestamp_utc must be present as a non-empty string")

    for field in NUMERIC_FIELDS:
        if field not in input_data or input_data[field] is None:
            continue

        value = input_data[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{field} must be an int or float when present")
        if not isfinite(value):
            raise ValueError(f"{field} must be finite when present")
        if field in NON_NEGATIVE_FIELDS and value < 0:
            raise ValueError(f"{field} must be non-negative")


def _calculate_renewable_share(input_data: dict[str, Any]) -> float | None:
    production_mw = input_data.get("production_mw")
    renewable_values = [input_data.get(field) for field in RENEWABLE_FIELDS]

    if production_mw is None or any(value is None for value in renewable_values):
        return None

    if production_mw == 0:
        return 0.0

    renewable_mw = sum(renewable_values)
    return renewable_mw / production_mw


def _risk_level_for_score(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def _build_explanation(
    risk_level: str, risk_score: int, reason_codes: list[str]
) -> str:
    reasons = ", ".join(reason_codes)
    return (
        f"Surplus risk is {risk_level} with score {risk_score}/100 based on "
        f"deterministic rule-engine-v0 signals: {reasons}. This is read-only "
        "decision support and must not be used for automatic control, dispatch, "
        "or activation."
    )


def _recommended_human_action(risk_level: str) -> str:
    if risk_level == "high":
        return (
            "Human review required before planning; verify source data and keep "
            "any action outside this read-only model."
        )
    if risk_level == "medium":
        return (
            "Human review recommended; compare against current market and "
            "production context before planning."
        )
    return (
        "No surplus-risk escalation from this rule engine; continue routine "
        "human monitoring."
    )
