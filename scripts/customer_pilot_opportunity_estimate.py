#!/usr/bin/env python3
"""Read-only local customer pilot opportunity estimate preview."""

from __future__ import annotations

import csv
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


REQUIRED_COLUMNS = (
    "site_id",
    "price_area",
    "timestamp",
    "timezone",
)
ALLOWED_PRICE_AREAS = frozenset({"DK1", "DK2"})
DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH = (
    "frontend/src/data/public-surplus-risk-backtest-snapshot.json"
)
DEFAULT_DRY_RUN = "true"
TRUE_AVAILABILITY_VALUES = frozenset({"1", "true", "yes"})
SAFETY_BOUNDARY = (
    "read-only opportunity preview only",
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
)


class CustomerPilotOpportunityEstimateError(RuntimeError):
    """Expected safe-fail error for customer pilot opportunity estimates."""


@dataclass(frozen=True)
class CustomerPilotOpportunityEstimateConfig:
    input_path: Path
    snapshot_path: Path
    price_area: str | None
    dry_run: bool


@dataclass(frozen=True)
class CustomerPilotRow:
    price_area: str
    timestamp_utc: datetime
    values: Mapping[str, str]


@dataclass(frozen=True)
class CustomerPilotOpportunityEstimateSummary:
    status: str
    total_customer_rows: int
    matched_window_count: int
    matched_customer_rows: int
    total_matched_flexible_energy_mwh: float
    total_indicative_gross_opportunity_signal_eur: float
    candidate_estimates: tuple[Mapping[str, Any], ...]
    warnings: tuple[str, ...]
    safety_boundary: tuple[str, ...]
    customer_price_areas_detected: tuple[str, ...]
    errors: tuple[str, ...]
    dry_run: bool
    file_written: bool = False
    database_write_performed: bool = False
    external_api_calls_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "total_customer_rows": self.total_customer_rows,
            "matched_window_count": self.matched_window_count,
            "matched_customer_rows": self.matched_customer_rows,
            "total_matched_flexible_energy_mwh": (
                self.total_matched_flexible_energy_mwh
            ),
            "total_indicative_gross_opportunity_signal_eur": (
                self.total_indicative_gross_opportunity_signal_eur
            ),
            "candidate_estimates": list(self.candidate_estimates),
            "warnings": list(self.warnings),
            "safety_boundary": list(self.safety_boundary),
            "customer_price_areas_detected": list(
                self.customer_price_areas_detected
            ),
            "errors": list(self.errors),
            "dry_run": self.dry_run,
            "file_written": self.file_written,
            "database_write_performed": self.database_write_performed,
            "external_api_calls_performed": self.external_api_calls_performed,
        }


def load_config(
    env: Mapping[str, str] | None = None,
) -> CustomerPilotOpportunityEstimateConfig:
    safe_env = os.environ if env is None else env
    raw_input_path = safe_env.get("CUSTOMER_PILOT_INPUT_PATH")
    if raw_input_path is None or not raw_input_path.strip():
        raise CustomerPilotOpportunityEstimateError(
            "CUSTOMER_PILOT_INPUT_PATH is required"
        )

    raw_price_area = safe_env.get("CUSTOMER_PILOT_PRICE_AREA")
    price_area = raw_price_area.strip() if raw_price_area else None
    if price_area == "":
        price_area = None
    if price_area is not None and price_area not in ALLOWED_PRICE_AREAS:
        raise CustomerPilotOpportunityEstimateError(
            "CUSTOMER_PILOT_PRICE_AREA must be DK1 or DK2"
        )

    snapshot_path = (
        safe_env.get(
            "PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH",
            DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH,
        ).strip()
        or DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH
    )

    return CustomerPilotOpportunityEstimateConfig(
        input_path=Path(raw_input_path).expanduser(),
        snapshot_path=Path(snapshot_path).expanduser(),
        price_area=price_area,
        dry_run=_parse_bool(
            safe_env.get("CUSTOMER_PILOT_DRY_RUN", DEFAULT_DRY_RUN),
            "CUSTOMER_PILOT_DRY_RUN",
        ),
    )


