from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audit import router as audit_router
from app.api.dashboard import router as dashboard_router
from app.api.energy import router as energy_router
from app.api.energy_freshness import router as energy_freshness_router
from app.api.energy_freshness_read import router as energy_freshness_read_router
from app.api.forecast import router as forecast_router
from app.api.report import router as report_router
from app.api.risk import router as risk_router


APP_VERSION = "0.1.0"
LOCAL_DEVELOPMENT_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)
EXPOSED_PDF_EXPORT_HEADERS = (
    "Content-Disposition",
    "X-FlexSignal-Decision-Support-Only",
    "X-FlexSignal-File-Written",
    "X-FlexSignal-Pdf-Generated-In-Memory",
    "X-FlexSignal-Audit-Event-Created",
    "X-FlexSignal-Audit-Event-Persisted",
    "X-FlexSignal-Audit-Event-Type",
    "X-FlexSignal-Audit-Event-Id",
    "X-FlexSignal-Audit-Table",
    "X-FlexSignal-Database-Query-Executed",
    "X-FlexSignal-Database-Write-Performed",
    "X-FlexSignal-Database-Write-Scope",
    "X-FlexSignal-Requires-Database-Url",
    "X-FlexSignal-No-Control-Dispatch-Activation",
)


def _include_materialized_router(application: FastAPI, router: APIRouter) -> None:
    """Register routes so app.routes exposes concrete route paths."""
    application.router.routes.extend(router.routes)
    mark_routes_changed = getattr(application.router, "_mark_routes_changed", None)
    if callable(mark_routes_changed):
        mark_routes_changed()


app = FastAPI(title="FlexSignal AI API", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_DEVELOPMENT_CORS_ORIGINS,
    allow_methods=("GET", "POST", "OPTIONS"),
    expose_headers=EXPOSED_PDF_EXPORT_HEADERS,
)
_include_materialized_router(app, energy_router)
_include_materialized_router(app, energy_freshness_router)
_include_materialized_router(app, energy_freshness_read_router)
_include_materialized_router(app, forecast_router)
_include_materialized_router(app, risk_router)
_include_materialized_router(app, dashboard_router)
_include_materialized_router(app, audit_router)
_include_materialized_router(app, report_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "flexsignal-ai-api",
        "version": APP_VERSION,
    }
