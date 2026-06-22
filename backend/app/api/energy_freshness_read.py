from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException

from app.db.repositories.energy_freshness_reader import (
    SAFETY_BOUNDARY,
    read_energy_freshness_summary,
)


router = APIRouter(prefix="/api/energy", tags=["energy"])

SUPPORTED_PRICE_AREAS = ("DK1", "DK2")
WARNINGS = (
    "Executes SELECT-only freshness reads against the configured database.",
    "Does not write to the database or trigger ingestion.",
)


@router.get("/freshness/read")
def read_energy_freshness(price_area: str) -> dict[str, Any]:
    if price_area not in SUPPORTED_PRICE_AREAS:
        raise HTTPException(status_code=400, detail="Unsupported price_area")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail={
                "warning": (
                    "DATABASE_URL is required at request time; no database "
                    "freshness read was attempted."
                ),
                "database_query_executed": False,
                "database_write_performed": False,
                "requires_database_url": True,
            },
        )

    connection = None
    try:
        connection = connect_with_psycopg(database_url)
        freshness_result = read_energy_freshness_summary(connection, price_area)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Unsupported price_area") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - real DB failures are env-specific
        raise HTTPException(
            status_code=503,
            detail="Database freshness read failed",
        ) from exc
    finally:
        if connection is not None:
            close = getattr(connection, "close", None)
            if callable(close):
                close()

    result_warnings = list(freshness_result.get("warnings", ()))
    return {
        "price_area": price_area,
        "dry_run": False,
        "database_query_executed": True,
        "database_write_performed": False,
        "requires_database_url": True,
        "freshness_result": freshness_result,
        "spot_price_freshness": freshness_result["spot_price_freshness"],
        "power_balance_freshness": freshness_result["power_balance_freshness"],
        "warnings": [*WARNINGS, *result_warnings],
        "safety_boundary": dict(SAFETY_BOUNDARY),
    }


def connect_with_psycopg(database_url: str) -> Any:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:  # pragma: no cover - depends on deployment env
        raise RuntimeError("Database driver is not installed") from exc

    return psycopg.connect(
        database_url,
        row_factory=dict_row,
        autocommit=True,
    )