def estimate_customer_pilot_opportunity(
    config: CustomerPilotOpportunityEstimateConfig,
) -> CustomerPilotOpportunityEstimateSummary:
    warnings: list[str] = [
        "Indicative gross opportunity signal uses public price signal only.",
        (
            "Customer-specific value requires tariff, constraints, operating "
            "costs, and human validation."
        ),
        "Read-only decision support; human review required.",
    ]
    errors: list[str] = []

    if not config.input_path.exists() or not config.input_path.is_file():
        errors.append("Input file does not exist or is not a readable file.")
        return _invalid_summary(config, warnings, errors)
    if config.input_path.suffix.lower() != ".csv":
        errors.append("Only CSV input files are accepted for v0.")
        return _invalid_summary(config, warnings, errors)
    if not config.snapshot_path.exists() or not config.snapshot_path.is_file():
        errors.append("Public surplus-risk snapshot path is invalid.")
        return _invalid_summary(config, warnings, errors)

    try:
        detected_columns, raw_rows = _read_csv(config.input_path)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        errors.append(f"CSV could not be parsed: {exc.__class__.__name__}.")
        return _invalid_summary(config, warnings, errors)

    missing_columns = tuple(
        column for column in REQUIRED_COLUMNS if column not in set(detected_columns)
    )
    if missing_columns:
        errors.append(
            "Required customer columns are missing: "
            f"{', '.join(missing_columns)}."
        )
        return _build_summary(
            config=config,
            status="invalid",
            customer_price_areas_detected=(),
            total_customer_rows=len(raw_rows),
            candidate_estimates=(),
            warnings=warnings,
            errors=errors,
        )

    try:
        snapshot = _read_snapshot(config.snapshot_path)
        public_windows = _public_windows_by_price_area(snapshot)
        customer_rows, detected_price_areas = _parse_customer_rows(raw_rows)
    except (
        OSError,
        json.JSONDecodeError,
        CustomerPilotOpportunityEstimateError,
    ) as exc:
        errors.append(str(exc))
        return _build_summary(
            config=config,
            status="invalid",
            customer_price_areas_detected=(),
            total_customer_rows=len(raw_rows),
            candidate_estimates=(),
            warnings=warnings,
            errors=errors,
        )

    skipped_rows = len(raw_rows) - len(customer_rows)
    if skipped_rows:
        warnings.append(
            "Rows outside DK1/DK2 were ignored; ignored row count: "
            f"{skipped_rows}."
        )

    active_price_areas = _active_price_areas(config.price_area, detected_price_areas)
    if not active_price_areas:
        warnings.append("No DK1/DK2 customer price areas were detected.")
    if config.price_area is not None and config.price_area not in detected_price_areas:
        warnings.append(
            "Configured customer price area was not present in the customer CSV."
        )

    active_area_set = set(active_price_areas)
    filtered_rows = [
        row for row in customer_rows if row.price_area in active_area_set
    ]
    candidate_estimates = _candidate_estimates(
        customer_rows=filtered_rows,
        public_windows=public_windows,
        columns=detected_columns,
    )

    if not candidate_estimates:
        status = "no_matches"
    elif any(
        estimate["estimate_status"] == "estimate_available"
        for estimate in candidate_estimates
    ):
        status = "estimate_available"
    else:
        status = "matched_with_missing_inputs"

    if candidate_estimates and status == "matched_with_missing_inputs":
        warnings.append(
            "Matched public windows need customer flexible energy, customer "
            "availability, or available public price context before a numeric "
            "indicative gross opportunity signal can be shown."
        )

    return _build_summary(
        config=config,
        status=status,
        customer_price_areas_detected=detected_price_areas,
        total_customer_rows=len(raw_rows),
        candidate_estimates=tuple(candidate_estimates),
        warnings=warnings,
        errors=errors,
    )


def print_summary(summary: CustomerPilotOpportunityEstimateSummary) -> None:
    print("Customer pilot indicative gross opportunity signal summary")
    print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))


def main() -> int:
    try:
        config = load_config()
        summary = estimate_customer_pilot_opportunity(config)
    except CustomerPilotOpportunityEstimateError as exc:
        summary = CustomerPilotOpportunityEstimateSummary(
            status="invalid",
            total_customer_rows=0,
            matched_window_count=0,
            matched_customer_rows=0,
            total_matched_flexible_energy_mwh=0.0,
            total_indicative_gross_opportunity_signal_eur=0.0,
            candidate_estimates=(),
            warnings=(),
            safety_boundary=SAFETY_BOUNDARY,
            customer_price_areas_detected=(),
            errors=(str(exc),),
            dry_run=True,
        )

    print_summary(summary)
    if summary.status == "invalid":
        return 1
    return 0


def _read_csv(path: Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file, strict=True)
        if reader.fieldnames is None:
            raise csv.Error("missing header row")
        fieldnames = tuple((fieldname or "").strip() for fieldname in reader.fieldnames)
        if not fieldnames or any(not fieldname for fieldname in fieldnames):
            raise csv.Error("blank column names are not supported")
        rows = []
        for row in reader:
            if None in row:
                raise csv.Error("row has more values than the header")
            rows.append(
                {
                    key.strip(): "" if value is None else str(value).strip()
                    for key, value in row.items()
                }
            )
    return fieldnames, rows


