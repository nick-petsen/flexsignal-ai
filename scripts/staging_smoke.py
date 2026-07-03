#!/usr/bin/env python3
"""Local/staging backend smoke check for MVP readiness."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any, Callable, TextIO


DEFAULT_BACKEND_BASE_URL = "http://127.0.0.1:8000"
TIMEOUT_SECONDS = 5
SAFETY_FLAGS = (
    "decision_support_only",
    "human_review_required",
    "no_automatic_control",
    "no_dispatch",
    "no_activation",
)


class SmokeFailure(RuntimeError):
    """Expected smoke-check failure with a user-safe message."""


UrlOpen = Callable[..., Any]


def backend_base_url(environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    configured_url = env.get("BACKEND_BASE_URL", "").strip()
    return (configured_url or DEFAULT_BACKEND_BASE_URL).rstrip("/")


def request_json(
    method: str,
    path: str,
    *,
    base_url: str,
    payload: dict[str, Any] | None = None,
    opener: UrlOpen = urllib.request.urlopen,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with opener(request, timeout=TIMEOUT_SECONDS) as response:
            status_code = getattr(response, "status", None)
            raw_body = response.read()
    except urllib.error.HTTPError as exc:
        if path == "/api/system/readiness" and exc.code == 404:
            raise SmokeFailure("readiness endpoint is missing") from exc
        raise SmokeFailure(f"{path} returned HTTP {exc.code}") from exc
    except (TimeoutError, urllib.error.URLError, OSError) as exc:
        raise SmokeFailure("backend is unreachable") from exc

    if status_code != 200:
        raise SmokeFailure(f"{path} returned HTTP {status_code}")

    try:
        decoded = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SmokeFailure(f"{path} did not return valid JSON") from exc

    if not isinstance(decoded, dict):
        raise SmokeFailure(f"{path} did not return a JSON object")
    return decoded


def require_safety_flags(payload: Mapping[str, Any], *, context: str) -> None:
    for flag in SAFETY_FLAGS:
        if payload.get(flag) is not True:
            raise SmokeFailure(f"{context} safety flag {flag} is not true")


def require_health(payload: Mapping[str, Any]) -> None:
    if payload.get("status") != "ok":
        raise SmokeFailure("health endpoint did not report ok status")


def require_dashboard_summary(payload: Mapping[str, Any], *, price_area: str) -> None:
    if payload.get("price_area") != price_area:
        raise SmokeFailure(f"{price_area} dashboard summary returned wrong price_area")
    require_safety_flags(payload, context=f"{price_area} dashboard summary")


def run_smoke(
    *,
    environ: Mapping[str, str] | None = None,
    opener: UrlOpen = urllib.request.urlopen,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    env = os.environ if environ is None else environ
    base_url = backend_base_url(env)
    target_label = (
        "configured BACKEND_BASE_URL"
        if env.get("BACKEND_BASE_URL", "").strip()
        else "default local backend"
    )

    try:
        health = request_json("GET", "/health", base_url=base_url, opener=opener)
        require_health(health)

        readiness = request_json(
            "GET",
            "/api/system/readiness",
            base_url=base_url,
            opener=opener,
        )
        require_safety_flags(readiness, context="readiness")

        dashboard_results: dict[str, dict[str, Any]] = {}
        for price_area in ("DK1", "DK2"):
            summary = request_json(
                "POST",
                "/api/dashboard/decision-summary/preview",
                base_url=base_url,
                payload={"price_area": price_area},
                opener=opener,
            )
            require_dashboard_summary(summary, price_area=price_area)
            dashboard_results[price_area] = summary
    except SmokeFailure as exc:
        print(f"Staging smoke failed: {exc}", file=stderr)
        return 1

    readiness_status = readiness.get("status", "unknown")
    database_configured = readiness.get("database_configured", "unknown")
    print("Staging smoke summary", file=stdout)
    print(f"- backend target: {target_label}", file=stdout)
    print("- health: ok", file=stdout)
    print(
        f"- readiness: {readiness_status}, database_configured={database_configured}",
        file=stdout,
    )
    for price_area in dashboard_results:
        print(f"- {price_area} decision summary: safe JSON", file=stdout)
    print("- safety boundary: decision support only, human review required", file=stdout)
    print("- writes/external APIs: none performed by this script", file=stdout)
    return 0


def main() -> int:
    return run_smoke()


if __name__ == "__main__":
    raise SystemExit(main())
