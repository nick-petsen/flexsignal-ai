#!/usr/bin/env python3
"""Read-only local customer pilot signal match preview."""

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
LOAD_COLUMNS = ("load_mwh",)
GENERATION_COLUMNS = ("generation_mwh",)
FLEXIBILITY_COLUMNS = ("flexible_capacity_mw", "flexible_energy_mwh")
DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH = (
    "frontend/src/data/public-surplus-risk-backtest-snapshot.json"
)
DEFAULT_MIN_MATCH_ROWS = 1
DEFAULT_DRY_RUN = "true"
SAFETY_BOUNDARY = (
    "read-only signal matching only",
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


class CustomerPilotSignalMatchError(RuntimeError):
    """Expected safe-fail error for customer pilot signal matching."""


@dataclass(frozen=True)
class CustomerPilotSignalMatchConfig:
    input_path: Path
    snapshot_path: Path
    price_area: str | None
    min_match_rows: int
    dry_run: bool


@dataclass(frozen=True)
class CustomerPilotRow:
    price_area: str
    timestamp_utc: datetime
    values: Mapping[str, str]


@dataclass(frozen=True)
class CustomerPilotSignalMatchSummary:
    status: str
    customer_price_areas_detected: tuple[str, ...]
    total_customer_rows: int
    matched_window_count: int
    matched_customer_rows: int
    candidate_windows: tuple[Mapping[str, Any], ...]
    warnings: tuple[str, ...]
    safety_boundary: tuple[str, ...]
    errors: tuple[str, ...]
    dry_run: bool
    file_written: bool = False
    database_write_performed: bool = False
    external_api_calls_performed: bool = False
    customer_specific_savings_calculated: bool = False
    profit_revenue_calculated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "customer_price_areas_detected": list(
                self.customer_price_areas_detected
            ),
            "total_customer_rows": self.total_customer_rows,
            "matched_window_count": self.matched_window_count,
            "matched_customer_rows": self.matched_customer_rows,
            "candidate_windows": list(self.candidate_windows),
            "warnings": list(self.warnings),
            "safety_boundary": list(self.safety_boundary),
            "errors": list(self.errors),
            "dry_run": self.dry_run,
            "file_written": self.file_written,
            "database_write_performed": self.database_write_performed,
            "external_api_calls_performed": self.external_api_calls_performed,
            "customer_specific_savings_calculated": (
                self.customer_specific_savings_calculated
            ),
            "profit_revenue_calculated": self.profit_revenue_calculated,
        }


def load_config(
    env: Mapping[str, str] | None = None,
) -> CustomerPilotSignalMatchConfig:
    safe_env = os.environ if env is None else env
    raw_input_path = safe_env.get("CUSTOMER_PILOT_INPUT_PATH")
    if raw_input_path is None or not raw_input_path.strip():
        raise CustomerPilotSignalMatchError("CUSTOMER_PILOT_INPUT_PATH is required")

    raw_price_area = safe_env.get("CUSTOMER_PILOT_PRICE_AREA")
    price_area = raw_price_area.strip() if raw_price_area else None
    if price_area == "":
        price_area = None
    if price_area is not None and price_area not in ALLOWED_PRICE_AREAS:
        raise CustomerPilotSignalMatchError(
            "CUSTOMER_PILOT_PRICE_AREA must be DK1 or DK2"
        )

    snapshot_path = (
        safe_env.get(
            "PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH",
            DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH,
        ).strip()
        or DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH
    )

    return CustomerPilotSignalMatchConfig(
        input_path=Path(raw_input_path).expanduser(),
        snapshot_path=Path(snapshot_path).expanduser(),
        price_area=price_area,
        min_match_rows=_parse_positive_int(
            safe_env.get(
                "CUSTOMER_PILOT_MIN_MATCH_ROWS",
                str(DEFAULT_MIN_MATCH_ROWS),
            ),
            "CUSTOMER_PILOT_MIN_MATCH_ROWS",
        ),
        dry_run=_parse_bool(
            safe_env.get("CUSTOMER_PILOT_DRY_RUN", DEFAULT_DRY_RUN),
            "CUSTOMER_PILOT_DRY_RUN",
        ),
    )