def _read_snapshot(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as snapshot_file:
        snapshot = json.load(snapshot_file)
    if not isinstance(snapshot, dict):
        raise CustomerPilotOpportunityEstimateError(
            "Public surplus-risk snapshot is invalid."
        )
    if "top_risk_windows" not in snapshot:
        raise CustomerPilotOpportunityEstimateError(
            "Public surplus-risk snapshot is missing top_risk_windows."
        )
    return snapshot


def _public_windows_by_price_area(
    snapshot: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    raw_windows = snapshot.get("top_risk_windows")
    if not isinstance(raw_windows, dict):
        raise CustomerPilotOpportunityEstimateError(
            "Public surplus-risk snapshot top_risk_windows is invalid."
        )

    public_windows: dict[str, list[dict[str, Any]]] = {"DK1": [], "DK2": []}
    for price_area in ALLOWED_PRICE_AREAS:
        area_windows = raw_windows.get(price_area, [])
        if not isinstance(area_windows, list):
            raise CustomerPilotOpportunityEstimateError(
                f"Public surplus-risk windows for {price_area} are invalid."
            )
        for raw_window in area_windows:
            if not isinstance(raw_window, dict):
                raise CustomerPilotOpportunityEstimateError(
                    f"Public surplus-risk window for {price_area} is invalid."
                )
            try:
                start = _parse_public_timestamp(str(raw_window["start"]))
                end = _parse_public_timestamp(str(raw_window["end"]))
            except (KeyError, ValueError) as exc:
                raise CustomerPilotOpportunityEstimateError(
                    f"Public surplus-risk window for {price_area} has invalid timestamps."
                ) from exc
            public_windows[price_area].append(
                {
                    "price_area": price_area,
                    "start": start,
                    "end": end,
                    "score": raw_window.get("score"),
                    "level": raw_window.get("level"),
                    "price_context_status": raw_window.get(
                        "price_context_status"
                    ),
                    "opportunity_signal_eur_per_mwh": raw_window.get(
                        "opportunity_signal_eur_per_mwh"
                    ),
                }
            )
    return public_windows


def _parse_customer_rows(
    raw_rows: Sequence[Mapping[str, str]],
) -> tuple[list[CustomerPilotRow], tuple[str, ...]]:
    customer_rows: list[CustomerPilotRow] = []
    detected_price_areas: set[str] = set()
    timestamp_errors = 0

    for row in raw_rows:
        price_area = row.get("price_area", "").strip()
        if price_area not in ALLOWED_PRICE_AREAS:
            continue
        detected_price_areas.add(price_area)
        try:
            timestamp_utc = _parse_customer_timestamp(
                row.get("timestamp", ""),
                row.get("timezone", ""),
            )
        except CustomerPilotOpportunityEstimateError:
            timestamp_errors += 1
            continue
        customer_rows.append(
            CustomerPilotRow(
                price_area=price_area,
                timestamp_utc=timestamp_utc,
                values=row,
            )
        )

    if timestamp_errors:
        raise CustomerPilotOpportunityEstimateError(
            "Customer timestamps could not be parsed safely; invalid row count: "
            f"{timestamp_errors}."
        )

    return customer_rows, tuple(sorted(detected_price_areas))


def _candidate_estimates(
    *,
    customer_rows: Sequence[CustomerPilotRow],
    public_windows: Mapping[str, Sequence[Mapping[str, Any]]],
    columns: Sequence[str],
) -> list[dict[str, Any]]:
    candidate_estimates: list[dict[str, Any]] = []
    has_availability_column = "availability_flag" in set(columns)

    for price_area in ("DK1", "DK2"):
        area_customer_rows = [
            row for row in customer_rows if row.price_area == price_area
        ]
        if not area_customer_rows:
            continue

        for public_window in public_windows.get(price_area, ()):
            start = public_window["start"]
            end = public_window["end"]
            matched_rows = [
                row
                for row in area_customer_rows
                if start <= row.timestamp_utc <= end
            ]
            if not matched_rows:
                continue

            opportunity_signal = _parse_optional_float(
                public_window.get("opportunity_signal_eur_per_mwh")
            )
            price_signal_available = (
                public_window.get("price_context_status") == "available"
                and opportunity_signal is not None
            )
            customer_available_rows = [
                row
                for row in matched_rows
                if _row_available_for_customer(row, has_availability_column)
            ]
            matched_flexible_energy_mwh = sum(
                _positive_float(row.values.get("flexible_energy_mwh", ""))
                for row in customer_available_rows
            )

            if has_availability_column and not customer_available_rows:
                estimate_status = "matched_but_not_available_for_customer"
            elif not price_signal_available:
                estimate_status = "matched_but_price_signal_unavailable"
            elif matched_flexible_energy_mwh <= 0:
                estimate_status = "matched_but_missing_flexible_energy"
            else:
                estimate_status = "estimate_available"

            estimate_value = 0.0
            if estimate_status == "estimate_available":
                estimate_value = matched_flexible_energy_mwh * float(
                    opportunity_signal
                )

            candidate_estimates.append(
                {
                    "price_area": price_area,
                    "public_window_start": _format_utc(start),
                    "public_window_end": _format_utc(end),
                    "public_risk_score": public_window.get("score"),
                    "public_risk_level": public_window.get("level"),
                    "public_opportunity_signal_eur_per_mwh": opportunity_signal,
                    "customer_rows_in_window": len(matched_rows),
                    "matched_flexible_energy_mwh": _round_amount(
                        matched_flexible_energy_mwh
                    ),
                    "indicative_gross_opportunity_signal_eur": _round_amount(
                        estimate_value
                    ),
                    "estimate_status": estimate_status,
                }
            )

    return candidate_estimates


def _active_price_areas(
    configured_price_area: str | None,
    detected_price_areas: Sequence[str],
) -> tuple[str, ...]:
    if configured_price_area is not None:
        return (configured_price_area,)
    return tuple(price_area for price_area in detected_price_areas if price_area)


def _parse_customer_timestamp(raw_timestamp: str, raw_timezone: str) -> datetime:
    normalized_timestamp = raw_timestamp.strip().replace("Z", "+00:00")
    if not normalized_timestamp:
        raise CustomerPilotOpportunityEstimateError("timestamp is required")
    try:
        parsed = datetime.fromisoformat(normalized_timestamp)
    except ValueError as exc:
        raise CustomerPilotOpportunityEstimateError("timestamp is invalid") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_parse_timezone(raw_timezone))
    return parsed.astimezone(timezone.utc)


def _parse_public_timestamp(raw_timestamp: str) -> datetime:
    normalized_timestamp = raw_timestamp.strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized_timestamp)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_timezone(raw_timezone: str) -> ZoneInfo:
    normalized_timezone = raw_timezone.strip()
    if not normalized_timezone:
        raise CustomerPilotOpportunityEstimateError("timezone is required")
    try:
        return ZoneInfo(normalized_timezone)
    except ZoneInfoNotFoundError as exc:
        raise CustomerPilotOpportunityEstimateError("timezone is invalid") from exc


