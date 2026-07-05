#!/usr/bin/env python3
"""Read-only local customer pilot intake CSV validator."""

from __future__ import annotations

import csv
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


COMMON_REQUIRED_COLUMNS = (
    "site_id",
    "price_area",
    "timestamp",
    "timezone",
)
ALLOWED_PRICE_AREAS = frozenset({"DK1", "DK2"})
ALLOWED_CUSTOMER_TYPES = frozenset(
    {"common", "producer", "flexible_consumption", "grid_dso"}
)
ENERGY_COLUMNS = (
    "load_mwh",
    "generation_mwh",
    "flexible_energy_mwh",
)
FLEXIBILITY_COLUMNS = (
    "flexible_capacity_mw",
    "flexible_energy_mwh",
)
SECRET_LIKE_COLUMN_MARKERS = (
    "password",
    "token",
    "api_key",
    "secret",
    "connection_string",
)
PRODUCER_RECOMMENDED_COLUMNS = (
    "asset_type",
    "installed_capacity_mw",
    "generation_mwh",
    "grid_export_limit_mw",
    "curtailment_event",
)
FLEXIBLE_CONSUMPTION_RECOMMENDED_COLUMNS = (
    "load_mwh",
    "flexible_load_mw",
    "shiftable_energy_mwh",
    "minimum_runtime",
    "maximum_runtime",
    "lead_time_minutes",
)
GRID_DSO_RECOMMENDED_COLUMNS = (
    "aggregated_load_mwh",
    "aggregated_generation_mwh",
    "grid_capacity_mw",
)
SAFETY_BOUNDARY = (
    "read-only validation only",
    "no customer-specific savings calculated",
    "no automatic control",
    "no dispatch",
    "no activation",
    "no live control signals",
    "no asset integration",
    "no database writes",
    "no external API calls",
)
DEFAULT_MIN_ROWS = 24
DEFAULT_DRY_RUN = "true"
TIMESTAMP_SAMPLE_LIMIT = 50


class CustomerPilotIntakeValidationError(RuntimeError):
    """Expected safe-fail error for customer pilot intake validation."""


@dataclass(frozen=True)
class CustomerPilotIntakeConfig:
    input_path: Path
    customer_type: str
    min_rows: int
    dry_run: bool


@dataclass(frozen=True)
class CustomerPilotIntakeSummary:
    status: str
    row_count: int
    detected_columns: tuple[str, ...]
    missing_required_columns: tuple[str, ...]
    warnings: tuple[str, ...]
    safety_boundary: tuple[str, ...]
    errors: tuple[str, ...]
    customer_type: str
    min_rows: int
    dry_run: bool
    file_written: bool = False
    database_write_performed: bool = False
    external_api_calls_performed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "row_count": self.row_count,
            "detected_columns": list(self.detected_columns),
            "missing_required_columns": list(self.missing_required_columns),
            "warnings": list(self.warnings),
            "safety_boundary": list(self.safety_boundary),
            "errors": list(self.errors),
            "customer_type": self.customer_type,
            "min_rows": self.min_rows,
            "dry_run": self.dry_run,
            "file_written": self.file_written,
            "database_write_performed": self.database_write_performed,
            "external_api_calls_performed": self.external_api_calls_performed,
        }


def load_config(env: Mapping[str, str] | None = None) -> CustomerPilotIntakeConfig:
    safe_env = os.environ if env is None else env
    raw_input_path = safe_env.get("CUSTOMER_PILOT_INPUT_PATH")
    if raw_input_path is None or not raw_input_path.strip():
        raise CustomerPilotIntakeValidationError(
            "CUSTOMER_PILOT_INPUT_PATH is required"
        )

    customer_type = (
        safe_env.get("CUSTOMER_PILOT_CUSTOMER_TYPE", "common").strip() or "common"
    )
    if customer_type not in ALLOWED_CUSTOMER_TYPES:
        raise CustomerPilotIntakeValidationError(
            "CUSTOMER_PILOT_CUSTOMER_TYPE must be one of: common, producer, "
            "flexible_consumption, grid_dso"
        )

    min_rows = _parse_positive_int(
        safe_env.get("CUSTOMER_PILOT_MIN_ROWS", str(DEFAULT_MIN_ROWS)),
        "CUSTOMER_PILOT_MIN_ROWS",
    )
    dry_run = _parse_bool(
        safe_env.get("CUSTOMER_PILOT_DRY_RUN", DEFAULT_DRY_RUN),
        "CUSTOMER_PILOT_DRY_RUN",
    )

    return CustomerPilotIntakeConfig(
        input_path=Path(raw_input_path).expanduser(),
        customer_type=customer_type,
        min_rows=min_rows,
        dry_run=dry_run,
    )


