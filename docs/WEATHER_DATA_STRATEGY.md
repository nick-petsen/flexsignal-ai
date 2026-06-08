# Weather Data Strategy

Weather data is required for the MVP forecast model, especially wind speed, wind direction, temperature, and cloud cover. No weather ingestion is implemented yet.

## Candidate Sources

### 1. DMI Open Data - Meteorological Observations

DMI Open Data meteorological observations are a candidate source for observed weather data.

Manual DMI/Open Data endpoint validation results are documented in [DMI Validation Results](DMI_VALIDATION_RESULTS.md).

They may support historical backtesting and feature validation with candidate fields including:

- wind speed
- wind direction
- temperature
- cloud cover

This source requires separate validation before ingestion.

Candidate DMI endpoints can be manually validated with:

```bash
scripts/validate_data_sources.py --source dmi-url --url "<DMI_URL>"
```

No DMI endpoint is selected yet.

### 2. DMI Open Data - Forecast Data EDR

DMI Open Data Forecast Data EDR is a candidate source for weather forecast data.

It may support 24-72 hour surplus-risk forecasting with candidate fields including:

- forecasted wind speed
- forecasted wind direction
- forecasted temperature
- forecasted cloud cover

This source requires separate validation before ingestion.

### 3. Alternative Fallback Source

A simpler public weather API may be considered for early MVP validation if DMI integration becomes too complex.

Any fallback source must be documented before use.

## Required Weather Features for MVP

- `wind_speed_mps`
- `wind_direction_deg`
- `temperature_c`
- `cloud_cover_pct`
- `timestamp_utc`
- `location_id` or grid reference
- `source`
- `source_record_id` where available

## DK1/DK2 Weather Mapping Challenge

DK1 and DK2 are electricity bidding zones, not single weather points.

Weather data must be mapped to representative locations, weather stations, or grid areas. The initial MVP may use a small set of representative locations per price area. Final mapping must be documented before ingestion.

## Proposed MVP Approach

- Start with a small, explainable mapping.
- Use representative locations or grid points for DK1 and DK2.
- Keep weather features nullable in the database until validated.
- Do not use weather data as the only driver of surplus-risk scoring.
- Combine weather with production, consumption, price, and exchange data.

## Open Questions

- Which DMI endpoint is easiest to validate first?
- Is an API key required for the selected endpoint?
- Which stations/grid points represent DK1 and DK2?
- How should weather forecasts be aligned to electricity timestamps?
- What update frequency is acceptable?
- How should missing weather values be handled?
- Should Open-Meteo or another fallback be evaluated for early testing?

## Compliance Boundary

- Weather data is used only for forecasting and decision support.
- Weather data must not trigger automatic control.
- Weather data must not generate dispatch or activation instructions.
- All recommendations remain read-only and require human review.
