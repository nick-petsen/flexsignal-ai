from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from app.db.repositories.eds_records import (
    DAY_AHEAD_PRICES_DATASET,
    ELECTRICITY_PRODEX_5MIN_REALTIME_DATASET,
)
from app.db.sql_builder import build_eds_write_plan_entry_upsert_sql
from app.db.write_plan import build_eds_write_plan


SUPPORTED_DATASETS = {
    DAY_AHEAD_PRICES_DATASET,
    ELECTRICITY_PRODEX_5MIN_REALTIME_DATASET,
}

SqlCommand = dict[str, Any]
SqlCommandExecutor = Callable[[list[SqlCommand]], Any]


def run_eds_persistence_dry_run(
    *,
    dataset: str,
    normalized_records: Iterable[Mapping[str, Any]],
    executor: SqlCommandExecutor | None = None,
) -> dict[str, Any]:
    """Build an EDS persistence preview and optionally submit it to a fake executor.

    This is a dry-run/test-only orchestration helper. It does not create database
    connections, read environment variables, perform HTTP requests, or integrate
    with application startup.
    """
    _validate_dataset(dataset)
    records = _validated_records(normalized_records)

    write_plan = build_eds_write_plan(
        dataset=dataset,
        normalized_records=records,
    )
    sql_commands = [
        build_eds_write_plan_entry_upsert_sql(write_plan_entry)
        for write_plan_entry in write_plan
    ]

    preview_only = executor is None
    executed_count = 0
    if executor is not None:
        executor(sql_commands)
        executed_count = len(sql_commands)

    return {
        "dataset": dataset,
        "write_plan_count": len(write_plan),
        "sql_command_count": len(sql_commands),
        "executed_count": executed_count,
        "preview_only": preview_only,
        "tables": sorted({sql_command["table"] for sql_command in sql_commands}),
        "write_plan": write_plan,
        "sql_commands": sql_commands,
    }


def _validate_dataset(dataset: str) -> None:
    if dataset not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported Energi Data Service dataset: {dataset}")


def _validated_records(
    normalized_records: Iterable[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    records = list(normalized_records)
    for normalized_record in records:
        if not isinstance(normalized_record, Mapping):
            raise ValueError("Malformed normalized EDS record")

    return records
