# Data Sources

## Focus Area

The initial platform scope is the Danish electricity system with focus on DK1 and DK2.

## Energi Data Service

Energi Data Service is a planned primary source for Danish electricity market and system data.

Planned datasets may include:

- Day-ahead prices
- Production by type
- Consumption
- Exchange flows
- Grid area data relevant to DK1 and DK2
- Balancing or reserve-related signals where appropriate for read-only analysis

Update frequency: TODO, depends on selected datasets.

## Candidate API Sources

Candidate endpoints can be manually validated with `scripts/validate_data_sources.py` before ingestion code is implemented.

### Energi Data Service

Energi Data Service is the primary candidate source for Danish energy system data.

API base pattern:

```text
https://api.energidataservice.dk/dataset/{datasetName}
```

The API requires exact dataset names. Do not assume `PowerProduction` is a valid dataset; it returned "table not found" during manual browser testing.

Candidate datasets to investigate:

- `ElectricityProdex5MinRealtime`: electricity production and exchange in MW, 5-minute resolution, updated every 5 minutes.
- `DayAheadPrices`: day-ahead spot prices for DK1/DK2 and neighboring bidding zones.
- `ProductionConsumptionSettlement`: production and consumption settlement data, useful for historical backtesting.
- `ElectricityBalanceNonv`: non-validated electricity balance data, useful for near-real-time features.

API usage must respect each dataset's update frequency and avoid unnecessary polling.

### Elprisenligenu

Elprisenligenu is a secondary or backup candidate source for Danish electricity spot prices.

API pattern:

```text
https://www.elprisenligenu.dk/api/v1/prices/[YEAR]/[MONTH]-[DAY]_[PRICE_AREA].json
```

`PRICE_AREA` is `DK1` or `DK2`.

Example resolved URL format:

```text
https://www.elprisenligenu.dk/api/v1/prices/2026/06-07_DK1.json
```

Placeholders must be replaced before testing in a browser. The API may return `404` if data is not ready. Prices are without VAT and taxes.

Treat Elprisenligenu as a secondary source until license, stability, and data quality are reviewed.

## Open Questions

- Which Energi Data Service datasets should be primary for v0.1?
- Should spot prices come from `DayAheadPrices` or Elprisenligenu?
- What polling/update frequency is acceptable for each source?
- Which fields are required for surplus-risk scoring?
- What data should be stored for backtesting?

## DMI / Weather Data

DMI and other weather data sources may support forecasting through weather features.

Planned weather data may include:

- Wind speed and direction
- Temperature
- Solar irradiance or cloud cover
- Precipitation
- Forecast horizons relevant to electricity demand and renewable production

Update frequency: TODO, depends on selected datasets and provider access.

## Planned Datasets

- Historical electricity prices for DK1 and DK2
- Historical production and consumption
- Weather observations
- Weather forecasts
- Renewable production indicators
- Calendar features such as weekday, weekend, holiday, and season

## Data Quality Considerations

- Missing values
- Delayed updates
- Source outages
- Timestamp alignment
- Time zone handling
- DK1/DK2 market-area consistency
- Duplicate records
- Unit consistency
- Sudden source schema changes
