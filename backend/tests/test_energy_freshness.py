import re
from pathlib import Path
from typing import Any

import pytest

from app.db.repositories.energy_freshness import (
    POWER_BALANCE_FRESHNESS_PART,
    SPOT_PRICE_FRESHNESS_PART,
    build_energy_freshness_summary_plan,
    build_power_balance_freshness_query,
    build_spot_price_freshness_query,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "db"
    / "repositories"
    / "energy_freshness.py"
)
MODULE_SOURCE = MODULE_PATH.read_text(encoding="utf-8")
FORBIDDEN_SQL_OPERATIONS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "UPSERT",
    "CREATE",
    "ALTER",
    "DROP",
)


@pytest.mark.parametrize(
    "builder",
    [
        build_spot_price_freshness_query,
        build_power_balance_freshness_query,
        build_energy_freshness_summary_plan,
    ],
)
@pytest.mark.parametrize("price_area", ["DK1", "DK2"])
def test_dk1_and_dk2_are_accepted(builder: Any, price_area: str) -> None:
    plan = builder(price_area)

    assert plan["price_area"] == price_area


@pytest.mark.parametrize(
    "builder",
    [
        build_spot_price_freshness_query,
        build_power_balance_freshness_query,
        build_energy_freshness_summary_plan,
    ],
)
def test_invalid_price_area_is_rejected(builder: Any) -> None:
    with pytest.raises(ValueError, match="Unsupported energy freshness price area"):
        builder("SE3")


@pytest.mark.parametrize(
    "query",
    [
        build_spot_price_freshness_query("DK1"),
        build_power_balance_freshness_query("DK2"),
    ],
)
def test_generated_sql_is_select_only(query: dict[str, Any]) -> None:
    sql = query["sql"]

    assert query["operation"] == "select"
    assert re.match(r"^SELECT\b", sql)
    for operation in FORBIDDEN_SQL_OPERATIONS:
        assert not re.search(rf"\b{operation}\b", sql, flags=re.IGNORECASE)


@pytest.mark.parametrize(
    "query",
    [
        build_spot_price_freshness_query("DK1"),
        build_power_balance_freshness_query("DK2"),
    ],
)
def test_generated_sql_uses_parameters(query: dict[str, Any]) -> None:
    sql = query["sql"]

    assert "%(price_area)s" in sql
    assert "%(source_label)s" in sql
    assert "%(empty_warning)s" in sql
    assert query["params"]["price_area"] in {"DK1", "DK2"}
    assert query["params"]["price_area"] not in sql


def test_spot_price_freshness_query_shape() -> None:
    query = build_spot_price_freshness_query("DK1")

    assert query["read_model"] == "eds-data-freshness-read-model-v0"
    assert query["part"] == SPOT_PRICE_FRESHNESS_PART
    assert query["table"] == "spot_prices"
    assert query["params"] == {
        "price_area": "DK1",
        "source_label": "Energi Data Service:DayAheadPrices",
        "empty_warning": "No spot price rows are available for this price area.",
    }
    assert "MIN(timestamp_utc) AS earliest_timestamp_utc" in query["sql"]
    assert "MAX(timestamp_utc) AS latest_timestamp_utc" in query["sql"]
    assert "COUNT(*) AS row_count" in query["sql"]


def test_power_balance_freshness_query_shape() -> None:
    query = build_power_balance_freshness_query("DK2")

    assert query["part"] == POWER_BALANCE_FRESHNESS_PART
    assert query["table"] == "power_balance"
    assert query["params"] == {
        "price_area": "DK2",
        "source_label": "Energi Data Service:ElectricityProdex5MinRealtime",
        "empty_warning": "No power balance rows are available for this price area.",
    }
    assert "FROM power_balance" in query["sql"]


def test_summary_plan_contains_spot_price_and_power_balance_parts() -> None:
    plan = build_energy_freshness_summary_plan("DK1")

    assert plan["read_model"] == "eds-data-freshness-read-model-v0"
    assert plan["operation"] == "select"
    assert set(plan["queries"]) == {
        SPOT_PRICE_FRESHNESS_PART,
        POWER_BALANCE_FRESHNESS_PART,
    }
    assert plan["queries"][SPOT_PRICE_FRESHNESS_PART]["table"] == "spot_prices"
    assert plan["queries"][POWER_BALANCE_FRESHNESS_PART]["table"] == "power_balance"


def test_query_plans_do_not_contain_raw_user_interpolation() -> None:
    query = build_spot_price_freshness_query("DK1")

    assert "DK1" not in query["sql"]
    assert "{price_area}" not in query["sql"]
    assert query["params"]["price_area"] == "DK1"


def test_module_does_not_import_fastapi_or_apirouter() -> None:
    assert "FastAPI" not in MODULE_SOURCE
    assert "APIRouter" not in MODULE_SOURCE


def test_module_does_not_read_database_url() -> None:
    assert "DATABASE_URL" not in MODULE_SOURCE
    assert "os.environ" not in MODULE_SOURCE
    assert "getenv" not in MODULE_SOURCE


def test_module_does_not_call_energi_data_service_or_dmi() -> None:
    assert "api.energidataservice" not in MODULE_SOURCE
    assert "DMI" not in MODULE_SOURCE
    assert "requests." not in MODULE_SOURCE
    assert "httpx." not in MODULE_SOURCE


def test_module_does_not_perform_writes_or_control_behavior() -> None:
    for operation in FORBIDDEN_SQL_OPERATIONS:
        assert operation not in MODULE_SOURCE

    assert "connect(" not in MODULE_SOURCE
    assert "execute(" not in MODULE_SOURCE
    assert "commit(" not in MODULE_SOURCE
    assert "rollback(" not in MODULE_SOURCE
    assert "dispatch" not in MODULE_SOURCE.lower()
    assert "activation" not in MODULE_SOURCE.lower()
    assert "control" not in MODULE_SOURCE.lower()
