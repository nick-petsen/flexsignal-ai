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

## Frontend Local Development

The frontend is a minimal Next.js dashboard shell for `v0.1` read-only decision
support. It does not fetch data, poll live endpoints, forecast, dispatch,
activate, or control energy assets.

From the `frontend/` directory:

```bash
npm install
npm run build
npm run dev
```

The frontend keeps a backend API base URL helper for future read-only API
integration. It defaults to `http://127.0.0.1:8000` and can be overridden with
`NEXT_PUBLIC_API_BASE_URL`.

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
- Placeholder, loading-ready, and error-ready sections visible.
- Backend API base URL helper visible as `http://127.0.0.1:8000`.
- No error screen.

The frontend shell made no backend API requests, direct Energi Data Service
calls, polling requests, database writes, auth calls, Azure resource changes,
forecasting/model calls, or control, dispatch, activation, or operational
functionality.

Known local development note: opening the Next.js dev server through
`127.0.0.1` showed a development-only cross-origin warning for dev resources.
Use `http://localhost:3000` during local development unless `allowedDevOrigins`
is configured later. This warning did not block the page render.

## Compliance Principles

- Read-only decision support in `v0.1`.
- Human review before any operational action.
- No autonomous control.
- No control signals to energy infrastructure.
- Auditability for forecasts, recommendations, explanations, and user actions.
- Least-privilege access to systems and data.
- LLMs are limited to explanation and reporting, not core forecasting or final decision-making.
