import pytest

from app.db.repositories.eds_records import (
    build_eds_record_insert_payload,
    day_ahead_price_to_spot_price_payload,
    electricity_prodex_5min_realtime_to_power_balance_payload,
)


def test_day_ahead_price_maps_to_spot_prices_payload() -> None:
    normalized_record = {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "price_dkk_per_mwh": 512.34,
        "price_eur_per_mwh": 68.67,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
    }

    payload = day_ahead_price_to_spot_price_payload(normalized_record)

    assert payload == {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "price_eur_per_mwh": 68.67,
        "price_dkk_per_mwh": 512.34,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
    }


def test_electricity_prodex_maps_to_power_balance_payload() -> None:
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

    payload = electricity_prodex_5min_realtime_to_power_balance_payload(
        normalized_record
    )

    assert payload == {
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


@pytest.mark.parametrize(
    "missing_field",
    [
        "price_area",
        "timestamp_utc",
        "price_eur_per_mwh",
        "price_dkk_per_mwh",
        "source",
        "source_record_id",
    ],
)
def test_missing_required_spot_price_fields_are_rejected(
    missing_field: str,
) -> None:
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
        day_ahead_price_to_spot_price_payload(normalized_record)


@pytest.mark.parametrize(
    "missing_field",
    [
        "price_area",
        "timestamp_utc",
        "production_mw",
        "wind_onshore_mw",
        "wind_offshore_mw",
        "solar_mw",
        "exchange_net_mw",
        "source",
        "source_record_id",
    ],
)
def test_missing_required_power_balance_fields_are_rejected(
    missing_field: str,
) -> None:
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
    del normalized_record[missing_field]

    with pytest.raises(ValueError, match="Missing required normalized EDS field"):
        electricity_prodex_5min_realtime_to_power_balance_payload(normalized_record)


def test_unsupported_dataset_table_target_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported EDS dataset/table target"):
        build_eds_record_insert_payload(
            dataset="DayAheadPrices",
            table="power_balance",
            normalized_record={},
        )


def test_supported_dataset_table_target_uses_mapper() -> None:
    normalized_record = {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "price_dkk_per_mwh": 512.34,
        "price_eur_per_mwh": 68.67,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
    }

    payload = build_eds_record_insert_payload(
        dataset="DayAheadPrices",
        table="spot_prices",
        normalized_record=normalized_record,
    )

    assert payload["price_eur_per_mwh"] == 68.67
