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

Unit note: `DayAheadPriceDKK` and `DayAheadPriceEUR` are treated as
MWh-based internal spot price values for future schema mapping.

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

Unit note: Elprisenligenu exposes kWh-based spot price fields. Any future
ingestion must explicitly convert them to MWh-based internal spot price values.

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

Unit note: Elprisenligenu exposes kWh-based spot price fields. Any future
ingestion must explicitly convert them to MWh-based internal spot price values.

## Energi Data Service PriceArea Filter Validation

Manual validation was performed for Energi Data Service `PriceArea` filtering
with both `DK1` and `DK2`.

Validated filter syntax:

```text
filter={"PriceArea":["DK1"]}
filter={"PriceArea":["DK2"]}
```

The following manual validation commands returned HTTP 200, record count 5, and
sample records with the expected `PriceArea`:

| Dataset | PriceArea | Command | Result |
| --- | --- | --- | --- |
| `DayAheadPrices` | `DK1` | `python3 scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --price-area DK1 --limit 5` | HTTP 200; record count 5; sample record `PriceArea` was `DK1`. |
| `DayAheadPrices` | `DK2` | `python3 scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --price-area DK2 --limit 5` | HTTP 200; record count 5; sample record `PriceArea` was `DK2`. |
| `ElectricityProdex5MinRealtime` | `DK1` | `python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --price-area DK1 --limit 5` | HTTP 200; record count 5; sample record `PriceArea` was `DK1`. |
| `ElectricityProdex5MinRealtime` | `DK2` | `python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --price-area DK2 --limit 5` | HTTP 200; record count 5; sample record `PriceArea` was `DK2`. |

Any future ingestion for DK1/DK2 Energi Data Service datasets must use this
`PriceArea` filtering. This validation does not add ingestion, persistence,
forecasting, dispatch, activation, or control behavior.

## Energi Data Service Normalized Preview

The manual `scripts/preview_eds_normalized_records.py` helper can be used to
preview how `DayAheadPrices` and `ElectricityProdex5MinRealtime` records
normalize after applying the validated DK1/DK2 `PriceArea` filter. It performs a
single read-only HTTP `GET`, prints the final request URL, status, raw count,
normalized count, and compact normalized JSON lines.

This helper is not ingestion, persistence, scheduling, forecasting, dispatch,
activation, or control behavior. It does not expose an API and must remain a
manual validation aid only.

## Energi Data Service Write-Plan Preview

The manual `scripts/preview_eds_write_plan.py` helper can be used to preview how
`DayAheadPrices` and `ElectricityProdex5MinRealtime` records would map into
database write-plan entries after applying the validated DK1/DK2 `PriceArea`
filter. It performs a single read-only HTTP `GET`, prints the final request URL,
HTTP status, raw count, normalized count, write-plan entry count, and compact
write-plan JSON lines.

This helper is manual preview only. It does not connect to a database, execute
SQL, write records, create ingestion jobs, run automatically, expose an API
endpoint, schedule polling, forecast, dispatch, activate, or control energy
assets.

Manual read-only validation was performed for the current write-plan preview
mapping with both `DK1` and `DK2`.

| Dataset | PriceArea | Command | Result |
| --- | --- | --- | --- |
| `DayAheadPrices` | `DK1` | `python3 scripts/preview_eds_write_plan.py --dataset DayAheadPrices --price-area DK1 --limit 2` | HTTP 200; raw records 2; normalized records 2; write-plan entries 2; target table `spot_prices`; operations `upsert_preview`. |
| `DayAheadPrices` | `DK2` | `python3 scripts/preview_eds_write_plan.py --dataset DayAheadPrices --price-area DK2 --limit 2` | HTTP 200; raw records 2; normalized records 2; write-plan entries 2; target table `spot_prices`; operations `upsert_preview`. |
| `ElectricityProdex5MinRealtime` | `DK1` | `python3 scripts/preview_eds_write_plan.py --dataset ElectricityProdex5MinRealtime --price-area DK1 --limit 2` | HTTP 200; raw records 2; normalized records 2; write-plan entries 2; target table `power_balance`; operations `upsert_preview`. |
| `ElectricityProdex5MinRealtime` | `DK2` | `python3 scripts/preview_eds_write_plan.py --dataset ElectricityProdex5MinRealtime --price-area DK2 --limit 2` | HTTP 200; raw records 2; normalized records 2; write-plan entries 2; target table `power_balance`; operations `upsert_preview`. |

All four preview runs generated in-memory write-plan entries only. No SQL was
generated, no database connection was opened, and no database writes were
performed.

Important note: `ElectricityProdex5MinRealtime` write-plan entries currently
have `consumption_mw = null`. This is expected because the selected realtime
production dataset does not provide a clear consumption field. Consumption must
be sourced later from a separate validated dataset before surplus-risk scoring
depends on consumption.

## Energi Data Service Dry-Run Ingestion Validation

The backend includes a controlled dry-run module at
`backend/app/ingestion/eds_dry_run.py` for validating `DayAheadPrices` and
`ElectricityProdex5MinRealtime` normalization before any persistence workflow is
implemented. It builds the validated Energi Data Service request URL, requires a
DK1 or DK2 `PriceArea`, accepts an injectable fetch function, extracts records,
normalizes supported records, and returns counts for raw, normalized, and
rejected records.

The dry-run module does not write to the database, run automatically, expose an
API endpoint, schedule polling, forecast, dispatch, activate, or control energy
assets. Current tests use mocked payloads only.

## Initial Source Selection for MVP

- Spot prices: `DayAheadPrices` as primary, Elprisenligenu as secondary/backup.
- Near-real-time production and exchange: `ElectricityProdex5MinRealtime`.
- Historical backtesting: `ProductionConsumptionSettlement`.
- Near-real-time load/balance candidate: `ElectricityBalanceNonv`.
- Weather data remains unresolved and must be validated separately.

## Open Implementation Notes

- Add `DK1`/`DK2` filtering before ingestion.
- Use the manually validated Energi Data Service `PriceArea` filter syntax for `DayAheadPrices` and `ElectricityProdex5MinRealtime` ingestion.
- Confirm timestamp normalization to UTC.
- Confirm unit conversions between MW, MWh, EUR/MWh, DKK/MWh, and kWh-based source spot price fields.
- Confirm source licensing and attribution requirements.
- Confirm polling/update frequency before scheduled ingestion.
- Avoid treating Elprisenligenu as the primary source until stability and license are reviewed.
- No source should be used for automatic control or dispatch in v0.1.
