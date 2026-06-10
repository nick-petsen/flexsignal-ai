#!/usr/bin/env python3
"""Manual local batch wrapper for EDS local DB ingest validation."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


ALLOWED_LOCAL_HOSTS = {"localhost", "127.0.0.1"}
CONFIRM_FLAG = "--confirm-local-db-write"
DATASETS = ("DayAheadPrices", "ElectricityProdex5MinRealtime")
PRICE_AREAS = ("DK1", "DK2")
DEFAULT_LIMIT = 10
HARD_MAX_LIMIT = 10
CHILD_SCRIPT = Path(__file__).resolve().with_name("manual_eds_local_db_ingest.py")


def limited_positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc

    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")

    if parsed > HARD_MAX_LIMIT:
        raise argparse.ArgumentTypeError(f"must be no greater than {HARD_MAX_LIMIT}")

    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Manually run supported Energi Data Service local DB ingest "
            "validation combinations. Dry-run is the default; local database "
            f"writes require {CONFIRM_FLAG}."
        )
    )
    parser.add_argument(
        "--price-area",
        choices=(*PRICE_AREAS, "all"),
        default="all",
        help="Price area to run, or all DK1/DK2 areas. Default: all.",
    )
    parser.add_argument(
        "--dataset",
        choices=(*DATASETS, "all"),
        default="all",
        help="Dataset to run, or all supported datasets. Default: all.",
    )
    parser.add_argument(
        "--limit",
        type=limited_positive_int,
        default=DEFAULT_LIMIT,
        help=(
            "Maximum records to request per child command. "
            f"Default: {DEFAULT_LIMIT}. Hard maximum: {HARD_MAX_LIMIT}."
        ),
    )
    parser.add_argument(
        CONFIRM_FLAG,
        action="store_true",
        help=(
            "Pass write confirmation through to child ingest commands. Without "
            "this flag, child commands remain dry-run only."
        ),
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue running remaining child commands after a child failure.",
    )
    return parser


def require_local_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is required")

    parsed = urlparse(database_url)
    if parsed.scheme != "postgresql":
        raise ValueError(
            "DATABASE_URL must use DB-API format, for example "
            "postgresql://localhost/flexsignal_ai"
        )

    host = parsed.hostname
    if host not in ALLOWED_LOCAL_HOSTS:
        raise ValueError(
            "Refusing to run: DATABASE_URL host must be localhost or 127.0.0.1"
        )

    return database_url


def selected_values(selected: str, supported_values: tuple[str, ...]) -> list[str]:
    if selected == "all":
        return list(supported_values)
    return [selected]


def build_child_commands(
    *,
    datasets: list[str],
    price_areas: list[str],
    limit: int,
    confirmed_local_write: bool,
) -> list[list[str]]:
    commands: list[list[str]] = []
    for dataset in datasets:
        for price_area in price_areas:
            command = [
                sys.executable,
                str(CHILD_SCRIPT),
                "--dataset",
                dataset,
                "--price-area",
                price_area,
                "--limit",
                str(limit),
            ]
            if confirmed_local_write:
                command.append(CONFIRM_FLAG)
            commands.append(command)
    return commands


def print_warning(*, confirmed_local_write: bool) -> None:
    mode = "CONFIRMED LOCAL WRITE" if confirmed_local_write else "DRY-RUN"
    print(
        "WARNING: Manual local developer validation only. "
        f"Mode: {mode}. This wrapper only invokes manual child scripts from a "
        "shell against a local PostgreSQL DATABASE_URL. It must not be used for "
        "production databases, schedulers, backend startup ingestion, FastAPI "
        "endpoints, frontend-triggered ingestion, forecasting automation, "
        "dispatch, activation, control workflows, or operational energy "
        "infrastructure."
    )


def print_command_plan(commands: list[list[str]]) -> None:
    print("Command plan:")
    for index, command in enumerate(commands, start=1):
        print(f"{index}. {shlex.join(command)}")


def print_json_summary(
    *,
    dry_run: bool,
    confirmed_local_write: bool,
    limit: int,
    price_areas: list[str],
    datasets: list[str],
    commands_planned: int,
    commands_succeeded: int,
    commands_failed: int,
    child_exit_codes: list[int],
) -> None:
    summary = {
        "dry_run": dry_run,
        "confirmed_local_write": confirmed_local_write,
        "limit": limit,
        "price_areas": price_areas,
        "datasets": datasets,
        "commands_planned": commands_planned,
        "commands_succeeded": commands_succeeded,
        "commands_failed": commands_failed,
        "child_exit_codes": child_exit_codes,
        "decision_support_only": True,
        "local_only": True,
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    confirmed_local_write = bool(args.confirm_local_db_write)
    dry_run = not confirmed_local_write
    datasets = selected_values(args.dataset, DATASETS)
    price_areas = selected_values(args.price_area, PRICE_AREAS)
    commands = build_child_commands(
        datasets=datasets,
        price_areas=price_areas,
        limit=args.limit,
        confirmed_local_write=confirmed_local_write,
    )

    try:
        require_local_database_url()
    except ValueError as exc:
        print(f"Configuration failed: {exc}", file=sys.stderr)
        return 2

    print_warning(confirmed_local_write=confirmed_local_write)
    print_command_plan(commands)

    commands_succeeded = 0
    commands_failed = 0
    child_exit_codes: list[int] = []

    for index, command in enumerate(commands, start=1):
        print(f"Running child command {index}/{len(commands)}")
        completed = subprocess.run(command, check=False)
        child_exit_codes.append(completed.returncode)

        if completed.returncode == 0:
            commands_succeeded += 1
            continue

        commands_failed += 1
        if not args.continue_on_error:
            print(
                "Stopping after first failed child command. Pass "
                "--continue-on-error to run remaining planned commands.",
                file=sys.stderr,
            )
            break

    print_json_summary(
        dry_run=dry_run,
        confirmed_local_write=confirmed_local_write,
        limit=args.limit,
        price_areas=price_areas,
        datasets=datasets,
        commands_planned=len(commands),
        commands_succeeded=commands_succeeded,
        commands_failed=commands_failed,
        child_exit_codes=child_exit_codes,
    )

    return 1 if commands_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
