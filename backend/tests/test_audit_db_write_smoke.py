from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_db_write_smoke.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(
        "audit_db_write_smoke",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_main(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> tuple[int, dict[str, object], str]:
    module = _load_script_module()
    monkeypatch.setattr(
        module,
        "connect_with_psycopg",
        lambda _: pytest.fail("dry-run path must not connect to a database"),
    )
    monkeypatch.setattr("sys.argv", ["audit_db_write_smoke.py", *argv])

    exit_code = module.main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    return exit_code, payload, captured.out + captured.err


def test_dry_run_does_not_require_database_url(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code, payload, _ = _run_main(monkeypatch, capsys, [])

    assert exit_code == 0
    assert payload["dry_run"] is True
    assert payload["execute_requested"] is False
    assert payload["database_write_performed"] is False
    assert payload["inserted_attempts"] == 0


def test_execute_without_database_url_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code, payload, _ = _run_main(monkeypatch, capsys, ["--execute"])

    assert exit_code == 2
    assert payload["execute_requested"] is True
    assert payload["database_write_performed"] is False
    assert "database URL is required" in payload["warnings"][0]


def test_remote_database_url_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code, payload, output = _run_main(
        monkeypatch,
        capsys,
        [
            "--execute",
            "--database-url",
            "postgresql://remote.example.com/flexsignal_ai",
        ],
    )

    assert exit_code == 2
    assert payload["database_write_performed"] is False
    assert payload["warnings"] == ["refusing non-local database URL"]
    assert "postgresql://remote.example.com/flexsignal_ai" not in output


def test_local_database_url_validation_accepts_loopback_hosts() -> None:
    module = _load_script_module()

    assert (
        module.validate_local_database_url("postgresql://localhost/flexsignal_ai")
        == "localhost"
    )
    assert (
        module.validate_local_database_url("postgresql://127.0.0.1/flexsignal_ai")
        == "127.0.0.1"
    )
    assert (
        module.validate_local_database_url("postgresql:///flexsignal_ai")
        == "local"
    )


def test_output_does_not_include_raw_database_url(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    raw_url = "postgresql://localhost/flexsignal_ai"
    exit_code, payload, output = _run_main(
        monkeypatch,
        capsys,
        ["--database-url", raw_url],
    )

    assert exit_code == 0
    assert payload["dry_run"] is True
    assert raw_url not in output


def test_event_id_is_deterministic() -> None:
    module = _load_script_module()

    first = module.build_smoke_event("report_pdf_exported")
    second = module.build_smoke_event("report_pdf_exported")

    assert first["event_id"] == second["event_id"]
    assert first["event_id"].startswith("audit_evt_")


def test_script_and_repository_do_not_add_runtime_integration_paths() -> None:
    forbidden_terms = [
        "Fast" + "API",
        "API" + "Router",
        "api.energi" + "dataservice",
        "D" + "MI",
        "report" + "lab",
        "weasy" + "print",
        "sched" + "uler",
        "Az" + "ure",
        "dispatch",
        "activation",
        "control",
    ]
    source_paths = [
        SCRIPT_PATH,
        REPO_ROOT / "backend" / "app" / "audit" / "repository.py",
    ]

    for source_path in source_paths:
        source = source_path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            assert term not in source
