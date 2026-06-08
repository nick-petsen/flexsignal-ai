# Data Field Mapping

This document maps validated public API fields to the internal MVP schema before ingestion is implemented. It is a planning document only; it does not define ingestion code, database writes, new API endpoints, forecasting logic, or operational workflows.

## General Mapping Rules

- All timestamps must be stored as UTC.
- DK1/DK2 filtering is required before ingestion.
- Source dataset name must be stored with each record.
- Source record identifiers are optional until stable source IDs are confirmed.
- Unit conversions must be explicit and tested.
- No field may represent control signals, dispatch instructions, asset activation, or operational commands in v0.1.

## spot_prices

### Energi Data Service: DayAheadPrices

Map `DayAheadPrices` to `spot_prices`:

| Source field | Target field | Notes |
| --- | --- | --- |
| `PriceArea` | `price_area` | Filter to `DK1` and `DK2` only. |
| `TimeUTC` | `timestamp_utc` | Store as UTC. |
| `DayAheadPriceEUR` | `price_eur_per_mwh` | Confirm source unit before ingestion. |
| `DayAheadPriceDKK / 1000` | `price_dkk_per_kwh` | Confirm whether `DayAheadPriceDKK` is DKK/MWh before final ingestion. |
| source constant | `source` | Use `Energi Data Service:DayAheadPrices`. |
| TODO | `source_record_id` | Optional until stable source IDs are confirmed. |
| ingestion timestamp | `ingested_at_utc` | Capture when ingestion later writes the record. |

Notes:

- Filter `PriceArea` to `DK1` and `DK2` only.
- Unfiltered validation returned `PriceArea = DE`, so filtering is mandatory.
- Confirm whether `DayAheadPriceDKK` is DKK/MWh before final ingestion.

### Elprisenligenu

Map Elprisenligenu to `spot_prices` as a secondary or backup source:

| Source field | Target field | Notes |
| --- | --- | --- |
| CLI/input URL price area | `price_area` | Must be `DK1` or `DK2`. |
| `time_start` | `timestamp_utc` | Normalize timezone before storing. |
| `EUR_per_kWh * 1000` | `price_eur_per_mwh` | Explicit unit conversion required. |
| `DKK_per_kWh` | `price_dkk_per_kwh` | No conversion required if source unit is confirmed. |
| source constant | `source` | Use `Elprisenligenu`. |
| TODO | `source_record_id` | Optional until stable source IDs are confirmed. |

Notes:

- Treat as secondary or backup until license, stability, and data quality are reviewed.

## power_balance

### Energi Data Service: ElectricityProdex5MinRealtime

Map `ElectricityProdex5MinRealtime` to `power_balance`:

| Source field | Target field | Notes |
| --- | --- | --- |
| `PriceArea` | `price_area` | Filter to `DK1` and `DK2` only. |
| `Minutes5UTC` | `timestamp_utc` | Store as UTC. |
| `OnshoreWindPower` | `wind_onshore_mw` | Confirm unit before ingestion. |
| `OffshoreWindPower` | `wind_offshore_mw` | Confirm unit before ingestion. |
| `SolarPower` | `solar_mw` | Confirm unit before ingestion. |
| `ProductionGe100MW + ProductionLt100MW + OnshoreWindPower + OffshoreWindPower + SolarPower` | `production_mw` | Candidate calculation; must be verified. |
| `ExchangeGermany + ExchangeNorway + ExchangeSweden + ExchangeGreatBelt + ExchangeNetherlands + ExchangeGreatBritain` | `exchange_net_mw` | Candidate calculation; sign convention must be verified. |
| source constant | `source` | Use `Energi Data Service:ElectricityProdex5MinRealtime`. |
| TODO | `source_record_id` | Optional until stable source IDs are confirmed. |
| ingestion timestamp | `ingested_at_utc` | Capture when ingestion later writes the record. |

Notes:

- Consumption is not clearly present in this dataset, so `consumption_mw` remains nullable unless mapped later.
- Exchange sign convention must be documented before using it for risk scoring.

### Energi Data Service: ElectricityBalanceNonv

Map `ElectricityBalanceNonv` to `power_balance` as a candidate load and balance source:

| Source field | Target field | Notes |
| --- | --- | --- |
| `PriceArea` | `price_area` | Filter to `DK1` and `DK2` only. |
| `HourUTC` | `timestamp_utc` | Store as UTC. |
| `TotalLoad` | `consumption_mw` | Confirm unit before ingestion. |
| `OnshoreWindPower` | `wind_onshore_mw` | Confirm unit before ingestion. |
| `OffshoreWindPower` | `wind_offshore_mw` | Confirm unit before ingestion. |
| `SolarPower` | `solar_mw` | Confirm unit before ingestion. |
| `Biomass + FossilGas + FossilHardCoal + FossilOil + HydroPower + Waste + OtherRenewable + OnshoreWindPower + OffshoreWindPower + SolarPower` | `production_mw` | Candidate calculation; must be verified. |
| source constant | `source` | Use `Energi Data Service:ElectricityBalanceNonv`. |

## backtesting source mapping

Map `ProductionConsumptionSettlement` for historical backtesting:

| Source field | Target concept | Notes |
| --- | --- | --- |
| `PriceArea` | `price_area` | Filter to `DK1` and `DK2` only. |
| `HourUTC` | `timestamp_utc` | Store as UTC. |
| `GrossConsumptionMWh` | historical consumption energy | MWh value. |
| `OnshoreWindGe50kW_MWh + OnshoreWindLt50kW_MWh` | historical onshore wind energy | Candidate calculation. |
| `OffshoreWindGe100MW_MWh + OffshoreWindLt100MW_MWh` | historical offshore wind energy | Candidate calculation. |
| `SolarPowerGe10Lt40kW_MWh + SolarPowerGe40kW_MWh + SolarPowerLt10kW_MWh + SolarPowerSelfConMWh` | historical solar energy | Candidate calculation. |
| `ExchangeGE_MWh + ExchangeNO_MWh + ExchangeSE_MWh + ExchangeGB_MWh + ExchangeNL_MWh + ExchangeGreatBelt_MWh` | historical exchange candidate calculation | Sign convention must be verified. |

Notes:

- This dataset is MWh, not MW.
- It should be used carefully for backtesting and may require separate derived tables later.
- Do not force MWh into MW fields without an explicit interval conversion.

## weather_observations

Weather source mapping remains unresolved.

- DMI or another weather API must be validated separately.
- Required candidate fields are wind speed, wind direction, temperature, and cloud cover.
- Mapping remains TODO.

## surplus_risk_forecasts

This table stores model outputs, not raw source data.

- Field mapping depends on the future baseline risk model.
- LLM explanations may populate `explanation_text` only after deterministic or model outputs exist.
- LLM output must not be the primary forecast or sole decision engine.

## Open Questions Before Ingestion

- Confirm Energi Data Service unit definitions for each selected dataset.
- Confirm exchange sign conventions.
- Confirm final DK1/DK2 filter syntax.
- Confirm whether `DayAheadPrices` or Elprisenligenu should be used for first spot price ingestion.
- Confirm how to handle duplicate records and late-arriving updates.
- Confirm whether backtesting requires separate historical tables or derived views.
- Confirm DMI/weather API source and field mapping.
