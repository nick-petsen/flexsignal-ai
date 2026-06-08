import pytest

from app.db.executor import execute_eds_write_plan


class RecordingCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, dict[str, object]]] = []

    def execute(self, sql: str, params: dict[str, object]) -> None:
        self.executed.append((sql, params))


def test_execute_eds_write_plan_uses_injected_cursor() -> None:
    spot_price_payload = {
        "price_area": "DK1",
        "timestamp_utc": "2026-01-01T00:00:00",
        "price_eur_per_mwh": 68.67,
        "price_dkk_per_mwh": 512.34,
        "source": "Energi Data Service:DayAheadPrices",
        "source_record_id": "DayAheadPrices:DK1:2026-01-01T00:00:00",
    }
    power_balance_payload = {
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
    cursor = RecordingCursor()

    summary = execute_eds_write_plan(
        write_plan=[
            {
                "table": "spot_prices",
                "operation": "upsert_preview",
                "payload": spot_price_payload,
            },
            {
                "table": "power_balance",
                "operation": "upsert_preview",
                "payload": power_balance_payload,
            },
        ],
        cursor=cursor,
    )

    assert summary.statement_count == 2
    assert summary.table_counts == {
        "power_balance": 1,
        "spot_prices": 1,
    }
    assert len(cursor.executed) == 2
    assert cursor.executed[0][0].startswith("INSERT INTO spot_prices")
    assert cursor.executed[0][1] == spot_price_payload
    assert cursor.executed[1][0].startswith("INSERT INTO power_balance")
    assert cursor.executed[1][1] == power_balance_payload


def test_execute_eds_write_plan_validates_full_batch_before_executing() -> None:
    cursor = RecordingCursor()

    with pytest.raises(ValueError, match="Unsupported EDS write-plan table"):
        execute_eds_write_plan(
            write_plan=[
                {
                    "table": "spot_prices",
                    "operation": "upsert_preview",
                    "payload": {
                        "price_area": "DK1",
                        "timestamp_utc": "2026-01-01T00:00:00",
                        "price_eur_per_mwh": 68.67,
                        "price_dkk_per_mwh": 512.34,
                        "source": "Energi Data Service:DayAheadPrices",
                        "source_record_id": (
                            "DayAheadPrices:DK1:2026-01-01T00:00:00"
                        ),
                    },
                },
                {
                    "table": "weather_observations",
                    "operation": "upsert_preview",
                    "payload": {},
                },
            ],
            cursor=cursor,
        )

    assert cursor.executed == []


def test_execute_eds_write_plan_allows_empty_plan() -> None:
    cursor = RecordingCursor()

    summary = execute_eds_write_plan(write_plan=[], cursor=cursor)

    assert summary.statement_count == 0
    assert summary.table_counts == {}
    assert cursor.executed == []
