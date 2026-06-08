import pytest

from app.ingestion.eds_persistence_dry_run import run_eds_persistence_dry_run


class RecordingExecutor:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, object]]] = []

    def __call__(self, sql_commands: list[dict[str, object]]) -> None:
        self.calls.append(sql_commands)


def test_day_ahead_prices_chain_produces_spot_prices_sql_preview() -> None:
    result = run_eds_persistence_dry_run(
        dataset="DayAheadPrices",
        normalized_records=[_day_ahead_price_record()],
    )

    assert result["dataset"] == "DayAheadPrices"
    assert result["write_plan_count"] == 1
    assert result["sql_command_count"] == 1
    assert result["executed_count"] == 0
    assert result["preview_only"] is True
    assert result["tables"] == ["spot_prices"]

    sql_command = result["sql_commands"][0]
    assert sql_command["table"] == "spot_prices"
    assert sql_command["operation"] == "upsert_preview"
    assert sql_command["sql"].startswith("INSERT INTO spot_prices")
    assert "ON CONFLICT (source, source_record_id)" in sql_command["sql"]
    assert sql_command["params"] == {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "price_eur_per_mwh": 68.67,
        "price_dkk_per_mwh": 512.34,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
    }


def test_electricity_prodex_chain_produces_power_balance_sql_preview() -> None:
    result = run_eds_persistence_dry_run(
        dataset="ElectricityProdex5MinRealtime",
        normalized_records=[_electricity_prodex_record()],
    )

    assert result["dataset"] == "ElectricityProdex5MinRealtime"
    assert result["write_plan_count"] == 1
    assert result["sql_command_count"] == 1
    assert result["executed_count"] == 0
    assert result["preview_only"] is True
    assert result["tables"] == ["power_balance"]

    sql_command = result["sql_commands"][0]
    assert sql_command["table"] == "power_balance"
    assert sql_command["operation"] == "upsert_preview"
    assert sql_command["sql"].startswith("INSERT INTO power_balance")
    assert "ON CONFLICT (source, source_record_id)" in sql_command["sql"]
    assert sql_command["params"] == {
        "price_area": "DK2",
        "timestamp_utc": "2026-01-01T00:05:00",
        "production_mw": 505,
        "consumption_mw": None,
        "wind_onshore_mw": 80,
        "wind_offshore_mw": 120,
        "solar_mw": 40,
        "exchange_net_mw": 30,
        "source": "Energi Data Service:ElectricityProdex5MinRealtime",
        "source_record_id": (
            "ElectricityProdex5MinRealtime:DK2:2026-01-01T00:05:00"
        ),
    }


def test_preview_only_is_true_when_no_executor_is_provided() -> None:
    result = run_eds_persistence_dry_run(
        dataset="DayAheadPrices",
        normalized_records=[_day_ahead_price_record()],
    )

    assert result["preview_only"] is True
    assert result["executed_count"] == 0


def test_executor_is_called_with_generated_sql_commands_when_provided() -> None:
    executor = RecordingExecutor()

    result = run_eds_persistence_dry_run(
        dataset="DayAheadPrices",
        normalized_records=[_day_ahead_price_record()],
        executor=executor,
    )

    assert result["preview_only"] is False
    assert result["executed_count"] == 1
    assert len(executor.calls) == 1
    assert executor.calls[0] == result["sql_commands"]
    assert executor.calls[0][0]["table"] == "spot_prices"


def test_unsupported_dataset_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported Energi Data Service dataset"):
        run_eds_persistence_dry_run(
            dataset="ProductionConsumptionSettlement",
            normalized_records=[],
        )


def test_malformed_normalized_record_is_rejected() -> None:
    with pytest.raises(ValueError, match="Malformed normalized EDS record"):
        run_eds_persistence_dry_run(
            dataset="DayAheadPrices",
            normalized_records=["not-a-record"],
        )


def test_missing_required_normalized_field_is_rejected() -> None:
    record = _day_ahead_price_record()
    del record["price_dkk_per_mwh"]

    with pytest.raises(ValueError, match="Missing required normalized EDS field"):
        run_eds_persistence_dry_run(
            dataset="DayAheadPrices",
            normalized_records=[record],
        )


def _day_ahead_price_record() -> dict[str, object]:
    return {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "price_dkk_per_mwh": 512.34,
        "price_eur_per_mwh": 68.67,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
    }


def _electricity_prodex_record() -> dict[str, object]:
    return {
        "price_area": "DK2",
        "timestamp_utc": "2026-01-01T00:05:00",
        "wind_onshore_mw": 80,
        "wind_offshore_mw": 120,
        "solar_mw": 40,
        "production_mw": 505,
        "exchange_net_mw": 30,
        "source": "Energi Data Service:ElectricityProdex5MinRealtime",
        "source_record_id": (
            "ElectricityProdex5MinRealtime:DK2:2026-01-01T00:05:00"
        ),
    }
