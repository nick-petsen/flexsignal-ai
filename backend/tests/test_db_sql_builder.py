import pytest

from app.db.sql_builder import build_eds_write_plan_entry_upsert_sql


def test_spot_prices_upsert_sql_uses_placeholders_and_params() -> None:
    entry = {
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

    result = build_eds_write_plan_entry_upsert_sql(entry)

    assert result["table"] == "spot_prices"
    assert result["operation"] == "upsert_preview"
    assert result["params"] == entry["payload"]
    assert result["sql"] == (
        "INSERT INTO spot_prices "
        "(price_area, timestamp_utc, price_eur_per_mwh, price_dkk_per_mwh, "
        "source, source_record_id) "
        "VALUES (%(price_area)s, %(timestamp_utc)s, %(price_eur_per_mwh)s, "
        "%(price_dkk_per_mwh)s, %(source)s, %(source_record_id)s) "
        "ON CONFLICT (source, source_record_id) "
        "DO UPDATE SET price_area = EXCLUDED.price_area, "
        "timestamp_utc = EXCLUDED.timestamp_utc, "
        "price_eur_per_mwh = EXCLUDED.price_eur_per_mwh, "
        "price_dkk_per_mwh = EXCLUDED.price_dkk_per_mwh"
    )


def test_power_balance_upsert_sql_uses_placeholders_and_params() -> None:
    payload = {
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
    entry = {
        "table": "power_balance",
        "operation": "upsert_preview",
        "conflict_key": {
            "source": "Energi Data Service:ElectricityProdex5MinRealtime",
            "source_record_id": (
                "ElectricityProdex5MinRealtime:DK2:2026-01-01T00:05:00"
            ),
        },
        "payload": payload,
    }

    result = build_eds_write_plan_entry_upsert_sql(entry)

    assert result["table"] == "power_balance"
    assert result["operation"] == "upsert_preview"
    assert result["params"] == payload
    assert result["sql"] == (
        "INSERT INTO power_balance "
        "(price_area, timestamp_utc, production_mw, consumption_mw, "
        "wind_onshore_mw, wind_offshore_mw, solar_mw, exchange_net_mw, "
        "source, source_record_id) "
        "VALUES (%(price_area)s, %(timestamp_utc)s, %(production_mw)s, "
        "%(consumption_mw)s, %(wind_onshore_mw)s, %(wind_offshore_mw)s, "
        "%(solar_mw)s, %(exchange_net_mw)s, %(source)s, %(source_record_id)s) "
        "ON CONFLICT (source, source_record_id) "
        "DO UPDATE SET price_area = EXCLUDED.price_area, "
        "timestamp_utc = EXCLUDED.timestamp_utc, "
        "production_mw = EXCLUDED.production_mw, "
        "consumption_mw = EXCLUDED.consumption_mw, "
        "wind_onshore_mw = EXCLUDED.wind_onshore_mw, "
        "wind_offshore_mw = EXCLUDED.wind_offshore_mw, "
        "solar_mw = EXCLUDED.solar_mw, "
        "exchange_net_mw = EXCLUDED.exchange_net_mw"
    )


def test_raw_values_are_not_interpolated_into_sql() -> None:
    entry = {
        "table": "spot_prices",
        "operation": "upsert_preview",
        "payload": {
            "price_area": "DK1",
            "timestamp_utc": "2026-01-01T00:00:00",
            "price_eur_per_mwh": 68.67,
            "price_dkk_per_mwh": 512.34,
            "source": "Energi Data Service:DayAheadPrices",
            "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
        },
    }

    result = build_eds_write_plan_entry_upsert_sql(entry)

    for raw_value in entry["payload"].values():
        assert str(raw_value) not in result["sql"]


def test_source_record_id_can_be_absent_with_area_timestamp_source_conflict() -> None:
    entry = {
        "table": "spot_prices",
        "operation": "upsert_preview",
        "payload": {
            "price_area": "DK1",
            "timestamp_utc": "2026-01-01T00:00:00",
            "price_eur_per_mwh": 68.67,
            "price_dkk_per_mwh": 512.34,
            "source": "Energi Data Service:DayAheadPrices",
        },
    }

    result = build_eds_write_plan_entry_upsert_sql(entry)

    assert result["params"]["source_record_id"] is None
    assert "ON CONFLICT (price_area, timestamp_utc, source)" in result["sql"]


def test_unsupported_table_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported EDS write-plan table"):
        build_eds_write_plan_entry_upsert_sql(
            {
                "table": "weather_observations",
                "operation": "upsert_preview",
                "payload": {},
            }
        )


def test_unsupported_operation_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported EDS write-plan operation"):
        build_eds_write_plan_entry_upsert_sql(
            {
                "table": "spot_prices",
                "operation": "insert_preview",
                "payload": {},
            }
        )


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
def test_missing_required_spot_price_payload_fields_are_rejected(
    missing_field: str,
) -> None:
    payload = {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "price_eur_per_mwh": 68.67,
        "price_dkk_per_mwh": 512.34,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
    }
    del payload[missing_field]

    with pytest.raises(
        ValueError,
        match="Missing required EDS write-plan payload field",
    ):
        build_eds_write_plan_entry_upsert_sql(
            {
                "table": "spot_prices",
                "operation": "upsert_preview",
                "payload": payload,
            }
        )


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
    ],
)
def test_missing_required_power_balance_payload_fields_are_rejected(
    missing_field: str,
) -> None:
    payload = {
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
    del payload[missing_field]

    with pytest.raises(
        ValueError,
        match="Missing required EDS write-plan payload field",
    ):
        build_eds_write_plan_entry_upsert_sql(
            {
                "table": "power_balance",
                "operation": "upsert_preview",
                "payload": payload,
            }
        )