def match_customer_pilot_signal(
    config: CustomerPilotSignalMatchConfig,
) -> CustomerPilotSignalMatchSummary:
    warnings: list[str] = []
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
            candidate_windows=(),
            warnings=warnings,
            errors=errors,
        )

    try:
        snapshot = _read_snapshot(config.snapshot_path)
        public_windows = _public_windows_by_price_area(snapshot)
        customer_rows, detected_price_areas = _parse_customer_rows(raw_rows)
    except (OSError, json.JSONDecodeError, CustomerPilotSignalMatchError) as exc:
        errors.append(str(exc))
        return _build_summary(
            config=config,
            status="invalid",
            customer_price_areas_detected=(),
            total_customer_rows=len(raw_rows),
            candidate_windows=(),
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

    filtered_rows = [
        row for row in customer_rows if row.price_area in set(active_price_areas)
    ]
    candidate_windows = _candidate_windows(
        customer_rows=filtered_rows,
        public_windows=public_windows,
        columns=detected_columns,
    )
    matched_customer_rows = sum(
        int(window["customer_rows_in_window"]) for window in candidate_windows
    )

    if matched_customer_rows and matched_customer_rows < config.min_match_rows:
        warnings.append(
            "Matched customer row count is below CUSTOMER_PILOT_MIN_MATCH_ROWS."
        )

    if candidate_windows and any(
        window["match_status"] == "matched_but_customer_data_limited"
        for window in candidate_windows
    ):
        warnings.append(
            "Matched public risk windows have limited customer load, generation, "
            "or flexibility data."
        )

    if not candidate_windows:
        status = "no_matches"
    elif warnings:
        status = "matched_with_warnings"
    else:
        status = "matched"

    return _build_summary(
        config=config,
        status=status,
        customer_price_areas_detected=detected_price_areas,
        total_customer_rows=len(raw_rows),
        candidate_windows=tuple(candidate_windows),
        warnings=warnings,
        errors=errors,
    )


def print_summary(summary: CustomerPilotSignalMatchSummary) -> None:
    print("Customer pilot signal match summary")
    print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))