def _row_available_for_customer(
    row: CustomerPilotRow,
    has_availability_column: bool,
) -> bool:
    if not has_availability_column:
        return True
    return row.values.get("availability_flag", "").strip().lower() in (
        TRUE_AVAILABILITY_VALUES
    )


def _positive_float(raw_value: str) -> float:
    parsed = _parse_optional_float(raw_value)
    if parsed is None or parsed <= 0:
        return 0.0
    return parsed


def _parse_optional_float(raw_value: Any) -> float | None:
    if raw_value is None:
        return None
    if isinstance(raw_value, bool):
        return None
    try:
        return float(str(raw_value).strip())
    except ValueError:
        return None


def _round_amount(value: float) -> float:
    return round(value, 6)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_summary(
    *,
    config: CustomerPilotOpportunityEstimateConfig,
    status: str,
    customer_price_areas_detected: tuple[str, ...],
    total_customer_rows: int,
    candidate_estimates: tuple[Mapping[str, Any], ...],
    warnings: list[str],
    errors: list[str],
) -> CustomerPilotOpportunityEstimateSummary:
    return CustomerPilotOpportunityEstimateSummary(
        status=status,
        total_customer_rows=total_customer_rows,
        matched_window_count=len(candidate_estimates),
        matched_customer_rows=sum(
            int(estimate["customer_rows_in_window"])
            for estimate in candidate_estimates
        ),
        total_matched_flexible_energy_mwh=_round_amount(
            sum(
                float(estimate["matched_flexible_energy_mwh"])
                for estimate in candidate_estimates
            )
        ),
        total_indicative_gross_opportunity_signal_eur=_round_amount(
            sum(
                float(estimate["indicative_gross_opportunity_signal_eur"])
                for estimate in candidate_estimates
            )
        ),
        candidate_estimates=candidate_estimates,
        warnings=tuple(warnings),
        safety_boundary=SAFETY_BOUNDARY,
        customer_price_areas_detected=customer_price_areas_detected,
        errors=tuple(errors),
        dry_run=config.dry_run,
    )


def _invalid_summary(
    config: CustomerPilotOpportunityEstimateConfig,
    warnings: list[str],
    errors: list[str],
) -> CustomerPilotOpportunityEstimateSummary:
    return _build_summary(
        config=config,
        status="invalid",
        customer_price_areas_detected=(),
        total_customer_rows=0,
        candidate_estimates=(),
        warnings=warnings,
        errors=errors,
    )


def _parse_bool(raw_value: str | None, env_name: str) -> bool:
    normalized = (raw_value or "").strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise CustomerPilotOpportunityEstimateError(f"{env_name} must be true or false")


if __name__ == "__main__":
    raise SystemExit(main())
