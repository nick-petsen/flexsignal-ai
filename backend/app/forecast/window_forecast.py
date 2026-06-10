from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from app.risk.rule_engine import (
    MODEL_VERSION as RULE_ENGINE_MODEL_VERSION,
    NUMERIC_FIELDS,
    VALID_PRICE_AREAS,
    calculate_surplus_risk,
)

FORECAST_WINDOW_MODEL_VERSION = f"{RULE_ENGINE_MODEL_VERSION}+forecast-window-v0"
DECISION_SUPPORT_SAFETY_TEXT = (
    "This is read-only decision support and must not be used for automatic "
    "control, dispatch, or activation."
)

WINDOW_DEFINITIONS = (
    ("0-24h", timedelta(hours=0), timedelta(hours=24)),
    ("24-48h", timedelta(hours=24), timedelta(hours=48)),
    ("48-72h", timedelta(hours=48), timedelta(hours=72)),
)

RISK_LEVELS = ("low", "medium", "high", "unknown")


def build_forecast_window_forecast(
    *,
    price_area: str,
    generated_at_utc: datetime,
    rows: Sequence[Mapping[str, Any] | object],
) -> dict[str, Any]:
    """Aggregate caller-provided surplus-risk rows into 24-hour windows.

    This function is deterministic aggregation only. It does not fetch, persist,
    schedule, train, call APIs, use LLMs, or perform operational control.
    """
    if price_area not in VALID_PRICE_AREAS:
        raise ValueError("price_area must be DK1 or DK2")

    generated_at = _ensure_aware_datetime(
        generated_at_utc,
        field_name="generated_at_utc",
    )

    scored_windows: dict[str, list[dict[str, Any]]] = {
        label: [] for label, _, _ in WINDOW_DEFINITIONS
    }

    for row in rows:
        row_price_area = _get_required_value(row, "price_area")
        if row_price_area not in VALID_PRICE_AREAS:
            raise ValueError("row price_area must be DK1 or DK2")
        if row_price_area != price_area:
            continue

        timestamp_value = _get_required_value(row, "timestamp_utc")
        timestamp = _coerce_aware_datetime(
            timestamp_value,
            field_name="timestamp_utc",
        )

        if timestamp < generated_at or timestamp >= generated_at + timedelta(hours=72):
            continue

        window_label = _window_label_for_timestamp(timestamp, generated_at)
        scoring_input = _build_scoring_input(row, price_area, timestamp)
        scored_windows[window_label].append(calculate_surplus_risk(scoring_input))

    return {
        "price_area": price_area,
        "generated_at_utc": generated_at,
        "model_version": FORECAST_WINDOW_MODEL_VERSION,
        "decision_support_only": True,
        "safety": DECISION_SUPPORT_SAFETY_TEXT,
        "windows": [
            _summarize_window(label, generated_at + start, generated_at + end, results)
            for label, start, end in WINDOW_DEFINITIONS
            for results in (scored_windows[label],)
        ],
    }


def _summarize_window(
    window_label: str,
    start_utc: datetime,
    end_utc: datetime,
    scored_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if not scored_rows:
        return {
            "window_label": window_label,
            "start_utc": start_utc,
            "end_utc": end_utc,
            "row_count": 0,
            "risk_level": "unknown",
            "max_risk_score": None,
            "average_risk_score": None,
            "average_confidence_score": 0,
            "risk_level_counts": _risk_level_counts([]),
            "top_reason_codes": [],
            "recommended_human_action": (
                "Human review required before planning because there is not "
                f"enough caller-provided data for this window. {DECISION_SUPPORT_SAFETY_TEXT}"
            ),
            "explanation": (
                "There is not enough caller-provided data for this forecast "
                f"window. {DECISION_SUPPORT_SAFETY_TEXT}"
            ),
            "decision_support_only": True,
        }

    max_result = max(scored_rows, key=lambda result: result["risk_score"])
    risk_scores = [result["risk_score"] for result in scored_rows]
    confidence_scores = [result["confidence_score"] for result in scored_rows]

    return {
        "window_label": window_label,
        "start_utc": start_utc,
        "end_utc": end_utc,
        "row_count": len(scored_rows),
        "risk_level": max_result["risk_level"],
        "max_risk_score": max_result["risk_score"],
        "average_risk_score": round(sum(risk_scores) / len(risk_scores), 4),
        "average_confidence_score": round(
            sum(confidence_scores) / len(confidence_scores),
            4,
        ),
        "risk_level_counts": _risk_level_counts(
            result["risk_level"] for result in scored_rows
        ),
        "top_reason_codes": _top_reason_codes(scored_rows),
        "recommended_human_action": _recommended_human_action(max_result["risk_level"]),
        "explanation": (
            "This is deterministic forecast-window aggregation over "
            "caller-provided data using rule-engine-v0 row scores. The window "
            f"risk level is based on the maximum observed risk score, "
            f"{max_result['risk_score']}/100. {DECISION_SUPPORT_SAFETY_TEXT}"
        ),
        "decision_support_only": True,
    }


def _get_required_value(row: Mapping[str, Any] | object, field_name: str) -> Any:
    if isinstance(row, Mapping):
        value = row.get(field_name)
    else:
        value = getattr(row, field_name, None)

    if value is None:
        raise ValueError(f"{field_name} must be present")
    return value


def _get_optional_value(row: Mapping[str, Any] | object, field_name: str) -> Any:
    if isinstance(row, Mapping):
        return row.get(field_name)
    return getattr(row, field_name, None)


def _ensure_aware_datetime(value: datetime, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _coerce_aware_datetime(value: Any, *, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return _ensure_aware_datetime(value, field_name=field_name)

    if isinstance(value, str) and value:
        normalized_value = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized_value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be an ISO datetime") from exc
        return _ensure_aware_datetime(parsed, field_name=field_name)

    raise ValueError(f"{field_name} must be present as a timezone-aware datetime")


def _window_label_for_timestamp(timestamp: datetime, generated_at: datetime) -> str:
    offset = timestamp - generated_at
    for label, start, end in WINDOW_DEFINITIONS:
        if start <= offset < end:
            return label
    raise ValueError("timestamp is outside the forecast window")


def _build_scoring_input(
    row: Mapping[str, Any] | object,
    price_area: str,
    timestamp_utc: datetime,
) -> dict[str, Any]:
    scoring_input: dict[str, Any] = {
        "price_area": price_area,
        "timestamp_utc": _format_utc_timestamp(timestamp_utc),
    }

    for field_name in sorted(NUMERIC_FIELDS):
        value = _get_optional_value(row, field_name)
        if value is not None:
            scoring_input[field_name] = value

    return scoring_input


def _format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _risk_level_counts(risk_levels: Any) -> dict[str, int]:
    counts = Counter(risk_levels)
    return {risk_level: counts.get(risk_level, 0) for risk_level in RISK_LEVELS}


def _top_reason_codes(scored_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for result in scored_rows:
        counts.update(result["reason_codes"])

    return [
        {"reason_code": reason_code, "count": count}
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]


def _recommended_human_action(risk_level: str) -> str:
    if risk_level in {"medium", "high"}:
        return (
            "Human review required before planning; verify caller-provided "
            f"source data and operational context. {DECISION_SUPPORT_SAFETY_TEXT}"
        )

    return (
        "Continue routine human monitoring of caller-provided forecasts. "
        f"{DECISION_SUPPORT_SAFETY_TEXT}"
    )
