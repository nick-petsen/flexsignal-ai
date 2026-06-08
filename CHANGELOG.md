# Changelog

## v0.1.0 - TODO

- Added a pure parameterized SQL builder for Energi Data Service write-plan
  preview entries targeting `spot_prices` and `power_balance`, without database
  connections, execution, writes, ingestion jobs, or runtime startup changes.
- Documented manual read-only Energi Data Service write-plan preview validation
  for `DayAheadPrices` and `ElectricityProdex5MinRealtime` DK1/DK2 records,
  including the expected null `consumption_mw` value for the selected realtime
  production dataset.
- Added a manual read-only Energi Data Service write-plan preview script for
  `DayAheadPrices` and `ElectricityProdex5MinRealtime` DK1/DK2 records without
  database connections, SQL generation, or writes.
- Added a pure dry-run Energi Data Service database write-plan builder for
  `spot_prices` and `power_balance` preview entries without SQL generation or
  database writes.
- Added pure Energi Data Service record-to-database payload repository helpers
  for `spot_prices` and `power_balance` with mocked/unit tests and no database
  writes.
- Fixed backend package discovery so Alembic migrations are not installed as an application package.
- Added a controlled Energi Data Service dry-run ingestion module with mocked
  unit tests and no database writes.
- Added an Alembic initial migration baseline for the documented database schema.
- Initial project structure.
- Initial documentation baseline.
- Read-only decision-support scope defined.
- No frontend, database runtime, or infrastructure implementation yet.
