from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.audit.events import build_audit_event


RUNTIME_FACTORY_VERSION = "audit-runtime-event-factory-v0"
DEFAULT_ACTOR_TYPE = "local_developer"
DEFAULT_ACTOR_ID = "unknown-local-user"
DEFAULT_OUTCOME = "success"
DEFAULT_FORECAST_WINDOW_VERSION = "forecast-window-v0"
DEFAULT_REPORT_VERSION = "report-summary-v0"


def build_current_risk_viewed_event(
    *,
    price_area: str,
    actor_type: str = DEFAULT_ACTOR_TYPE,
    actor_id: str | None = DEFAULT_ACTOR_ID,
    occurred_at_utc: datetime | None = None,
    request_id: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    price_area = _required_text(price_area, field_name="price_area")
    return build_audit_event(
        event_type="current_risk_viewed",
        actor_type=actor_type,
        actor_id=_actor_id_or_default(actor_id),
        occurred_at_utc=_occurred_at_or_now(occurred_at_utc),
        resource_type="risk_snapshot",
        resource_id=f"risk-snapshot-v0:{price_area}",
        action="view_current_risk",
        outcome=DEFAULT_OUTCOME,
        decision_support_only=True,
        metadata=_runtime_metadata(
            price_area=price_area,
            request_id=request_id,
            source=source,
        ),
    )


def build_forecast_preview_requested_event(
    *,
    price_area: str,
    actor_type: str = DEFAULT_ACTOR_TYPE,
    actor_id: str | None = DEFAULT_ACTOR_ID,
    occurred_at_utc: datetime | None = None,
    request_id: str | None = None,
    source: str | None = None,
    forecast_window_version: str = DEFAULT_FORECAST_WINDOW_VERSION,
    model_version: str | None = None,
) -> dict[str, Any]:
    price_area = _required_text(price_area, field_name="price_area")
    forecast_window_version = _required_text(
        forecast_window_version,
        field_name="forecast_window_version",
    )
    metadata = _runtime_metadata(
        price_area=price_area,
        request_id=request_id,
        source=source,
        forecast_window_version=forecast_window_version,
    )
    if model_version is not None:
        metadata["model_version"] = _required_text(
            model_version,
            field_name="model_version",
        )

    return build_audit_event(
        event_type="forecast_preview_requested",
        actor_type=actor_type,
        actor_id=_actor_id_or_default(actor_id),
        occurred_at_utc=_occurred_at_or_now(occurred_at_utc),
        resource_type="forecast_preview",
        resource_id=f"{forecast_window_version}:{price_area}",
        action="preview_forecast",
        outcome=DEFAULT_OUTCOME,
        decision_support_only=True,
        metadata=metadata,
    )


def build_report_summary_built_event(
    *,
    price_area: str,
    actor_type: str = DEFAULT_ACTOR_TYPE,
    actor_id: str | None = DEFAULT_ACTOR_ID,
    occurred_at_utc: datetime | None = None,
    request_id: str | None = None,
    source: str | None = None,
    report_version: str = DEFAULT_REPORT_VERSION,
) -> dict[str, Any]:
    price_area = _required_text(price_area, field_name="price_area")
    report_version = _required_text(report_version, field_name="report_version")
    return build_audit_event(
        event_type="report_summary_built",
        actor_type=actor_type,
        actor_id=_actor_id_or_default(actor_id),
        occurred_at_utc=_occurred_at_or_now(occurred_at_utc),
        resource_type="report_summary",
        resource_id=f"{report_version}:{price_area}:summary",
        action="build_report_summary",
        outcome=DEFAULT_OUTCOME,
        decision_support_only=True,
        metadata=_runtime_metadata(
            price_area=price_area,
            request_id=request_id,
            source=source,
            report_version=report_version,
        ),
    )


def build_report_markdown_rendered_event(
    *,
    price_area: str,
    actor_type: str = DEFAULT_ACTOR_TYPE,
    actor_id: str | None = DEFAULT_ACTOR_ID,
    occurred_at_utc: datetime | None = None,
    request_id: str | None = None,
    source: str | None = None,
    report_version: str = DEFAULT_REPORT_VERSION,
    output_format: str = "markdown",
) -> dict[str, Any]:
    price_area = _required_text(price_area, field_name="price_area")
    report_version = _required_text(report_version, field_name="report_version")
    output_format = _required_text(output_format, field_name="output_format")
    return build_audit_event(
        event_type="report_markdown_rendered",
        actor_type=actor_type,
        actor_id=_actor_id_or_default(actor_id),
        occurred_at_utc=_occurred_at_or_now(occurred_at_utc),
        resource_type="report_markdown",
        resource_id=f"{report_version}:{price_area}:markdown",
        action="render_report_markdown",
        outcome=DEFAULT_OUTCOME,
        decision_support_only=True,
        metadata=_runtime_metadata(
            price_area=price_area,
            request_id=request_id,
            source=source,
            report_version=report_version,
            output_format=output_format,
        ),
    )


def build_report_pdf_exported_event(
    *,
    price_area: str,
    actor_type: str = DEFAULT_ACTOR_TYPE,
    actor_id: str | None = DEFAULT_ACTOR_ID,
    occurred_at_utc: datetime | None = None,
    request_id: str | None = None,
    source: str | None = None,
    report_version: str = DEFAULT_REPORT_VERSION,
    output_format: str = "pdf",
) -> dict[str, Any]:
    price_area = _required_text(price_area, field_name="price_area")
    report_version = _required_text(report_version, field_name="report_version")
    output_format = _required_text(output_format, field_name="output_format")
    return build_audit_event(
        event_type="report_pdf_exported",
        actor_type=actor_type,
        actor_id=_actor_id_or_default(actor_id),
        occurred_at_utc=_occurred_at_or_now(occurred_at_utc),
        resource_type="report_pdf",
        resource_id=f"{report_version}:{price_area}:pdf",
        action="preview_report_pdf_export",
        outcome=DEFAULT_OUTCOME,
        decision_support_only=True,
        metadata=_runtime_metadata(
            price_area=price_area,
            request_id=request_id,
            source=source,
            report_version=report_version,
            output_format=output_format,
        ),
    )


def _runtime_metadata(
    *,
    price_area: str,
    request_id: str | None = None,
    source: str | None = None,
    forecast_window_version: str | None = None,
    report_version: str | None = None,
    output_format: str | None = None,
) -> dict[str, str]:
    metadata = {
        "price_area": price_area,
        "runtime_factory_version": RUNTIME_FACTORY_VERSION,
    }
    _add_optional_text(metadata, "request_id", request_id)
    _add_optional_text(metadata, "source", source)
    _add_optional_text(
        metadata,
        "forecast_window_version",
        forecast_window_version,
    )
    _add_optional_text(metadata, "report_version", report_version)
    _add_optional_text(metadata, "output_format", output_format)
    return metadata


def _add_optional_text(
    metadata: dict[str, str],
    key: str,
    value: str | None,
) -> None:
    if value is not None:
        metadata[key] = _required_text(value, field_name=key)


def _required_text(value: str, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def _actor_id_or_default(actor_id: str | None) -> str:
    if actor_id is None:
        return DEFAULT_ACTOR_ID
    return _required_text(actor_id, field_name="actor_id")


def _occurred_at_or_now(occurred_at_utc: datetime | None) -> datetime:
    if occurred_at_utc is None:
        return datetime.now(timezone.utc)
    return occurred_at_utc
