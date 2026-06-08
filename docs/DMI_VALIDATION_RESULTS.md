# DMI Validation Results

Manual validation date: 2026-06-08 local project validation session.

This document records manually validated DMI/Open Data endpoints only. It does not define ingestion code, database writes, API endpoints, forecasting logic, control behavior, dispatch workflows, activation workflows, or operational functionality.

## Validated Endpoints

### 1. DMI metObs collections

Command:

```bash
python3 scripts/validate_data_sources.py --source dmi-url --url "https://opendataapi.dmi.dk/v2/metObs/collections"
```

Result:

- HTTP status: 200
- Top-level keys: `collections`, `links`
- Record count: not obvious
- Sample record: not available

Candidate use:

- Discovery endpoint for DMI meteorological observation collections.

### 2. DMI metObs stations

Command:

```bash
python3 scripts/validate_data_sources.py --source dmi-url --url "https://opendataapi.dmi.dk/v2/metObs/collections/station/items?limit=1"
```

Result:

- HTTP status: 200
- Top-level keys: `features`, `links`, `numberReturned`, `timeStamp`, `type`
- Record count: 1
- Sample fields observed:
  - `geometry.coordinates`
  - `id`
  - `properties.stationId`
  - `properties.name`
  - `properties.country`
  - `properties.parameterId`
  - `properties.status`
  - `properties.type`
  - `properties.validFrom`
  - `properties.validTo`

Important note:

- The unfiltered sample returned a Greenland station.
- Future station selection must filter to representative Danish stations or grid points for DK1 and DK2.

### 3. DMI metObs observations

Command:

```bash
python3 scripts/validate_data_sources.py --source dmi-url --url "https://opendataapi.dmi.dk/v2/metObs/collections/observation/items?limit=1&sortorder=observed,DESC"
```

Result:

- HTTP status: 200
- Top-level keys: `features`, `links`, `numberReturned`, `timeStamp`, `type`
- Record count: 1
- Sample fields observed:
  - `geometry.coordinates`
  - `id`
  - `properties.created`
  - `properties.observed`
  - `properties.parameterId`
  - `properties.stationId`
  - `properties.value`
- Sample parameter observed: `humidity`

Candidate use:

- Candidate source for observed weather features.
- Future validation must test `wind_speed`, `wind_dir`, `temp_dry`, and `cloud_cover`.

### 4. DMI forecastdata HARMONIE DINI SF

Command:

```bash
python3 scripts/validate_data_sources.py --source dmi-url --url "https://opendataapi.dmi.dk/v1/forecastdata/collections/harmonie_dini_sf/items?limit=1"
```

Result:

- HTTP status: 200
- Top-level keys: `features`, `links`, `numberReturned`, `timeStamp`, `type`
- Record count: 1
- Sample fields observed:
  - `asset.data.href`
  - `asset.data.type`
  - `bbox`
  - `collection`
  - `geometry`
  - `id`
  - `properties.created`
  - `properties.datetime`
  - `properties.modelRun`
  - `stac_version`
  - `type`

Important note:

- This endpoint returns a GRIB forecast file reference, not simple JSON weather feature values.
- Forecast ingestion from this source is likely more complex than metObs observation ingestion.
- Do not select this as the first MVP weather forecast source until GRIB parsing or an easier forecast endpoint is evaluated.

## Initial Weather Source Assessment

- DMI metObs observation endpoints are validated and likely suitable for observed weather/backtesting features.
- DMI station endpoint is validated but requires DK1/DK2 representative station selection.
- DMI forecastdata endpoint is validated but returns GRIB file references, so it may be too complex for the first MVP ingestion step.
- Weather forecast source remains unresolved.
- A simpler fallback forecast API may be evaluated later if DMI forecast integration is too heavy for MVP.

## Open Questions Before Weather Ingestion

- Which Danish stations should represent DK1 and DK2?
- How should station coordinates be mapped to electricity price areas?
- Which parameters should be queried first: `wind_speed`, `wind_dir`, `temp_dry`, `cloud_cover`?
- What DMI filter syntax should be used for `stationId`, `parameterId`, and time range?
- Is GRIB parsing acceptable for MVP, or should a simpler forecast source be used first?
- How should observation timestamps align to electricity market timestamps?
- How should missing weather values be handled?

## Compliance Boundary

- DMI weather data is used only for forecasting and decision support.
- DMI weather data must not trigger automatic control.
- DMI weather data must not generate dispatch or activation instructions.
- All recommendations remain read-only and require human review.
