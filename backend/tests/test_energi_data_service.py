import pytest

from app.integrations.energi_data_service import build_eds_url, extract_records


ENCODED_DK1_FILTER = "filter=%7B%22PriceArea%22%3A%5B%22DK1%22%5D%7D"
ENCODED_DK2_FILTER = "filter=%7B%22PriceArea%22%3A%5B%22DK2%22%5D%7D"


def test_day_ahead_prices_dk1_url_contains_dataset_limit_and_filter() -> None:
    url = build_eds_url("DayAheadPrices", price_area="DK1", limit=250)

    assert url.startswith("https://api.energidataservice.dk/dataset/DayAheadPrices?")
    assert "limit=250" in url
    assert ENCODED_DK1_FILTER in url


def test_day_ahead_prices_dk2_url_contains_filter() -> None:
    url = build_eds_url("DayAheadPrices", price_area="DK2")

    assert ENCODED_DK2_FILTER in url


def test_electricity_prodex_5_min_realtime_dk1_url_works() -> None:
    url = build_eds_url("ElectricityProdex5MinRealtime", price_area="DK1")

    assert url.startswith(
        "https://api.energidataservice.dk/dataset/ElectricityProdex5MinRealtime?"
    )
    assert "limit=100" in url
    assert ENCODED_DK1_FILTER in url


def test_url_without_price_area_includes_limit_and_no_filter() -> None:
    url = build_eds_url("DayAheadPrices", limit=10)

    assert url == "https://api.energidataservice.dk/dataset/DayAheadPrices?limit=10"
    assert "filter=" not in url


def test_invalid_dataset_raises_value_error() -> None:
    with pytest.raises(ValueError):
        build_eds_url("UnsupportedDataset")


def test_invalid_price_area_raises_value_error() -> None:
    with pytest.raises(ValueError):
        build_eds_url("DayAheadPrices", price_area="SE3")


@pytest.mark.parametrize("limit", [0, 10_001])
def test_invalid_limit_raises_value_error(limit: int) -> None:
    with pytest.raises(ValueError):
        build_eds_url("DayAheadPrices", limit=limit)


def test_extract_records_returns_records() -> None:
    records = [{"PriceArea": "DK1"}, {"PriceArea": "DK2"}]

    assert extract_records({"records": records}) == records


@pytest.mark.parametrize("payload", [{}, {"records": None}, {"records": {}}])
def test_extract_records_rejects_missing_or_invalid_records(payload: dict) -> None:
    with pytest.raises(ValueError):
        extract_records(payload)
