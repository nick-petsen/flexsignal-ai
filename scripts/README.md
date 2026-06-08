# Data Source Validation Scripts

`validate_data_sources.py` is for manual validation of candidate public data source APIs before ingestion code is implemented.

The script performs one read-only HTTP `GET` request per run. It does not store data, write to the database, create ingestion jobs, or modify application behavior.

Verified datasets and endpoints must be documented before ingestion is implemented. Any future polling frequency must respect the source update frequency and avoid unnecessary requests.

## Examples

```bash
python scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --limit 5
python scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --limit 5
python scripts/validate_data_sources.py --source elprisenligenu --date 2026-06-07 --price-area DK1
```

Energi Data Service datasets can also be manually validated with a `PriceArea`
filter:

```bash
python3 scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --price-area DK1 --limit 5
python3 scripts/validate_data_sources.py --source energi-data-service --dataset DayAheadPrices --price-area DK2 --limit 5
python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --price-area DK1 --limit 5
python3 scripts/validate_data_sources.py --source energi-data-service --dataset ElectricityProdex5MinRealtime --price-area DK2 --limit 5
```

## DMI Validation

DMI Open Data validation is manual and read-only. The validator only performs a
single HTTP `GET` request against a pasted DMI Open Data URL and prints a compact
response summary. It does not store data, create ingestion jobs, or change
application behavior.

Paste a candidate DMI Open Data URL from the DMI documentation:

```bash
python scripts/validate_data_sources.py --source dmi-url --url "https://opendataapi.dmi.dk/..."
```

DMI endpoints must be documented before any ingestion implementation is added.
