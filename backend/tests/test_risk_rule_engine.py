import pytest

from app.risk import calculate_surplus_risk


def test_high_risk_with_negative_price_and_high_renewable_share() -> None:
    result = calculate_surplus_risk(
        {
            "price_area": "DK1",
            "timestamp_utc": "2026-01-01T00:00:00Z",
            "price_dkk_per_mwh": -25,
            "production_mw": 100,
            "consumption_mw": 80,
            "wind_onshore_mw": 50,
            "wind_offshore_mw": 30,
            "solar_mw": 5,
        }
    )

    assert result["risk_level"] == "high"
    assert result["risk_score"] == 75
    assert result["confidence_score"] == 1.0
    assert "NEGATIVE_PRICE" in result["reason_codes"]
    assert "HIGH_RENEWABLE_SHARE" in result["reason_codes"]


def test_medium_risk_with_low_price_and_moderate_renewable_share() -> None:
    result = calculate_surplus_risk(
        {
            "price_area": "DK2",
            "timestamp_utc": "2026-01-01T01:00:00Z",
            "price_dkk_per_mwh": 50,
            "production_mw": 100,
            "consumption_mw": 90,
            "wind_onshore_mw": 30,
            "wind_offshore_mw": 25,
            "solar_mw": 5,
        }
    )

    assert result["risk_level"] == "medium"
    assert result["risk_score"] == 45
    assert "LOW_PRICE" in result["reason_codes"]
    assert "MODERATE_RENEWABLE_SHARE" in result["reason_codes"]


def test_low_risk_with_normal_price_and_low_renewable_share() -> None:
    result = calculate_surplus_risk(
        {
            "price_area": "DK1",
            "timestamp_utc": "2026-01-01T02:00:00Z",
            "price_dkk_per_mwh": 500,
            "production_mw": 100,
            "consumption_mw": 95,
            "wind_onshore_mw": 10,
            "wind_offshore_mw": 5,
            "solar_mw": 5,
        }
    )

    assert result["risk_level"] == "low"
    assert result["risk_score"] == 0
    assert "NORMAL_PRICE" in result["reason_codes"]
    assert "LOW_RENEWABLE_SHARE" in result["reason_codes"]


def test_missing_price_lowers_confidence() -> None:
    result = calculate_surplus_risk(
        {
            "price_area": "DK1",
            "timestamp_utc": "2026-01-01T03:00:00Z",
            "production_mw": 100,
            "consumption_mw": 95,
            "wind_onshore_mw": 20,
            "wind_offshore_mw": 10,
            "solar_mw": 10,
        }
    )

    assert result["confidence_score"] == 0.75
    assert "MISSING_PRICE" in result["reason_codes"]


def test_missing_renewable_or_production_data_lowers_confidence() -> None:
    result = calculate_surplus_risk(
        {
            "price_area": "DK2",
            "timestamp_utc": "2026-01-01T04:00:00Z",
            "price_dkk_per_mwh": 75,
            "consumption_mw": 95,
        }
    )

    assert result["confidence_score"] == 0.70
    assert "MISSING_PRODUCTION_OR_RENEWABLE_DATA" in result["reason_codes"]


def test_invalid_price_area_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_surplus_risk(
            {
                "price_area": "SE3",
                "timestamp_utc": "2026-01-01T05:00:00Z",
            }
        )


def test_invalid_negative_production_rejected() -> None:
    with pytest.raises(ValueError):
        calculate_surplus_risk(
            {
                "price_area": "DK1",
                "timestamp_utc": "2026-01-01T06:00:00Z",
                "production_mw": -1,
            }
        )


def test_exchange_net_mw_does_not_drive_score_in_v0() -> None:
    base_input = {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T07:00:00Z",
        "price_dkk_per_mwh": 50,
        "production_mw": 100,
        "consumption_mw": 90,
        "wind_onshore_mw": 20,
        "wind_offshore_mw": 20,
        "solar_mw": 20,
    }

    positive_exchange = calculate_surplus_risk(
        {**base_input, "exchange_net_mw": 5000}
    )
    negative_exchange = calculate_surplus_risk(
        {**base_input, "exchange_net_mw": -5000}
    )

    assert positive_exchange["risk_score"] == negative_exchange["risk_score"]
    assert positive_exchange["risk_level"] == negative_exchange["risk_level"]
    assert "EXCHANGE_NET_NOT_USED_V0" in positive_exchange["reason_codes"]


def test_output_always_includes_decision_support_only_true() -> None:
    result = calculate_surplus_risk(
        {
            "price_area": "DK1",
            "timestamp_utc": "2026-01-01T08:00:00Z",
        }
    )

    assert result["decision_support_only"] is True


def test_risk_score_is_capped_at_100() -> None:
    result = calculate_surplus_risk(
        {
            "price_area": "DK2",
            "timestamp_utc": "2026-01-01T09:00:00Z",
            "price_dkk_per_mwh": -1000,
            "production_mw": 1,
            "consumption_mw": 1,
            "wind_onshore_mw": 10,
            "wind_offshore_mw": 10,
            "solar_mw": 10,
        }
    )

    assert result["risk_score"] <= 100
