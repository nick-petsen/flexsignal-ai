from __future__ import annotations

import importlib.util
import json
import urllib.error
from pathlib import Path
from types import ModuleType
from urllib.parse import urlparse

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "staging_smoke.py"


class FakeResponse:
    def __init__(self, payload: object, *, status: int = 200) -> None:
        self.status = status
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("staging_smoke", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def safe_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "decision_support_only": True,
        "human_review_required": True,
        "no_automatic_control": True,
        "no_dispatch": True,
        "no_activation": True,
    }
    payload.update(overrides)
    return payload


def test_staging_smoke_success_calls_expected_backend_paths_without_database_url(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = load_script_module()
    calls: list[tuple[str, str, dict[str, object] | None]] = []

    def fake_urlopen(request: object, *, timeout: int) -> FakeResponse:
        assert timeout == module.TIMEOUT_SECONDS
        method = getattr(request, "method")
        parsed = urlparse(getattr(request, "full_url"))
        body = getattr(request, "data", None)
        payload = json.loads(body.decode("utf-8")) if body else None
        calls.append((method, parsed.path, payload))

        if parsed.path == "/health":
            return FakeResponse({"status": "ok", "service": "flexsignal-ai-api"})
        if parsed.path == "/api/system/readiness":
            return FakeResponse(
                safe_payload(status="degraded", database_configured=False)
            )
        if parsed.path == "/api/dashboard/decision-summary/preview":
            assert payload is not None
            return FakeResponse(safe_payload(price_area=payload["price_area"]))
        pytest.fail(f"unexpected smoke path: {parsed.path}")

    exit_code = module.run_smoke(environ={}, opener=fake_urlopen)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert calls == [
        ("GET", "/health", None),
        ("GET", "/api/system/readiness", None),
        ("POST", "/api/dashboard/decision-summary/preview", {"price_area": "DK1"}),
        ("POST", "/api/dashboard/decision-summary/preview", {"price_area": "DK2"}),
    ]
    assert "DK1 decision summary: safe JSON" in captured.out
    assert "DK2 decision summary: safe JSON" in captured.out
    assert "DATABASE_URL" not in captured.out + captured.err


def test_staging_smoke_does_not_print_configured_backend_base_url(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = load_script_module()
    raw_base_url = "https://staging-token@example.internal/api"

    def fake_urlopen(request: object, *, timeout: int) -> FakeResponse:
        parsed = urlparse(getattr(request, "full_url"))
        body = getattr(request, "data", None)
        payload = json.loads(body.decode("utf-8")) if body else None
        if parsed.path == "/api/health":
            return FakeResponse({"status": "ok"})
        if parsed.path == "/api/api/system/readiness":
            return FakeResponse(safe_payload(status="ready", database_configured=True))
        if parsed.path == "/api/api/dashboard/decision-summary/preview":
            assert payload is not None
            return FakeResponse(safe_payload(price_area=payload["price_area"]))
        pytest.fail(f"unexpected smoke path: {parsed.path}")

    exit_code = module.run_smoke(
        environ={"BACKEND_BASE_URL": raw_base_url},
        opener=fake_urlopen,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert raw_base_url not in captured.out + captured.err
    assert "configured BACKEND_BASE_URL" in captured.out


def test_staging_smoke_fails_when_backend_is_unreachable(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = load_script_module()

    def fake_urlopen(request: object, *, timeout: int) -> FakeResponse:
        raise urllib.error.URLError("connection refused")

    exit_code = module.run_smoke(environ={}, opener=fake_urlopen)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "backend is unreachable" in captured.err


def test_staging_smoke_fails_when_readiness_endpoint_is_missing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = load_script_module()

    def fake_urlopen(request: object, *, timeout: int) -> FakeResponse:
        parsed = urlparse(getattr(request, "full_url"))
        if parsed.path == "/health":
            return FakeResponse({"status": "ok"})
        if parsed.path == "/api/system/readiness":
            raise urllib.error.HTTPError(
                getattr(request, "full_url"),
                404,
                "Not Found",
                hdrs=None,
                fp=None,
            )
        pytest.fail(f"unexpected smoke path: {parsed.path}")

    exit_code = module.run_smoke(environ={}, opener=fake_urlopen)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "readiness endpoint is missing" in captured.err


def test_staging_smoke_fails_when_safety_flag_is_not_true(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = load_script_module()

    def fake_urlopen(request: object, *, timeout: int) -> FakeResponse:
        parsed = urlparse(getattr(request, "full_url"))
        body = getattr(request, "data", None)
        payload = json.loads(body.decode("utf-8")) if body else None
        if parsed.path == "/health":
            return FakeResponse({"status": "ok"})
        if parsed.path == "/api/system/readiness":
            return FakeResponse(
                safe_payload(
                    status="ready",
                    database_configured=True,
                    decision_support_only=False,
                )
            )
        if parsed.path == "/api/dashboard/decision-summary/preview":
            assert payload is not None
            return FakeResponse(safe_payload(price_area=payload["price_area"]))
        pytest.fail(f"unexpected smoke path: {parsed.path}")

    exit_code = module.run_smoke(environ={}, opener=fake_urlopen)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "decision_support_only is not true" in captured.err


def test_staging_smoke_fails_when_dashboard_summary_is_not_safe_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = load_script_module()

    def fake_urlopen(request: object, *, timeout: int) -> FakeResponse:
        parsed = urlparse(getattr(request, "full_url"))
        body = getattr(request, "data", None)
        payload = json.loads(body.decode("utf-8")) if body else None
        if parsed.path == "/health":
            return FakeResponse({"status": "ok"})
        if parsed.path == "/api/system/readiness":
            return FakeResponse(safe_payload(status="ready", database_configured=True))
        if parsed.path == "/api/dashboard/decision-summary/preview":
            assert payload is not None
            if payload["price_area"] == "DK2":
                return FakeResponse(safe_payload(price_area="DK1"))
            return FakeResponse(safe_payload(price_area=payload["price_area"]))
        pytest.fail(f"unexpected smoke path: {parsed.path}")

    exit_code = module.run_smoke(environ={}, opener=fake_urlopen)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "DK2 dashboard summary returned wrong price_area" in captured.err
