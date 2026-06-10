from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script_module(script_name: str) -> ModuleType:
    module_path = REPO_ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(script_name.removesuffix(".py"), module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


manual_eds_local_db_ingest = load_script_module("manual_eds_local_db_ingest.py")
manual_eds_historical_batch_import = load_script_module(
    "manual_eds_historical_batch_import.py"
)


def test_manual_eds_local_limit_50_is_accepted_and_dry_run_remains_default() -> None:
    args = manual_eds_local_db_ingest.build_parser().parse_args(
        [
            "--dataset",
            "DayAheadPrices",
            "--price-area",
            "DK1",
            "--limit",
            "50",
        ]
    )

    assert args.limit == 50
    assert args.confirm_local_db_write is False


@pytest.mark.parametrize("limit", ["0", "51"])
def test_manual_eds_local_invalid_limits_are_rejected(limit: str) -> None:
    with pytest.raises(SystemExit) as exc_info:
        manual_eds_local_db_ingest.build_parser().parse_args(
            [
                "--dataset",
                "DayAheadPrices",
                "--price-area",
                "DK1",
                "--limit",
                limit,
            ]
        )

    assert exc_info.value.code == 2


def test_manual_eds_local_default_limit_remains_conservative() -> None:
    args = manual_eds_local_db_ingest.build_parser().parse_args(
        ["--dataset", "DayAheadPrices", "--price-area", "DK1"]
    )

    assert args.limit == 2
    assert args.confirm_local_db_write is False


def test_manual_eds_local_rejects_non_local_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.com/flexsignal_ai")

    with pytest.raises(ValueError, match="localhost or 127.0.0.1"):
        manual_eds_local_db_ingest.require_local_database_url()


def test_historical_wrapper_limit_50_is_accepted_and_dry_run_remains_default() -> None:
    args = manual_eds_historical_batch_import.build_parser().parse_args(["--limit", "50"])

    assert args.limit == 50
    assert args.confirm_local_db_write is False


@pytest.mark.parametrize("limit", ["0", "51"])
def test_historical_wrapper_invalid_limits_are_rejected(limit: str) -> None:
    with pytest.raises(SystemExit) as exc_info:
        manual_eds_historical_batch_import.build_parser().parse_args(["--limit", limit])

    assert exc_info.value.code == 2


def test_historical_wrapper_default_limit_remains_10() -> None:
    args = manual_eds_historical_batch_import.build_parser().parse_args([])

    assert args.limit == 10
    assert args.confirm_local_db_write is False


def test_historical_wrapper_confirm_flag_passthrough_is_explicit_only() -> None:
    dry_run_commands = manual_eds_historical_batch_import.build_child_commands(
        datasets=["DayAheadPrices"],
        price_areas=["DK1"],
        limit=50,
        confirmed_local_write=False,
    )
    confirmed_commands = manual_eds_historical_batch_import.build_child_commands(
        datasets=["DayAheadPrices"],
        price_areas=["DK1"],
        limit=50,
        confirmed_local_write=True,
    )

    assert manual_eds_historical_batch_import.CONFIRM_FLAG not in dry_run_commands[0]
    assert manual_eds_historical_batch_import.CONFIRM_FLAG in confirmed_commands[0]


def test_historical_wrapper_rejects_non_local_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://example.com/flexsignal_ai")

    with pytest.raises(ValueError, match="localhost or 127.0.0.1"):
        manual_eds_historical_batch_import.require_local_database_url()


def test_historical_wrapper_limit_50_dry_run_does_not_pass_confirm_or_call_live_eds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded_commands: list[list[str]] = []

    def fake_run(command: list[str], *, check: bool) -> subprocess.CompletedProcess[str]:
        assert check is False
        recorded_commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/flexsignal_ai")
    monkeypatch.setattr(manual_eds_historical_batch_import.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "manual_eds_historical_batch_import.py",
            "--dataset",
            "DayAheadPrices",
            "--price-area",
            "DK1",
            "--limit",
            "50",
        ],
    )

    assert manual_eds_historical_batch_import.main() == 0
    assert len(recorded_commands) == 1
    assert "--limit" in recorded_commands[0]
    assert "50" in recorded_commands[0]
    assert manual_eds_historical_batch_import.CONFIRM_FLAG not in recorded_commands[0]
