#!/usr/bin/env python3
"""Read-only local customer pilot workflow preview."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from customer_pilot_intake_validate import (  # noqa: E402
    DEFAULT_MIN_ROWS,
    CustomerPilotIntakeConfig,
    CustomerPilotIntakeSummary,
    CustomerPilotIntakeValidationError,
    validate_customer_pilot_intake,
)
from customer_pilot_opportunity_estimate import (  # noqa: E402
    CustomerPilotOpportunityEstimateConfig,
    CustomerPilotOpportunityEstimateError,
    CustomerPilotOpportunityEstimateSummary,
    estimate_customer_pilot_opportunity,
)
from customer_pilot_signal_match import (  # noqa: E402
    DEFAULT_MIN_MATCH_ROWS,
    DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH,
    CustomerPilotSignalMatchConfig,
    CustomerPilotSignalMatchError,
    CustomerPilotSignalMatchSummary,
    match_customer_pilot_signal,
)


ALLOWED_PRICE_AREAS = frozenset({"DK1", "DK2"})
ALLOWED_CUSTOMER_TYPES = frozenset(
    {"common", "producer", "flexible_consumption", "grid_dso"}
)
DEFAULT_DRY_RUN = "true"
SAFETY_BOUNDARY = (
    "read-only workflow preview only",
    "no customer-specific savings calculated",
    "no profit/revenue calculated",
    "no automatic control",
    "no dispatch",
    "no activation",
    "no live control signals",
    "no asset integration",
    "no database writes",
    "no external API calls",
    "human review required",
    "customer data must not be committed to git",
)
BASELINE_OPPORTUNITY_WARNINGS = frozenset(
    {
        "Indicative gross opportunity signal uses public price signal only.",
        (
            "Customer-specific value requires tariff, constraints, operating "
            "costs, and human validation."
        ),
        "Read-only decision support; human review required.",
    }
)
NEXT_HUMAN_REVIEW_STEPS = (
    "Review candidate windows with the customer operational owner.",
    "Confirm the preview uses public price signal only.",
    (
        "Validate tariff, constraints, operating costs, and human interpretation "
        "before any customer-specific assessment."
    ),
    "Keep customer data and pilot CSV files out of git.",
)


class CustomerPilotWorkflowPreviewError(RuntimeError):
    """Expected safe-fail error for customer pilot workflow preview."""


@dataclass(frozen=True)
class CustomerPilotWorkflowPreviewConfig:
    input_path: Path
    snapshot_path: Path
    customer_type: str
    price_area: str | None
    dry_run: bool


@dataclass(frozen=True)
class CustomerPilotWorkflowPreviewSummary:
    workflow_status: str
    validation_status: str
    signal_match_status: str
    opportunity_estimate_status: str
    total_customer_rows: int
    matched_window_count: int
    matched_customer_rows: int
    total_matched_flexible_energy_mwh: float
    total_indicative_gross_opportunity_signal_eur: float
    top_candidate_windows: tuple[Mapping[str, Any], ...]
    warnings: tuple[str, ...]
    next_human_review_steps: tuple[str, ...]
    safety_boundary: tuple[str, ...]
    errors: tuple[str, ...]
    dry_run: bool
    file_written: bool = False
    database_write_performed: bool = False
    external_api_calls_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_status": self.workflow_status,
            "validation_status": self.validation_status,
            "signal_match_status": self.signal_match_status,
            "opportunity_estimate_status": self.opportunity_estimate_status,
            "total_customer_rows": self.total_customer_rows,
            "matched_window_count": self.matched_window_count,
            "matched_customer_rows": self.matched_customer_rows,
            "total_matched_flexible_energy_mwh": (
                self.total_matched_flexible_energy_mwh
            ),
            "total_indicative_gross_opportunity_signal_eur": (
                self.total_indicative_gross_opportunity_signal_eur
            ),
            "top_candidate_windows": list(self.top_candidate_windows),
            "warnings": list(self.warnings),
            "next_human_review_steps": list(self.next_human_review_steps),
            "safety_boundary": list(self.safety_boundary),
            "errors": list(self.errors),
            "dry_run": self.dry_run,
            "file_written": self.file_written,
            "database_write_performed": self.database_write_performed,
            "external_api_calls_performed": self.external_api_calls_performed,
        }


def load_config(
    env: Mapping[str, str] | None = None,
) -> CustomerPilotWorkflowPreviewConfig:
    safe_env = os.environ if env is None else env
    raw_input_path = safe_env.get("CUSTOMER_PILOT_INPUT_PATH")
    if raw_input_path is None or not raw_input_path.strip():
        raise CustomerPilotWorkflowPreviewError("CUSTOMER_PILOT_INPUT_PATH is required")

    customer_type = (
        safe_env.get("CUSTOMER_PILOT_CUSTOMER_TYPE", "common").strip() or "common"
    )
    if customer_type not in ALLOWED_CUSTOMER_TYPES:
        raise CustomerPilotWorkflowPreviewError(
            "CUSTOMER_PILOT_CUSTOMER_TYPE must be one of: common, producer, "
            "flexible_consumption, grid_dso"
        )

    raw_price_area = safe_env.get("CUSTOMER_PILOT_PRICE_AREA")
    price_area = raw_price_area.strip() if raw_price_area else None
    if price_area == "":
        price_area = None
    if price_area is not None and price_area not in ALLOWED_PRICE_AREAS:
        raise CustomerPilotWorkflowPreviewError(
            "CUSTOMER_PILOT_PRICE_AREA must be DK1 or DK2"
        )

    snapshot_path = (
        safe_env.get(
            "PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH",
            DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH,
        ).strip()
        or DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH
    )

    return CustomerPilotWorkflowPreviewConfig(
        input_path=Path(raw_input_path).expanduser(),
        snapshot_path=Path(snapshot_path).expanduser(),
        customer_type=customer_type,
        price_area=price_area,
        dry_run=_parse_bool(
            safe_env.get("CUSTOMER_PILOT_DRY_RUN", DEFAULT_DRY_RUN),
            "CUSTOMER_PILOT_DRY_RUN",
        ),
    )


def run_customer_pilot_workflow_preview(
    config: CustomerPilotWorkflowPreviewConfig,
) -> CustomerPilotWorkflowPreviewSummary:
    validation_config = CustomerPilotIntakeConfig(
        input_path=config.input_path,
        customer_type=config.customer_type,
        min_rows=DEFAULT_MIN_ROWS,
        dry_run=config.dry_run,
    )
    validation_summary = validate_customer_pilot_intake(validation_config)
    if validation_summary.status == "invalid":
        return _build_invalid_summary(
            validation_status=validation_summary.status,
            signal_match_status="not_run",
            opportunity_estimate_status="not_run",
            total_customer_rows=validation_summary.row_count,
            warnings=validation_summary.warnings,
            errors=validation_summary.errors,
            dry_run=config.dry_run,
        )

    signal_summary = match_customer_pilot_signal(
        CustomerPilotSignalMatchConfig(
            input_path=config.input_path,
            snapshot_path=config.snapshot_path,
            price_area=config.price_area,
            min_match_rows=DEFAULT_MIN_MATCH_ROWS,
            dry_run=config.dry_run,
        )
    )
    if signal_summary.status == "invalid":
        return _build_invalid_summary(
            validation_status=validation_summary.status,
            signal_match_status=signal_summary.status,
            opportunity_estimate_status="not_run",
            total_customer_rows=signal_summary.total_customer_rows
            or validation_summary.row_count,
            warnings=(*validation_summary.warnings, *signal_summary.warnings),
            errors=signal_summary.errors,
            dry_run=config.dry_run,
        )

    estimate_summary = estimate_customer_pilot_opportunity(
        CustomerPilotOpportunityEstimateConfig(
            input_path=config.input_path,
            snapshot_path=config.snapshot_path,
            price_area=config.price_area,
            dry_run=config.dry_run,
        )
    )

    workflow_status = _workflow_status(
        validation_summary=validation_summary,
        signal_summary=signal_summary,
        estimate_summary=estimate_summary,
    )
    warnings = _workflow_warnings(
        validation_summary=validation_summary,
        signal_summary=signal_summary,
        estimate_summary=estimate_summary,
    )
    if workflow_status == "ready_with_warnings" and not warnings:
        warnings = ("Matched public windows need human review before next steps.",)

    return CustomerPilotWorkflowPreviewSummary(
        workflow_status=workflow_status,
        validation_status=validation_summary.status,
        signal_match_status=signal_summary.status,
        opportunity_estimate_status=estimate_summary.status,
        total_customer_rows=estimate_summary.total_customer_rows,
        matched_window_count=estimate_summary.matched_window_count,
        matched_customer_rows=estimate_summary.matched_customer_rows,
        total_matched_flexible_energy_mwh=(
            estimate_summary.total_matched_flexible_energy_mwh
        ),
        total_indicative_gross_opportunity_signal_eur=(
            estimate_summary.total_indicative_gross_opportunity_signal_eur
        ),
        top_candidate_windows=_top_candidate_windows(
            estimate_summary.candidate_estimates
        ),
        warnings=warnings,
        next_human_review_steps=NEXT_HUMAN_REVIEW_STEPS,
        safety_boundary=SAFETY_BOUNDARY,
        errors=estimate_summary.errors,
        dry_run=config.dry_run,
    )


def print_summary(summary: CustomerPilotWorkflowPreviewSummary) -> None:
    print("Customer pilot workflow preview summary")
    print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))


def main() -> int:
    try:
        config = load_config()
        summary = run_customer_pilot_workflow_preview(config)
    except (
        CustomerPilotWorkflowPreviewError,
        CustomerPilotIntakeValidationError,
        CustomerPilotSignalMatchError,
        CustomerPilotOpportunityEstimateError,
    ) as exc:
        summary = _build_invalid_summary(
            validation_status="not_run",
            signal_match_status="not_run",
            opportunity_estimate_status="not_run",
            total_customer_rows=0,
            warnings=(),
            errors=(str(exc),),
            dry_run=True,
        )

    print_summary(summary)
    if summary.workflow_status == "invalid":
        return 1
    return 0


def _workflow_status(
    *,
    validation_summary: CustomerPilotIntakeSummary,
    signal_summary: CustomerPilotSignalMatchSummary,
    estimate_summary: CustomerPilotOpportunityEstimateSummary,
) -> str:
    if (
        validation_summary.status == "invalid"
        or signal_summary.status == "invalid"
        or estimate_summary.status == "invalid"
    ):
        return "invalid"
    if signal_summary.status == "no_matches" or estimate_summary.status == "no_matches":
        return "no_matches"
    if estimate_summary.status != "estimate_available":
        return "ready_with_warnings"
    if validation_summary.status == "valid_with_warnings":
        return "ready_with_warnings"
    if signal_summary.status == "matched_with_warnings":
        return "ready_with_warnings"
    if _filtered_opportunity_warnings(estimate_summary.warnings):
        return "ready_with_warnings"
    return "ready_for_human_review"


def _workflow_warnings(
    *,
    validation_summary: CustomerPilotIntakeSummary,
    signal_summary: CustomerPilotSignalMatchSummary,
    estimate_summary: CustomerPilotOpportunityEstimateSummary,
) -> tuple[str, ...]:
    warnings = [
        *_prefixed("validation", validation_summary.warnings),
        *_prefixed("signal_match", signal_summary.warnings),
        *_prefixed(
            "opportunity_estimate",
            _filtered_opportunity_warnings(estimate_summary.warnings),
        ),
    ]
    return tuple(dict.fromkeys(warnings))


def _filtered_opportunity_warnings(warnings: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        warning for warning in warnings if warning not in BASELINE_OPPORTUNITY_WARNINGS
    )


def _prefixed(label: str, values: Sequence[str]) -> tuple[str, ...]:
    return tuple(f"{label}: {value}" for value in values)


def _top_candidate_windows(
    candidate_estimates: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    sorted_candidates = sorted(
        candidate_estimates,
        key=lambda estimate: (
            estimate.get("estimate_status") != "estimate_available",
            -_safe_float(estimate.get("indicative_gross_opportunity_signal_eur")),
            -_safe_float(estimate.get("public_risk_score")),
            str(estimate.get("public_window_start", "")),
        ),
    )
    return tuple(sorted_candidates[:5])


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _build_invalid_summary(
    *,
    validation_status: str,
    signal_match_status: str,
    opportunity_estimate_status: str,
    total_customer_rows: int,
    warnings: Sequence[str],
    errors: Sequence[str],
    dry_run: bool,
) -> CustomerPilotWorkflowPreviewSummary:
    return CustomerPilotWorkflowPreviewSummary(
        workflow_status="invalid",
        validation_status=validation_status,
        signal_match_status=signal_match_status,
        opportunity_estimate_status=opportunity_estimate_status,
        total_customer_rows=total_customer_rows,
        matched_window_count=0,
        matched_customer_rows=0,
        total_matched_flexible_energy_mwh=0.0,
        total_indicative_gross_opportunity_signal_eur=0.0,
        top_candidate_windows=(),
        warnings=tuple(warnings),
        next_human_review_steps=NEXT_HUMAN_REVIEW_STEPS,
        safety_boundary=SAFETY_BOUNDARY,
        errors=tuple(errors),
        dry_run=dry_run,
    )


def _parse_bool(raw_value: str | None, env_name: str) -> bool:
    normalized = (raw_value or "").strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise CustomerPilotWorkflowPreviewError(f"{env_name} must be true or false")


if __name__ == "__main__":
    raise SystemExit(main())
