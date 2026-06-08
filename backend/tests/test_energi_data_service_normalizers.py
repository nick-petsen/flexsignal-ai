import pytest

from app.integrations.energi_data_service_normalizers import (
    normalize_day_ahead_price,
    normalize_electricity_prodex_5min_realtime,
)


def test_day_ahead_prices_dk1_normalization() -> None:
    record = {
        "PriceArea": "DK1",
        "TimeUTC": "2026-01-01T00:00:00",
        "DayAheadPriceDKK": 512.34,
        "DayAheadPriceEUR": 68.67,
    }

    assert normalize_day_ahead_price(record) == {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "price_dkk_per_mwh": 512.34,
        "price_eur_per_mwh": 68.67,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
    }


def test_day_ahead_prices_dk2_normalization() -> None:
    record = {
        "PriceArea": "DK2",
        "TimeUTC": "2026-01-01T01:00:00",
        "DayAheadPriceDKK": 401.25,
        "DayAheadPriceEUR": 53.82,
    }

    assert normalize_day_ahead_price(record) == {
        "price_area": "DK2",
        "timestamp_utc": "2026-01-01T01:00:00",
        "price_dkk_per_mwh": 401.25,
        "price_eur_per_mwh": 53.82,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": "DayAheadPrices:DK2:2026-01-01T01:00:00",
    }


def test_day_ahead_prices_rejects_unsupported_price_area() -> None:
    record = {
        "PriceArea": "DE",
        "TimeUTC": "2026-01-01T00:00:00",
        "DayAheadPriceDKK": 512.34,
        "DayAheadPriceEUR": 68.67,
    }

    with pytest.raises(ValueError):
        normalize_day_ahead_price(record)


@pytest.mark.parametrize(
    "missing_field",
    ["PriceArea", "TimeUTC", "DayAheadPriceDKK", "DayAheadPriceEUR"],
)
def test_day_ahead_prices_rejects_missing_required_fields(missing_field: str) -> None:
    record = {
        "PriceArea": "DK1",
        "TimeUTC": "2026-01-01T00:00:00",
        "DayAheadPriceDKK": 512.34,
        "DayAheadPriceEUR": 68.67,
    }
    del record[missing_field]

    with pytest.raises(ValueError):
        normalize_day_ahead_price(record)


def test_electricity_prodex_5min_realtime_dk1_normalization() -> None:
    record = {
        "PriceArea": "DK1",
        "Minutes5UTC": "2026-01-01T00:00:00",
        "OnshoreWindPower": 100,
        "OffshoreWindPower": 200,
        "SolarPower": 50,
        "ProductionGe100MW": 300,
        "ProductionLt100MW": 25,
        "ExchangeGermany": -75,
        "ExchangeNorway": 10,
        "ExchangeSweden": 20,
        "ExchangeGreatBelt": 30,
        "ExchangeNetherlands": -15,
        "ExchangeGreatBritain": 5,
    }

    assert normalize_electricity_prodex_5min_realtime(record) == {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "wind_onshore_mw": 100,
        "wind_offshore_mw": 200,
        "solar_mw": 50,
        "production_mw": 675,
        "exchange_net_mw": -25,
        "source": "Energi Data Service:ElectricityProdex5MinRealtime",
        "source_record_id": (
            "ElectricityProdex5MinRealtime:DK1:2026-01-01T00:00:00"
        ),
    }


def test_electricity_prodex_5min_realtime_dk2_normalization() -> None:
    record = {
        "PriceArea": "DK2",
        "Minutes5UTC": "2026-01-01T00:05:00",
        "OnshoreWindPower": 80,
        "OffshoreWindPower": 120,
        "SolarPower": 40,
        "ProductionGe100MW": 250,
        "ProductionLt100MW": 15,
        "ExchangeGermany": -25,
        "ExchangeNorway": None,
        "ExchangeSweden": 60,
        "ExchangeGreatBelt": -10,
        "ExchangeNetherlands": None,
        "ExchangeGreatBritain": 5,
    }

    assert normalize_electricity_prodex_5min_realtime(record) == {
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


def test_electricity_prodex_5min_realtime_sums_production_fields_correctly() -> None:
    record = {
        "PriceArea": "DK1",
        "Minutes5UTC": "2026-01-01T00:10:00",
        "OnshoreWindPower": 10,
        "OffshoreWindPower": 20,
        "SolarPower": 30,
        "ProductionGe100MW": 40,
        "ProductionLt100MW": 50,
    }

    normalized = normalize_electricity_prodex_5min_realtime(record)

    assert normalized["production_mw"] == 150


def test_electricity_prodex_5min_realtime_sums_exchange_fields_with_null_as_zero() -> None:
    record = {
        "PriceArea": "DK1",
        "Minutes5UTC": "2026-01-01T00:15:00",
        "OnshoreWindPower": 10,
        "OffshoreWindPower": None,
        "SolarPower": 5,
        "ProductionGe100MW": 40,
        "ProductionLt100MW": None,
        "ExchangeGermany": -10,
        "ExchangeNorway": None,
        "ExchangeSweden": 25,
        "ExchangeGreatBelt": None,
        "ExchangeNetherlands": -5,
        "ExchangeGreatBritain": 15,
    }

    normalized = normalize_electricity_prodex_5min_realtime(record)

    assert normalized["wind_offshore_mw"] == 0
    assert normalized["production_mw"] == 55
    assert normalized["exchange_net_mw"] == 25


def test_electricity_prodex_5min_realtime_rejects_missing_price_area() -> None:
    record = {
        "Minutes5UTC": "2026-01-01T00:00:00",
    }

    with pytest.raises(ValueError):
        normalize_electricity_prodex_5min_realtime(record)


def test_electricity_prodex_5min_realtime_rejects_missing_minutes_5_utc() -> None:
    record = {
        "PriceArea": "DK1",
    }

    with pytest.raises(ValueError):
        normalize_electricity_prodex_5min_realtime(record)
