import pytest

from app.db.write_plan import build_eds_write_plan


def test_day_ahead_prices_produces_spot_prices_write_plan_entries() -> None:
    normalized_record = {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "price_dkk_per_mwh": 512.34,
        "price_eur_per_mwh": 68.67,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
    }

    plan = build_eds_write_plan(
        dataset="DayAheadPrices",
        normalized_records=[normalized_record],
    )

    assert plan == [
        {
            "table": "spot_prices",
            "operation": "upsert_preview",
            "conflict_key": {
                "source": "Energi Data Service:DayAheadPrices",
                "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
            },
            "payload": {
                "price_area": "DK1",
                "timestamp_utc": "2026-01-01T00:00:00",
                "price_eur_per_mwh": 68.67,
                "price_dkk_per_mwh": 512.34,
                "source": "Energi Data Service:DayAheadPrices",
                "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
            },
        }
    ]


def test_electricity_prodex_produces_power_balance_write_plan_entries() -> None:
    normalized_record = {
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

    plan = build_eds_write_plan(
        dataset="ElectricityProdex5MinRealtime",
        normalized_records=[normalized_record],
    )

    assert plan == [
        {
            "table": "power_balance",
            "operation": "upsert_preview",
            "conflict_key": {
                "source": "Energi Data Service:ElectricityProdex5MinRealtime",
                "source_record_id": (
                    "ElectricityProdex5MinRealtime:DK2:2026-01-01T00:05:00"
                ),
            },
            "payload": {
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
            },
        }
    ]


def test_operation_is_always_upsert_preview() -> None:
    plan = build_eds_write_plan(
        dataset="DayAheadPrices",
        normalized_records=[
            {
                "price_area": "DK1",
                "timestamp_utc": "2026-01-01T00:00:00",
                "price_dkk_per_mwh": 512.34,
                "price_eur_per_mwh": 68.67,
                "source": "Energi Data Service:DayAheadPrices",
                "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
            },
            {
                "price_area": "DK2",
                "timestamp_utc": "2026-01-01T01:00:00",
                "price_dkk_per_mwh": 500.0,
                "price_eur_per_mwh": 67.0,
                "source": "Energi Data Service:DayAheadPrices",
                "source_record_id": "DayAheadPrices:DK2:2026-01-01T01:00:00",
            },
        ],
    )

    assert {entry["operation"] for entry in plan} == {"upsert_preview"}


def test_conflict_key_falls_back_to_area_timestamp_source_without_source_record_id() -> None:
    plan = build_eds_write_plan(
        dataset="DayAheadPrices",
        normalized_records=[
            {
                "price_area": "DK1",
                "timestamp_utc": "2026-01-01T00:00:00",
                "price_dkk_per_mwh": 512.34,
                "price_eur_per_mwh": 68.67,
                "source": "Energi Data Service:DayAheadPrices",
            }
        ],
    )

    assert plan[0]["conflict_key"] == {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "source": "Energi Data Service:DayAheadPrices",
    }
    assert plan[0]["payload"]["source_record_id"] is None


@pytest.mark.parametrize(
    "missing_field",
    [
        "price_area",
        "timestamp_utc",
        "price_eur_per_mwh",
        "price_dkk_per_mwh",
        "source",
    ],
)
def test_missing_required_fields_are_rejected(missing_field: str) -> None:
    normalized_record = {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "price_dkk_per_mwh": 512.34,
        "price_eur_per_mwh": 68.67,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
    }
    del normalized_record[missing_field]

    with pytest.raises(ValueError, match="Missing required normalized EDS field"):
        build_eds_write_plan(
            dataset="DayAheadPrices",
            normalized_records=[normalized_record],
        )


def test_missing_required_power_balance_fields_are_rejected() -> None:
    normalized_record = {
        "price_area": "DK2",
        "timestamp_utc": "2026-01-01T00:05:00",
        "wind_onshore_mw": 80,
        "wind_offshore_mw": 120,
        "solar_mw": 40,
        "exchange_net_mw": 30,
        "source": "Energi Data Service:ElectricityProdex5MinRealtime",
        "source_record_id": (
            "ElectricityProdex5MinRealtime:DK2:2026-01-01T00:05:00"
        ),
    }

    with pytest.raises(ValueError, match="Missing required normalized EDS field"):
        build_eds_write_plan(
            dataset="ElectricityProdex5MinRealtime",
            normalized_records=[normalized_record],
        )


def test_unsupported_dataset_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported Energi Data Service dataset"):
        build_eds_write_plan(
            dataset="ProductionConsumptionSettlement",
            normalized_records=[],
        )