def main() -> int:
    try:
        config = load_config()
        summary = match_customer_pilot_signal(config)
    except CustomerPilotSignalMatchError as exc:
        summary = CustomerPilotSignalMatchSummary(
            status="invalid",
            customer_price_areas_detected=(),
            total_customer_rows=0,
            matched_window_count=0,
            matched_customer_rows=0,
            candidate_windows=(),
            warnings=(),
            safety_boundary=SAFETY_BOUNDARY,
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
        raise CustomerPilotSignalMatchError("Public surplus-risk snapshot is invalid.")
    if "top_risk_windows" not in snapshot:
        raise CustomerPilotSignalMatchError(
            "Public surplus-risk snapshot is missing top_risk_windows."
        )
    return snapshot


def _public_windows_by_price_area(
    snapshot: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    raw_windows = snapshot.get("top_risk_windows")
    if not isinstance(raw_windows, dict):
        raise CustomerPilotSignalMatchError(
            "Public surplus-risk snapshot top_risk_windows is invalid."
        )

    public_windows: dict[str, list[dict[str, Any]]] = {"DK1": [], "DK2": []}
    for price_area in ALLOWED_PRICE_AREAS:
        area_windows = raw_windows.get(price_area, [])
        if not isinstance(area_windows, list):
            raise CustomerPilotSignalMatchError(
                f"Public surplus-risk windows for {price_area} are invalid."
            )
        for raw_window in area_windows:
            if not isinstance(raw_window, dict):
                raise CustomerPilotSignalMatchError(
                    f"Public surplus-risk window for {price_area} is invalid."
                )
            try:
                start = _parse_public_timestamp(str(raw_window["start"]))
                end = _parse_public_timestamp(str(raw_window["end"]))
            except (KeyError, ValueError) as exc:
                raise CustomerPilotSignalMatchError(
                    f"Public surplus-risk window for {price_area} has invalid timestamps."
                ) from exc
            public_windows[price_area].append(
                {
                    "price_area": price_area,
                    "start": start,
                    "end": end,
                    "duration_hours": raw_window.get("duration_hours"),
                    "score": raw_window.get("score"),
                    "level": raw_window.get("level"),
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
        except CustomerPilotSignalMatchError:
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
        raise CustomerPilotSignalMatchError(
            "Customer timestamps could not be parsed safely; invalid row count: "
            f"{timestamp_errors}."
        )

    return customer_rows, tuple(sorted(detected_price_areas))


def _candidate_windows(
    *,
    customer_rows: Sequence[CustomerPilotRow],
    public_windows: Mapping[str, Sequence[Mapping[str, Any]]],
    columns: Sequence[str],
) -> list[dict[str, Any]]:
    candidate_windows: list[dict[str, Any]] = []
    column_set = set(columns)
    has_availability_column = "availability_flag" in column_set
    has_note_column = "operational_note" in column_set

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

            has_load = _has_any_data(matched_rows, LOAD_COLUMNS)
            has_generation = _has_any_data(matched_rows, GENERATION_COLUMNS)
            has_flexibility = _has_any_data(matched_rows, FLEXIBILITY_COLUMNS)
            candidate_window: dict[str, Any] = {
                "price_area": price_area,
                "public_window_start": _format_utc(start),
                "public_window_end": _format_utc(end),
                "public_window_duration_hours": public_window.get(
                    "duration_hours"
                ),
                "public_risk_score": public_window.get("score"),
                "public_risk_level": public_window.get("level"),
                "customer_rows_in_window": len(matched_rows),
                "customer_has_load_data": has_load,
                "customer_has_generation_data": has_generation,
                "customer_has_flexibility_data": has_flexibility,
                "match_status": (
                    "candidate_for_human_review"
                    if has_load or has_generation or has_flexibility
                    else "matched_but_customer_data_limited"
                ),
            }
            if has_availability_column:
                candidate_window["availability_rows_true"] = sum(
                    1
                    for row in matched_rows
                    if _parse_availability_flag(
                        row.values.get("availability_flag", "")
                    )
                )
            if has_note_column:
                candidate_window["notes_present_count"] = sum(
                    1
                    for row in matched_rows
                    if bool(row.values.get("operational_note", "").strip())
                )
            candidate_windows.append(candidate_window)

    return candidate_windows


def _active_price_areas(
    configured_price_area: str | None,
    detected_price_areas: Sequence[str],
) -> tuple[str, ...]:
    if configured_price_area is not None:
        return (configured_price_area,)
    return tuple(price_area for price_area in detected_price_areas if price_area)


def _has_any_data(
    rows: Sequence[CustomerPilotRow],
    columns: Sequence[str],
) -> bool:
    return any(
        bool(row.values.get(column, "").strip())
        for row in rows
        for column in columns
    )


def _parse_customer_timestamp(raw_timestamp: str, raw_timezone: str) -> datetime:
    normalized_timestamp = raw_timestamp.strip().replace("Z", "+00:00")
    if not normalized_timestamp:
        raise CustomerPilotSignalMatchError("timestamp is required")
    try:
        parsed = datetime.fromisoformat(normalized_timestamp)
    except ValueError as exc:
        raise CustomerPilotSignalMatchError("timestamp is invalid") from exc

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
        raise CustomerPilotSignalMatchError("timezone is required")
    try:
        return ZoneInfo(normalized_timezone)
    except ZoneInfoNotFoundError as exc:
        raise CustomerPilotSignalMatchError("timezone is invalid") from exc


def _parse_availability_flag(raw_value: str) -> bool:
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on", "available"}


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_summary(
    *,
    config: CustomerPilotSignalMatchConfig,
    status: str,
    customer_price_areas_detected: tuple[str, ...],
    total_customer_rows: int,
    candidate_windows: tuple[Mapping[str, Any], ...],
    warnings: list[str],
    errors: list[str],
) -> CustomerPilotSignalMatchSummary:
    return CustomerPilotSignalMatchSummary(
        status=status,
        customer_price_areas_detected=customer_price_areas_detected,
        total_customer_rows=total_customer_rows,
        matched_window_count=len(candidate_windows),
        matched_customer_rows=sum(
            int(window["customer_rows_in_window"]) for window in candidate_windows
        ),
        candidate_windows=candidate_windows,
        warnings=tuple(warnings),
        safety_boundary=SAFETY_BOUNDARY,
        errors=tuple(errors),
        dry_run=config.dry_run,
    )


def _invalid_summary(
    config: CustomerPilotSignalMatchConfig,
    warnings: list[str],
    errors: list[str],
) -> CustomerPilotSignalMatchSummary:
    return _build_summary(
        config=config,
        status="invalid",
        customer_price_areas_detected=(),
        total_customer_rows=0,
        candidate_windows=(),
        warnings=warnings,
        errors=errors,
    )


def _parse_bool(raw_value: str | None, env_name: str) -> bool:
    normalized = (raw_value or "").strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise CustomerPilotSignalMatchError(f"{env_name} must be true or false")


def _parse_positive_int(raw_value: str | None, env_name: str) -> int:
    try:
        parsed = int((raw_value or "").strip())
    except ValueError as exc:
        raise CustomerPilotSignalMatchError(
            f"{env_name} must be a positive integer"
        ) from exc

    if parsed < 1:
        raise CustomerPilotSignalMatchError(
            f"{env_name} must be a positive integer"
        )
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
