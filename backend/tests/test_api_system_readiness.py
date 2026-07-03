from __future__ import annotations

import importlib
import subprocess
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
READINESS_PATH = "/api/system/readiness"
RAW_DATABASE_URL = (
    "postgresql://user:super-secret-token@staging-db.internal.example/flexsignal_ai"
)


def test_system_readiness_endpoint_exists() -> None:
    response = client.get(READINESS_PATH)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["service"] == "flexsignal-ai-backend"


def test_system_readiness_degraded_without_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.get(READINESS_PATH)

    assert response.status_code == 200
    assert response.json() == {
        "service": "flexsignal-ai-backend",
        "status": "degraded",
        "decision_support_only": True,
        "human_review_required": True,
        "no_automatic_control": True,
        "no_dispatch": True,
        "no_activation": True,
        "database_configured": False,
        "auth_configured": False,
        "external_control_enabled": False,
        "system_status_label_allowed": "Manual refresh mode",
    }


def test_system_readiness_ready_with_database_url_without_leaking_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", RAW_DATABASE_URL)

    response = client.get(READINESS_PATH)
    rendered = repr(response.json())

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["database_configured"] is True
    assert "DATABASE_URL" not in rendered
    assert RAW_DATABASE_URL not in rendered
    assert "super-secret-token" not in rendered
    assert "staging-db.internal.example" not in rendered
    assert "postgresql://" not in rendered


def test_system_readiness_safety_flags_preserve_read_only_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", RAW_DATABASE_URL)

    response = client.get(READINESS_PATH)
    body = response.json()

    assert response.status_code == 200
    assert body["decision_support_only"] is True
    assert body["human_review_required"] is True
    assert body["no_automatic_control"] is True
    assert body["no_dispatch"] is True
    assert body["no_activation"] is True
    assert body["external_control_enabled"] is False
    assert body["system_status_label_allowed"] == "Manual refresh mode"


def test_system_readiness_does_not_add_mutating_methods() -> None:
    route_methods = {
        method
        for route in app.routes
        if getattr(route, "path", None) == READINESS_PATH
        for method in getattr(route, "methods", set())
    }

    assert route_methods == {"GET"}
    assert not route_methods & {"POST", "PUT", "PATCH", "DELETE"}


def test_app_import_does_not_require_database_url_for_system_readiness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import app.main as main_module

    reloaded_main = importlib.reload(main_module)

    assert any(
        getattr(route, "path", None) == READINESS_PATH
        for route in reloaded_main.app.routes
    )


def test_system_readiness_does_not_call_external_apis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", RAW_DATABASE_URL)
    http_calls = 0

    def fail_live_http_call(*args: Any, **kwargs: Any) -> None:
        nonlocal http_calls
        http_calls += 1
        raise AssertionError("Live HTTP calls are not allowed")

    monkeypatch.setattr("urllib.request.urlopen", fail_live_http_call)

    response = client.get(READINESS_PATH)

    assert response.status_code == 200
    assert http_calls == 0


def test_no_frontend_files_changed_for_system_readiness_endpoint() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    diff = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...", "--", "frontend"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if diff.returncode != 0:
        pytest.skip("origin/main is not available for frontend diff check")

    assert diff.stdout.strip() == ""
