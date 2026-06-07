# Data Source Validation

This document records manually validated public API data sources for the v0.1 decision-support MVP. It documents observed responses only; it does not define ingestion, persistence, forecasting, dispatch, activation, or control behavior.

Validation date: 2026-06-08 local project validation session

## Validated Endpoints

### Energi Data Service - `DayAheadPrices`

Command:

```bash
python3 scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --limit 5
```

Result:

- HTTP status: 200
- Top-level keys: `dataset`, `filters`, `limit`, `records`, `total`
- Record count: 5
- Sample fields observed: `DayAheadPriceDKK`, `DayAheadPriceEUR`, `PriceArea`, `TimeDK`, `TimeUTC`

Important note: the unfiltered sample returned `PriceArea = DE`. Future ingestion must filter to `DK1` and `DK2`.

### Energi Data Service - `ElectricityProdex5MinRealtime`

Command:

```bash
python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --limit 5
```

Result:

- HTTP status: 200
- Top-level keys: `dataset`, `filters`, `limit`, `records`, `total`
- Record count: 5
- Sample fields observed: `Minutes5DK`, `Minutes5UTC`, `PriceArea`, `OnshoreWindPower`, `OffshoreWindPower`, `SolarPower`, `ProductionGe100MW`, `ProductionLt100MW`, `ExchangeGermany`, `ExchangeNorway`, `ExchangeSweden`, `ExchangeGreatBelt`, `ExchangeNetherlands`, `ExchangeGreatBritain`

Candidate use: primary candidate for near-real-time DK1/DK2 production, wind, solar, and exchange data.

### Energi Data Service - `ProductionConsumptionSettlement`

Command:

```bash
python3 scripts/validate_data_sources.py --source energi-data-service --dataset ProductionConsumptionSettlement --limit 5
```

Result:

- HTTP status: 200
- Top-level keys: `dataset`, `filters`, `limit`, `records`, `total`
- Record count: 5
- Sample fields observed: `HourDK`, `HourUTC`, `PriceArea`, `GrossConsumptionMWh`, `CentralPowerMWh`, `LocalPowerMWh`, `OffshoreWindGe100MW_MWh`, `OffshoreWindLt100MW_MWh`, `OnshoreWindGe50kW_MWh`, `OnshoreWindLt50kW_MWh`, `SolarPowerGe10Lt40kW_MWh`, `SolarPowerGe40kW_MWh`, `SolarPowerLt10kW_MWh`, `PowerToHeatMWh`, `ExchangeGE_MWh`, `ExchangeNO_MWh`, `ExchangeSE_MWh`

Candidate use: primary candidate for historical backtesting and settlement-level analysis.

### Energi Data Service - `ElectricityBalanceNonv`

Command:

```bash
python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityBalanceNonv --limit 5
```

Result:

- HTTP status: 200
- Top-level keys: `dataset`, `filters`, `limit`, `records`, `total`
- Record count: 5
- Sample fields observed: `HourDK`, `HourUTC`, `PriceArea`, `TotalLoad`, `OnshoreWindPower`, `OffshoreWindPower`, `SolarPower`, `Biomass`, `FossilGas`, `FossilHardCoal`, `FossilOil`, `HydroPower`, `Waste`, `OtherRenewable`

Candidate use: candidate for non-validated near-real-time electricity balance/load data.

### Elprisenligenu - `DK1`

Command:

```bash
python3 scripts/validate_data_sources.py --source elprisenligenu --date 2026-06-07 --price-area DK1
```

Result:

- HTTP status: 200
- Top-level JSON type: list
- Record count: 24
- Sample fields observed: `DKK_per_kWh`, `EUR_per_kWh`, `EXR`, `time_start`, `time_end`

### Elprisenligenu - `DK2`

Command:

```bash
python3 scripts/validate_data_sources.py --source elprisenligenu --date 2026-06-07 --price-area DK2
```

Result:

- HTTP status: 200
- Top-level JSON type: list
- Record count: 24
- Sample fields observed: `DKK_per_kWh`, `EUR_per_kWh`, `EXR`, `time_start`, `time_end`

## Initial Source Selection for MVP

- Spot prices: `DayAheadPrices` as primary, Elprisenligenu as secondary/backup.
- Near-real-time production and exchange: `ElectricityProdex5MinRealtime`.
- Historical backtesting: `ProductionConsumptionSettlement`.
- Near-real-time load/balance candidate: `ElectricityBalanceNonv`.
- Weather data remains unresolved and must be validated separately.

## Open Implementation Notes

- Add `DK1`/`DK2` filtering before ingestion.
- Confirm timestamp normalization to UTC.
- Confirm unit conversions between MW, MWh, EUR/MWh, and DKK/kWh.
- Confirm source licensing and attribution requirements.
- Confirm polling/update frequency before scheduled ingestion.
- Avoid treating Elprisenligenu as the primary source until stability and license are reviewed.
- No source should be used for automatic control or dispatch in v0.1.
