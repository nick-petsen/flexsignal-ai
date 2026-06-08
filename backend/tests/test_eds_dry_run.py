import pytest

from app.ingestion.eds_dry_run import run_eds_dry_run


def test_day_ahead_prices_dk1_dry_run_summary() -> None:
    seen_urls: list[str] = []

    def fetch(url: str) -> dict:
        seen_urls.append(url)
        return {
            "records": [
                {
                    "PriceArea": "DK1",
                    "TimeUTC": "2026-01-01T00:00:00",
                    "DayAheadPriceDKK": 512.34,
                    "DayAheadPriceEUR": 68.67,
                }
            ]
        }

    summary = run_eds_dry_run(
        dataset="DayAheadPrices",
        price_area="DK1",
        limit=1,
        fetch=fetch,
    )

    assert summary.dataset == "DayAheadPrices"
    assert summary.price_area == "DK1"
    assert summary.limit == 1
    assert summary.request_url == seen_urls[0]
    assert summary.request_url.startswith(
        "https://api.energidataservice.dk/dataset/DayAheadPrices?"
    )
    assert "limit=1" in summary.request_url
    assert "filter=%7B%22PriceArea%22%3A%5B%22DK1%22%5D%7D" in summary.request_url
    assert summary.raw_record_count == 1
    assert summary.normalized_record_count == 1
    assert summary.rejected_record_count == 0
    assert summary.normalized_records == [
        {
            "price_area": "DK1",
            "timestamp_utc": "2026-01-01T00:00:00",
            "price_dkk_per_mwh": 512.34,
            "price_eur_per_mwh": 68.67,
            "source": "Energi Data Service:DayAheadPrices",
            "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
        }
    ]


def test_electricity_prodex_5min_realtime_dk2_dry_run_summary() -> None:
    def fetch(url: str) -> dict:
        return {
            "records": [
                {
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
            ]
        }

    summary = run_eds_dry_run(
        dataset="ElectricityProdex5MinRealtime",
        price_area="DK2",
        limit=5,
        fetch=fetch,
    )

    assert summary.dataset == "ElectricityProdex5MinRealtime"
    assert summary.price_area == "DK2"
    assert summary.limit == 5
    assert summary.request_url.startswith(
        "https://api.energidataservice.dk/dataset/ElectricityProdex5MinRealtime?"
    )
    assert "limit=5" in summary.request_url
    assert "filter=%7B%22PriceArea%22%3A%5B%22DK2%22%5D%7D" in summary.request_url
    assert summary.raw_record_count == 1
    assert summary.normalized_record_count == 1
    assert summary.rejected_record_count == 0
    assert summary.normalized_records == [
        {
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
    ]


def test_invalid_dataset_raises_value_error() -> None:
    with pytest.raises(ValueError):
        run_eds_dry_run(
            dataset="ProductionConsumptionSettlement",
            price_area="DK1",
            limit=1,
            fetch=lambda url: {"records": []},
        )


def test_invalid_price_area_raises_value_error() -> None:
    with pytest.raises(ValueError):
        run_eds_dry_run(
            dataset="DayAheadPrices",
            price_area="SE3",
            limit=1,
            fetch=lambda url: {"records": []},
        )


def test_empty_records_returns_zero_normalized_records() -> None:
    summary = run_eds_dry_run(
        dataset="DayAheadPrices",
        price_area="DK1",
        limit=10,
        fetch=lambda url: {"records": []},
    )

    assert summary.raw_record_count == 0
    assert summary.normalized_record_count == 0
    assert summary.rejected_record_count == 0
    assert summary.normalized_records == []


def test_malformed_records_are_rejected_without_crashing() -> None:
    summary = run_eds_dry_run(
        dataset="DayAheadPrices",
        price_area="DK1",
        limit=3,
        fetch=lambda url: {
            "records": [
                {
                    "PriceArea": "DK1",
                    "TimeUTC": "2026-01-01T00:00:00",
                    "DayAheadPriceDKK": 512.34,
                    "DayAheadPriceEUR": 68.67,
                },
                {"PriceArea": "DK1", "TimeUTC": "2026-01-01T01:00:00"},
                "not-a-record",
            ]
        },
    )

    assert summary.raw_record_count == 3
    assert summary.normalized_record_count == 1
    assert summary.rejected_record_count == 2