def validate_customer_pilot_intake(
    config: CustomerPilotIntakeConfig,
) -> CustomerPilotIntakeSummary:
    errors: list[str] = []
    warnings: list[str] = []
    detected_columns: tuple[str, ...] = ()
    missing_required_columns: tuple[str, ...] = ()
    row_count = 0

    if not config.input_path.exists() or not config.input_path.is_file():
        errors.append("Input file does not exist or is not a readable file.")
        return _build_summary(config, row_count, detected_columns, (), warnings, errors)

    if config.input_path.suffix.lower() != ".csv":
        errors.append("Only CSV input files are accepted for v0.")
        return _build_summary(config, row_count, detected_columns, (), warnings, errors)

    try:
        detected_columns, rows = _read_csv(config.input_path)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        errors.append(f"CSV could not be parsed: {exc.__class__.__name__}.")
        return _build_summary(config, row_count, detected_columns, (), warnings, errors)

    row_count = len(rows)
    column_set = set(detected_columns)
    missing_required_columns = tuple(
        column for column in COMMON_REQUIRED_COLUMNS if column not in column_set
    )
    if missing_required_columns:
        errors.append("Required common columns are missing.")

    if row_count < config.min_rows:
        errors.append("CSV row count is below CUSTOMER_PILOT_MIN_ROWS.")

    if not any(column in column_set for column in ENERGY_COLUMNS):
        errors.append(
            "At least one relevant energy column is required: "
            "load_mwh, generation_mwh, or flexible_energy_mwh."
        )

    if not any(column in column_set for column in FLEXIBILITY_COLUMNS):
        warnings.append(
            "At least one flexibility column is recommended: "
            "flexible_capacity_mw or flexible_energy_mwh."
        )

    warnings.extend(_secret_like_column_warnings(detected_columns))
    warnings.extend(_customer_type_warnings(config.customer_type, column_set))

    if "price_area" in column_set:
        invalid_price_area_rows = _invalid_price_area_rows(rows)
        if invalid_price_area_rows:
            errors.append(
                "price_area values must be DK1 or DK2; invalid row count: "
                f"{len(invalid_price_area_rows)}."
            )

    if "timestamp" in column_set:
        invalid_timestamp_rows = _invalid_timestamp_rows(rows)
        if invalid_timestamp_rows:
            errors.append(
                "timestamp must be non-empty and parseable for sampled rows; "
                f"invalid sampled row count: {len(invalid_timestamp_rows)}."
            )

    if "timezone" in column_set:
        missing_timezone_rows = _missing_timezone_rows(rows)
        if missing_timezone_rows:
            errors.append(
                "timezone must be present for sampled rows; missing sampled row "
                f"count: {len(missing_timezone_rows)}."
            )

    return _build_summary(
        config,
        row_count,
        detected_columns,
        missing_required_columns,
        warnings,
        errors,
    )


def print_summary(summary: CustomerPilotIntakeSummary) -> None:
    print("Customer pilot intake validation summary")
    print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))


def main() -> int:
    try:
        config = load_config()
        summary = validate_customer_pilot_intake(config)
    except CustomerPilotIntakeValidationError as exc:
        summary = CustomerPilotIntakeSummary(
            status="invalid",
            row_count=0,
            detected_columns=(),
            missing_required_columns=(),
            warnings=(),
            safety_boundary=SAFETY_BOUNDARY,
            errors=(str(exc),),
            customer_type="common",
            min_rows=DEFAULT_MIN_ROWS,
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
                    key.strip(): "" if value is None else str(value)
                    for key, value in row.items()
                }
            )
    return fieldnames, rows


