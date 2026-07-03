from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter


router = APIRouter(prefix="/api/system", tags=["system"])


ReadinessStatus = Literal["ready", "degraded"]


@router.get("/readiness")
def get_system_readiness() -> dict[str, bool | str]:
    database_configured = bool(os.environ.get("DATABASE_URL"))
    status: ReadinessStatus = "ready" if database_configured else "degraded"

    return {
        "service": "flexsignal-ai-backend",
        "status": status,
        "decision_support_only": True,
        "human_review_required": True,
        "no_automatic_control": True,
        "no_dispatch": True,
        "no_activation": True,
        "database_configured": database_configured,
        "auth_configured": False,
        "external_control_enabled": False,
        "system_status_label_allowed": "Manual refresh mode",
    }
