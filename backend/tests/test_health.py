from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
EXPECTED_EXPOSED_REPORT_PDF_HEADERS = {
    "content-disposition",
    "x-flexsignal-decision-support-only",
    "x-flexsignal-file-written",
    "x-flexsignal-database-query-executed",
    "x-flexsignal-database-write-performed",
    "x-flexsignal-requires-database-url",
}


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "flexsignal-ai-api"


def test_health_includes_local_development_cors_headers() -> None:
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    exposed_headers = {
        header.strip().lower()
        for header in response.headers["access-control-expose-headers"].split(",")
    }

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert EXPECTED_EXPOSED_REPORT_PDF_HEADERS <= exposed_headers


def test_local_development_cors_preflight_allows_read_only_api_methods() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
    assert set(response.headers["access-control-allow-methods"].split(", ")) == {
        "GET",
        "POST",
        "OPTIONS",
    }


def test_forecast_preview_post_cors_preflight_allows_local_frontend() -> None:
    response = client.options(
        "/api/forecast/preview",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "POST" in response.headers["access-control-allow-methods"].split(", ")


def test_risk_preview_post_cors_preflight_still_allows_local_frontend() -> None:
    response = client.options(
        "/api/risk/preview",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
    assert "POST" in response.headers["access-control-allow-methods"].split(", ")
