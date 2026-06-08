from __future__ import annotations

from typing import Any


ALLOWED_PRICE_AREAS = {"DK1", "DK2"}

DAY_AHEAD_PRICES_SOURCE = "Energi Data Service:DayAheadPrices"
ELECTRICITY_PRODEX_5MIN_REALTIME_SOURCE = (
    "Energi Data Service:ElectricityProdex5MinRealtime"
)

GENERATION_FIELDS = (
    "ProductionGe100MW",
    "ProductionLt100MW",
    "OnshoreWindPower",
    "OffshoreWindPower",
    "SolarPower",
)
EXCHANGE_FIELDS = (
    "ExchangeGermany",
    "ExchangeNorway",
    "ExchangeSweden",
    "ExchangeGreatBelt",
    "ExchangeNetherlands",
    "ExchangeGreatBritain",
)


def normalize_day_ahead_price(record: dict) -> dict:
    price_area = _require_price_area(record)
    timestamp_utc = _require_field(record, "TimeUTC")

    return {
        "price_area": price_area,
        "timestamp_utc": timestamp_utc,
        "price_dkk_per_mwh": _require_field(record, "DayAheadPriceDKK"),
        "price_eur_per_mwh": _require_field(record, "DayAheadPriceEUR"),
        "source": DAY_AHEAD_PRICES_SOURCE,
        "source_record_id": f"DayAheadPrices:{price_area}:{timestamp_utc}",
    }


def normalize_electricity_prodex_5min_realtime(record: dict) -> dict:
    price_area = _require_price_area(record)
    timestamp_utc = _require_field(record, "Minutes5UTC")

    wind_onshore_mw = _numeric_or_zero(record.get("OnshoreWindPower"))
    wind_offshore_mw = _numeric_or_zero(record.get("OffshoreWindPower"))
    solar_mw = _numeric_or_zero(record.get("SolarPower"))

    production_mw = sum(
        _numeric_or_zero(record.get(field)) for field in GENERATION_FIELDS
    )
    exchange_net_mw = sum(
        _numeric_or_zero(record.get(field)) for field in EXCHANGE_FIELDS
    )

    return {
        "price_area": price_area,
        "timestamp_utc": timestamp_utc,
        "wind_onshore_mw": wind_onshore_mw,
        "wind_offshore_mw": wind_offshore_mw,
        "solar_mw": solar_mw,
        "production_mw": production_mw,
        "exchange_net_mw": exchange_net_mw,
        "source": ELECTRICITY_PRODEX_5MIN_REALTIME_SOURCE,
        "source_record_id": (
            f"ElectricityProdex5MinRealtime:{price_area}:{timestamp_utc}"
        ),
    }


def _require_price_area(record: dict) -> str:
    price_area = _require_field(record, "PriceArea")

    if price_area not in ALLOWED_PRICE_AREAS:
        raise ValueError(f"Unsupported Energi Data Service price area: {price_area}")

    return price_area


def _require_field(record: dict, field_name: str) -> Any:
    if field_name not in record:
        raise ValueError(f"Missing required Energi Data Service field: {field_name}")

    return record[field_name]


def _numeric_or_zero(value: Any) -> Any:
    if value is None:
        return 0

    return value
