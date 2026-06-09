# FlexSignal AI

FlexSignal AI is an Azure-hosted forecasting and decision-support platform for the Danish electricity system, initially focused on DK1 and DK2.

Version `v0.1` is read-only decision support. The platform may forecast, visualize, explain, and recommend actions for human review, but it must not automatically control electricity consumption or send control signals to assets, plants, devices, or energy infrastructure.

## MVP Scope

- Forecast electricity surplus risk for DK1 and DK2.
- Visualize forecast windows, confidence, and expected economic potential.
- Explain model output and recommendations in clear text.
- Support human decision-making with auditable recommendations.
- Keep LLM usage limited to explanation, reporting, and recommendation text.

## Not Included in v0.1

- Automatic activation of consumption or flexibility.
- Live control signals to any assets, plants, devices, or energy infrastructure.
- Critical operational system responsibilities.
- LLMs as the primary forecasting engine or sole decision-making component.
- Production infrastructure deployment.
- Runtime database integration or migrations.
- Production-ready frontend workflows.

## Technology Stack

- Frontend: Next.js and TypeScript
- Backend: Python FastAPI
- Database: PostgreSQL with TimescaleDB
- Data jobs: Azure Functions or Azure Container Apps Jobs
- Hosting: Azure App Service or Azure Container Apps
- Secrets: Azure Key Vault
- Logs: Application Insights and Log Analytics
- Auth: Microsoft Entra ID
- AI/LLM: explanation and report generation only

## Database Schema

A documented PostgreSQL/TimescaleDB schema baseline is available in
[`docs/DATABASE_SCHEMA.md`](docs/DATABASE_SCHEMA.md). The schema is not yet wired
into the FastAPI application and no database migrations are run in `v0.1`.

## Backend Local Development

The current backend is a minimal FastAPI API for `v0.1` read-only decision support. It does not include control endpoints, authentication, runtime database code, data ingestion, forecasting logic, or infrastructure deployment.

From the `backend/` directory:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Backend tests also run in GitHub Actions on pull requests and pushes to `main`.

Start the API locally:

```bash
uvicorn app.main:app --reload
```

### Local risk preview API smoke test

Manual local validation was documented with the backend started manually:

```bash
python -m uvicorn app.main:app --reload
```

The valid smoke test posted caller-provided JSON only to
`POST /api/risk/preview`:

```json
{
  "price_area": "DK1",
  "timestamp_utc": "2026-06-09T21:45:00+02:00",
  "price_dkk_per_mwh": -10,
  "production_mw": 1000,
  "wind_onshore_mw": 500,
  "wind_offshore_mw": 350,
  "solar_mw": 50,
  "consumption_mw": 900
}
```

Observed local result:

- `risk_level`: `high`
- `risk_score`: `75`
- `confidence_score`: `1.0`
- `reason_codes` included `NEGATIVE_PRICE` and `HIGH_RENEWABLE_SHARE`
- `model_version`: `rule-engine-v0`
- `decision_support_only`: `true`

An invalid input smoke test using `price_area` `SE3` returned a validation
error. Only `DK1` and `DK2` are accepted.

Important boundary notes:

- The risk preview endpoint used caller-provided JSON only.
- No database connection was used.
- No database writes were performed.
- No live Energi Data Service polling was performed.
- No LLM or ML model was used.
- No automatic control, dispatch, activation, or operational functionality
  exists.

## Frontend Local Development

The frontend is a minimal Next.js dashboard for `v0.1` read-only decision
support. It includes a DK1/DK2 selector and manual buttons for loading recent
spot prices and power balance rows from the existing backend read-only energy
API endpoints. It does not fetch automatically on page load, poll live
endpoints, call Energi Data Service directly, forecast, dispatch, activate, or
control energy assets.

From the `frontend/` directory:

```bash
npm install
npm run build
npm run dev
```

The frontend uses a backend API base URL helper for manual read-only API
requests. It defaults to `http://127.0.0.1:8000` and can be overridden with
`NEXT_PUBLIC_API_BASE_URL`.

Manual frontend requests use:

- `GET /api/energy/spot-prices?price_area=DK1|DK2&limit=5`
- `GET /api/energy/power-balance?price_area=DK1|DK2&limit=5`

The read-only disclaimer remains visible in the dashboard:
`Read-only decision support — no automatic control`.

### Local frontend dashboard shell smoke test

Manual local frontend validation was performed by starting the dashboard shell
from the `frontend/` directory:

```bash
npm install
npm run build
npm run dev
```

`next build` completed successfully, TypeScript passed, and the static `/`
route was generated.

The browser smoke-test opened `http://127.0.0.1:3000` and confirmed:

- FlexSignal AI title visible.
- Read-only decision support -- no automatic control badge visible.
- DK1/DK2 selector visible.
- Spot prices card visible.
- Power balance card visible.
- Manual Load spot prices button visible.
- Manual Load power balance button visible.
- Idle, loading, error, row count, and compact result table states available.
- Backend API base URL helper visible as `http://127.0.0.1:8000`.
- Browser copy states that the frontend does not call Energi Data Service
  directly.
- No error screen.

The frontend makes no automatic page-load API requests, direct Energi Data
Service calls, polling requests, database writes, auth calls, Azure resource
changes, forecasting/model calls, or control, dispatch, activation, or
operational functionality. Backend API requests are made only when a user
presses one of the manual load buttons.

Known local development note: opening the Next.js dev server through
`127.0.0.1` showed a development-only cross-origin warning for dev resources.
Use `http://localhost:3000` during local development unless `allowedDevOrigins`
is configured later. This warning did not block the page render.

### Local frontend-to-backend read-only smoke test

Manual local frontend-to-backend validation was performed with the backend
started manually from the `backend/` directory:

```bash
DATABASE_URL="postgresql://localhost/flexsignal_ai" python -m uvicorn app.main:app --reload
```

The frontend was started manually from the repository root:

```bash
cd frontend
npm install
npm run dev
```

The browser opened `http://localhost:3000`. The manual read-only UI actions
were:

- Selected DK1.
- Clicked Load spot prices.
- Clicked Load power balance.

Observed local result:

- Spot prices displayed 3 rows for DK1.
- Power balance displayed 3 rows for DK1.
- No Failed to fetch error appeared.
- Backend logs showed HTTP 200 for both read-only API calls.
- The local-development CORS fix worked.

Important boundary notes:

- The frontend only called the backend API helper.
- No direct Energi Data Service calls were made from the frontend.
- No polling was added or observed.
- No database writes were added or performed.
- No live EDS polling was added or performed.
- No startup migrations were added or run.
- No Azure resources were added or used.
- No production database was used.
- No forecasting/model logic was added.
- No control, dispatch, activation, or operational functionality was added.

## Compliance Principles

- Read-only decision support in `v0.1`.
- Human review before any operational action.
- No autonomous control.
- No control signals to energy infrastructure.
- Auditability for forecasts, recommendations, explanations, and user actions.
- Least-privilege access to systems and data.
- LLMs are limited to explanation and reporting, not core forecasting or final decision-making.