def _build_summary(
    config: CustomerPilotIntakeConfig,
    row_count: int,
    detected_columns: tuple[str, ...],
    missing_required_columns: tuple[str, ...],
    warnings: list[str],
    errors: list[str],
) -> CustomerPilotIntakeSummary:
    if errors or missing_required_columns:
        status = "invalid"
    elif warnings:
        status = "valid_with_warnings"
    else:
        status = "valid"

    return CustomerPilotIntakeSummary(
        status=status,
        row_count=row_count,
        detected_columns=detected_columns,
        missing_required_columns=missing_required_columns,
        warnings=tuple(warnings),
        safety_boundary=SAFETY_BOUNDARY,
        errors=tuple(errors),
        customer_type=config.customer_type,
        min_rows=config.min_rows,
        dry_run=config.dry_run,
    )


def _invalid_price_area_rows(rows: list[dict[str, str]]) -> list[int]:
    invalid_rows = []
    for index, row in enumerate(rows, start=2):
        if row.get("price_area", "").strip() not in ALLOWED_PRICE_AREAS:
            invalid_rows.append(index)
    return invalid_rows


def _invalid_timestamp_rows(rows: list[dict[str, str]]) -> list[int]:
    invalid_rows = []
    for index, row in enumerate(rows[:TIMESTAMP_SAMPLE_LIMIT], start=2):
        raw_timestamp = row.get("timestamp", "").strip()
        if not raw_timestamp or not _is_parseable_timestamp(raw_timestamp):
            invalid_rows.append(index)
    return invalid_rows


def _missing_timezone_rows(rows: list[dict[str, str]]) -> list[int]:
    missing_rows = []
    for index, row in enumerate(rows[:TIMESTAMP_SAMPLE_LIMIT], start=2):
        if not row.get("timezone", "").strip():
            missing_rows.append(index)
    return missing_rows


def _is_parseable_timestamp(raw_timestamp: str) -> bool:
    normalized = raw_timestamp.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return True


def _secret_like_column_warnings(columns: tuple[str, ...]) -> list[str]:
    warnings = []
    for column in columns:
        normalized = column.lower()
        if any(marker in normalized for marker in SECRET_LIKE_COLUMN_MARKERS):
            warnings.append(
                f"Secret-like column detected and should be removed before pilot "
                f"analysis: {column}."
            )
    return warnings


def _customer_type_warnings(customer_type: str, column_set: set[str]) -> list[str]:
    if customer_type == "producer":
        return _missing_column_warnings(
            "producer",
            PRODUCER_RECOMMENDED_COLUMNS,
            column_set,
        )
    if customer_type == "flexible_consumption":
        return _missing_column_warnings(
            "flexible_consumption",
            FLEXIBLE_CONSUMPTION_RECOMMENDED_COLUMNS,
            column_set,
        )
    if customer_type == "grid_dso":
        warnings = _missing_column_warnings(
            "grid_dso",
            GRID_DSO_RECOMMENDED_COLUMNS,
            column_set,
        )
        if not ({"grid_area_id", "transformer_area_id"} & column_set):
            warnings.append(
                "grid_dso intake is missing one of: "
                "grid_area_id or transformer_area_id."
            )
        if not ({"congestion_event", "outage_or_constraint_note"} & column_set):
            warnings.append(
                "grid_dso intake is missing one of: congestion_event or "
                "outage_or_constraint_note."
            )
        return warnings
    return []


def _missing_column_warnings(
    label: str,
    recommended_columns: tuple[str, ...],
    column_set: set[str],
) -> list[str]:
    missing_columns = [
        column for column in recommended_columns if column not in column_set
    ]
    if not missing_columns:
        return []
    return [
        f"{label} intake is missing recommended columns: "
        f"{', '.join(missing_columns)}."
    ]


def _parse_bool(raw_value: str | None, env_name: str) -> bool:
    normalized = (raw_value or "").strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise CustomerPilotIntakeValidationError(f"{env_name} must be true or false")


def _parse_positive_int(raw_value: str | None, env_name: str) -> int:
    try:
        parsed = int((raw_value or "").strip())
    except ValueError as exc:
        raise CustomerPilotIntakeValidationError(
            f"{env_name} must be a positive integer"
        ) from exc

    if parsed < 1:
        raise CustomerPilotIntakeValidationError(
            f"{env_name} must be a positive integer"
        )
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
