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
