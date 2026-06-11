from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

REPORT_VERSION = "report-summary-v0"
VALID_PRICE_AREAS = {"DK1", "DK2"}

SAFETY_NOTES = [
    "read-only decision support only",
    "must not be used for automatic control",
    "must not be used for dispatch",
    "must not be used for activation",
    "no operational energy-system integration",
    "no autonomous decisions",
]

BASE_LIMITATIONS = [
    "no production forecast validation",
    "no outcome labels",
    "no DMI/weather data yet",
    "no ML training in report builder",
    "no LLM use in report builder",
    "caller-provided data only",
    "no database read/write",
    "no live API calls",
]

REQUIRED_HUMAN_ACTIONS = [
    "human review required before operational planning",
    "verify source data and operational context",
    "do not use for automatic control, dispatch, or activation",
]

CURRENT_RISK_FIELDS = (
    "risk_level",
    "risk_score",
    "confidence_score",
    "reason_codes",
    "recommended_human_action",
    "model_version",
)

FORECAST_WINDOW_FIELDS = (
    "window_label",
    "risk_level",
    "row_count",
    "max_risk_score",
    "average_risk_score",
    "top_reason_codes",
    "recommended_human_action",
)


def build_report_summary(
    *,
    price_area: str,
    generated_at_utc: datetime,
    current_risk: Mapping[str, Any] | object | None,
    forecast: Mapping[str, Any] | object | None,
    title: str | None = None,
    source_notes: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build a deterministic read-only report payload from supplied inputs."""
    if price_area not in VALID_PRICE_AREAS:
        raise ValueError("price_area must be DK1 or DK2")

    generated_at = _ensure_aware_datetime(
        generated_at_utc,
        field_name="generated_at_utc",
    )
    limitations = list(BASE_LIMITATIONS)
    current_risk_summary = _build_current_risk_summary(current_risk)
    if current_risk_summary["status"] == "unavailable":
        limitations.append("missing or incomplete current risk input")

    forecast_window_summary = _build_forecast_window_summary(forecast)
    if forecast_window_summary["status"] == "unavailable":
        limitations.append("missing or incomplete forecast input")

    report = {
        "report_id": _build_report_id(price_area, generated_at),
        "title": title or _default_title(price_area, generated_at),
        "price_area": price_area,
        "generated_at_utc": generated_at,
        "report_version": REPORT_VERSION,
        "decision_support_only": True,
        "human_review_required": True,
        "current_risk_summary": current_risk_summary,
        "forecast_window_summary": forecast_window_summary,
        "model_versions": _build_model_versions(
            current_risk_summary,
            forecast_window_summary,
        ),
        "key_findings": _build_key_findings(
            current_risk_summary,
            forecast_window_summary,
        ),
        "recommended_human_actions": _build_recommended_human_actions(
            current_risk_summary,
            forecast_window_summary,
        ),
        "safety_notes": list(SAFETY_NOTES),
        "limitations": limitations,
        "source_notes": list(source_notes or []),
    }
    return report


def _build_current_risk_summary(
    current_risk: Mapping[str, Any] | object | None,
) -> dict[str, Any]:
    if current_risk is None or not _has_fields(current_risk, CURRENT_RISK_FIELDS):
        return {
            "status": "unavailable",
            "decision_support_only": True,
        }

    return {
        "status": "available",
        "risk_level": _get_value(current_risk, "risk_level"),
        "risk_score": _get_value(current_risk, "risk_score"),
        "confidence_score": _get_value(current_risk, "confidence_score"),
        "reason_codes": list(_get_value(current_risk, "reason_codes") or []),
        "recommended_human_action": _get_value(
            current_risk,
            "recommended_human_action",
        ),
        "model_version": _get_value(current_risk, "model_version"),
        "decision_support_only": True,
    }


def _build_forecast_window_summary(
    forecast: Mapping[str, Any] | object | None,
) -> dict[str, Any]:
    if forecast is None or not _has_fields(forecast, ("model_version", "windows")):
        return {
            "status": "unavailable",
            "decision_support_only": True,
            "windows": [],
        }

    raw_windows = _get_value(forecast, "windows")
    if not isinstance(raw_windows, Sequence) or isinstance(raw_windows, (str, bytes)):
        return {
            "status": "unavailable",
            "decision_support_only": True,
            "windows": [],
        }

    windows: list[dict[str, Any]] = []
    for window in raw_windows:
        if not _has_present_fields(window, FORECAST_WINDOW_FIELDS):
            return {
                "status": "unavailable",
                "decision_support_only": True,
                "windows": [],
            }
        windows.append(
            {
                "window_label": _get_value(window, "window_label"),
                "risk_level": _get_value(window, "risk_level"),
                "row_count": _get_value(window, "row_count"),
                "max_risk_score": _get_value(window, "max_risk_score"),
                "average_risk_score": _get_value(window, "average_risk_score"),
                "top_reason_codes": list(
                    _get_value(window, "top_reason_codes") or []
                ),
                "recommended_human_action": _get_value(
                    window,
                    "recommended_human_action",
                ),
                "decision_support_only": True,
            }
        )

    return {
        "status": "available",
        "model_version": _get_value(forecast, "model_version"),
        "decision_support_only": True,
        "windows": windows,
    }


def _build_model_versions(
    current_risk_summary: Mapping[str, Any],
    forecast_window_summary: Mapping[str, Any],
) -> dict[str, str | None]:
    return {
        "report": REPORT_VERSION,
        "current_risk": current_risk_summary.get("model_version"),
        "forecast_window": forecast_window_summary.get("model_version"),
    }


def _build_key_findings(
    current_risk_summary: Mapping[str, Any],
    forecast_window_summary: Mapping[str, Any],
) -> list[str]:
    findings: list[str] = []

    if current_risk_summary.get("status") == "available":
        findings.append(
            f"Current risk is {current_risk_summary['risk_level']} based on caller-provided data."
        )
    else:
        findings.append("Current risk is unavailable because caller-provided input is missing or incomplete.")

    windows = forecast_window_summary.get("windows") or []
    high_windows = [
        window for window in windows if window.get("risk_level") == "high"
    ]
    unknown_windows = [
        window
        for window in windows
        if window.get("risk_level") == "unknown" or window.get("row_count") == 0
    ]

    for window in high_windows:
        findings.append(f"Forecast window {window['window_label']} is high risk.")

    for window in unknown_windows:
        findings.append(
            f"Forecast window {window['window_label']} is unknown due to no caller-provided rows."
        )

    if forecast_window_summary.get("status") == "available" and not high_windows:
        findings.append("No forecast window is high risk.")
    elif forecast_window_summary.get("status") == "unavailable":
        findings.append("Forecast window summary is unavailable because caller-provided input is missing or incomplete.")

    findings.append("Report is based on caller-provided data only.")
    return findings


def _build_recommended_human_actions(
    current_risk_summary: Mapping[str, Any],
    forecast_window_summary: Mapping[str, Any],
) -> list[str]:
    actions: list[str] = []

    if current_risk_summary.get("status") == "available":
        action = current_risk_summary.get("recommended_human_action")
        if action:
            actions.append(str(action))

    for window in forecast_window_summary.get("windows") or []:
        action = window.get("recommended_human_action")
        if action:
            actions.append(str(action))

    actions.extend(REQUIRED_HUMAN_ACTIONS)
    return _deduplicate(actions)


def _deduplicate(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        if value not in seen:
            deduplicated.append(value)
            seen.add(value)
    return deduplicated


def _has_fields(value: Mapping[str, Any] | object, fields: Sequence[str]) -> bool:
    return all(_has_present_field(value, field) for field in fields)


def _has_present_fields(
    value: Mapping[str, Any] | object,
    fields: Sequence[str],
) -> bool:
    return all(_has_present_field(value, field, allow_none=True) for field in fields)


def _has_present_field(
    value: Mapping[str, Any] | object,
    field_name: str,
    *,
    allow_none: bool = False,
) -> bool:
    if isinstance(value, Mapping):
        if field_name not in value:
            return False
        return allow_none or value[field_name] is not None

    if not hasattr(value, field_name):
        return False
    return allow_none or getattr(value, field_name) is not None


def _get_value(value: Mapping[str, Any] | object, field_name: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(field_name)
    return getattr(value, field_name, None)


def _ensure_aware_datetime(value: datetime, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _format_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_report_id(price_area: str, generated_at_utc: datetime) -> str:
    stable_key = f"{price_area}|{_format_utc_timestamp(generated_at_utc)}|{REPORT_VERSION}"
    digest = sha256(stable_key.encode("utf-8")).hexdigest()[:16]
    return f"{REPORT_VERSION}-{price_area}-{digest}"


def _default_title(price_area: str, generated_at_utc: datetime) -> str:
    return (
        f"FlexSignal AI report summary for {price_area} "
        f"at {_format_utc_timestamp(generated_at_utc)}"
    )
