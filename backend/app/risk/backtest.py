from __future__ import annotations

from collections import Counter
from typing import Any

from app.risk.rule_engine import MODEL_VERSION, calculate_surplus_risk

RISK_LEVELS = ("low", "medium", "high")
MISSING_PRICE_REASON = "MISSING_PRICE"
MISSING_GENERATION_REASON = "MISSING_PRODUCTION_OR_RENEWABLE_DATA"


def evaluate_risk_backtest(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate rule-engine-v0 over local rows without side effects."""
    risk_level_counts = dict.fromkeys(RISK_LEVELS, 0)
    reason_code_counts: Counter[str] = Counter()
    failed_row_errors: list[dict[str, Any]] = []

    risk_score_total = 0.0
    confidence_score_total = 0.0
    missing_price_count = 0
    missing_generation_data_count = 0
    evaluated_rows = 0

    for row_index, row in enumerate(rows):
        try:
            result = calculate_surplus_risk(row)
        except Exception as exc:  # noqa: BLE001 - row-level failures are reported.
            failed_row_errors.append(
                {
                    "row_index": row_index,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
            continue

        evaluated_rows += 1
        risk_score_total += result["risk_score"]
        confidence_score_total += result["confidence_score"]

        risk_level = result["risk_level"]
        if risk_level in risk_level_counts:
            risk_level_counts[risk_level] += 1

        reason_codes = result.get("reason_codes", [])
        reason_code_counts.update(reason_codes)

        if MISSING_PRICE_REASON in reason_codes:
            missing_price_count += 1
        if MISSING_GENERATION_REASON in reason_codes:
            missing_generation_data_count += 1

    failed_rows = len(failed_row_errors)

    return {
        "total_rows": len(rows),
        "evaluated_rows": evaluated_rows,
        "failed_rows": failed_rows,
        "risk_level_counts": risk_level_counts,
        "average_risk_score": _average(risk_score_total, evaluated_rows),
        "average_confidence_score": _average(
            confidence_score_total, evaluated_rows
        ),
        "reason_code_counts": dict(reason_code_counts),
        "missing_price_count": missing_price_count,
        "missing_generation_data_count": missing_generation_data_count,
        "failed_row_errors": failed_row_errors,
        "model_version": MODEL_VERSION,
        "decision_support_only": True,
    }


def _average(total: float, count: int) -> float:
    if count == 0:
        return 0.0
    return round(total / count, 4)
