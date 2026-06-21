from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "energy_freshness_db_smoke.py"


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "energy_freshness_db_smoke",
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
    monkeypatch.setattr("sys.argv", ["energy_freshness_db_smoke.py", *argv])

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
    assert payload["price_area"] == "DK1"
    assert payload["dry_run"] is True
    assert payload["execute_requested"] is False
    assert payload["database_query_executed"] is False
    assert payload["database_write_performed"] is False
    assert payload["requires_database_url"] is False
    assert "freshness_plan" in payload


def test_dry_run_does_not_connect_or_execute_sql(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code, payload, _ = _run_main(
        monkeypatch,
        capsys,
        ["--price-area", "DK2", "--pretty"],
    )

    assert exit_code == 0
    assert payload["price_area"] == "DK2"
    assert payload["database_query_executed"] is False
    assert payload["warnings"] == [
        "dry-run only; no database connection opened and no SQL executed"
    ]


def test_execute_without_database_url_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code, payload, _ = _run_main(monkeypatch, capsys, ["--execute"])

    assert exit_code == 2
    assert payload["execute_requested"] is True
    assert payload["database_query_executed"] is False
    assert payload["database_write_performed"] is False
    assert "database URL is required" in payload["warnings"][0]


def test_remote_database_url_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    raw_url = "postgresql://remote.example.com/flexsignal_ai"
    exit_code, payload, output = _run_main(
        monkeypatch,
        capsys,
        ["--execute", "--database-url", raw_url],
    )

    assert exit_code == 2
    assert payload["database_query_executed"] is False
    assert payload["database_write_performed"] is False
    assert payload["warnings"] == ["refusing non-local database URL"]
    assert raw_url not in output


def test_local_database_url_validation_accepts_local_urls() -> None:
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


def test_invalid_price_area_is_rejected() -> None:
    module = _load_script_module()

    with pytest.raises(SystemExit) as exc_info:
        module.build_parser().parse_args(["--price-area", "SE3"])

    assert exc_info.value.code == 2


def test_script_does_not_add_runtime_integration_paths() -> None:
    forbidden_terms = [
        "Fast" + "API",
        "API" + "Router",
        "api.energi" + "dataservice",
        "D" + "MI",
        "sched" + "uler",
        "Az" + "ure",
        "dispatch",
        "activation",
        "control",
    ]
    source = SCRIPT_PATH.read_text(encoding="utf-8")

    for term in forbidden_terms:
        assert term not in source
