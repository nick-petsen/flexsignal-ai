"use client";

import { useState } from "react";
import {
  backendApiBaseUrl,
  fetchCurrentRisk,
  fetchEnergyFreshness,
  fetchEnergyFreshnessRead,
  fetchForecastPreview,
  fetchPowerBalance,
  fetchSpotPrices,
  type CurrentRiskResponse,
  type EnergyApiResponse,
  type EnergyFreshnessQueryPlan,
  type EnergyFreshnessReadResult,
  type EnergyFreshnessResponse,
  type ForecastPreviewResponse,
  type ForecastWindowSummary,
  type PowerBalanceRow,
  type PriceArea,
  type SafetyBoundary,
  type SpotPriceRow
} from "../lib/api";

type EnergyRequestState<Row> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: EnergyApiResponse<Row> }
  | { status: "error"; message: string };

type RiskRequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: CurrentRiskResponse }
  | { status: "error"; message: string };

type ForecastRequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: ForecastPreviewResponse }
  | { status: "error"; message: string };

type FreshnessRequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: EnergyFreshnessResponse }
  | { status: "error"; message: string };

type Column<Row> = {
  key: keyof Row;
  label: string;
};

type EnergyCardProps<Row> = {
  title: string;
  description: string;
  endpointName: string;
  buttonLabel: string;
  state: EnergyRequestState<Row>;
  columns: Column<Row>[];
  onLoad: () => void;
};

const priceAreas: PriceArea[] = ["DK1", "DK2"];

const spotPriceColumns: Column<SpotPriceRow>[] = [
  { key: "timestamp_utc", label: "Timestamp UTC" },
  { key: "price_eur_per_mwh", label: "EUR/MWh" },
  { key: "price_dkk_per_mwh", label: "DKK/MWh" },
  { key: "source", label: "Source" }
];

const powerBalanceColumns: Column<PowerBalanceRow>[] = [
  { key: "timestamp_utc", label: "Timestamp UTC" },
  { key: "production_mw", label: "Production MW" },
  { key: "consumption_mw", label: "Consumption MW" },
  { key: "wind_onshore_mw", label: "Wind onshore MW" },
  { key: "wind_offshore_mw", label: "Wind offshore MW" },
  { key: "solar_mw", label: "Solar MW" }
];

function EnergyCard<Row extends { source_record_id: string }>({
  title,
  description,
  endpointName,
  buttonLabel,
  state,
  columns,
  onLoad
}: EnergyCardProps<Row>) {
  const isLoading = state.status === "loading";

  return (
    <section className="card" aria-labelledby={`${endpointName}-title`}>
      <div className="card__header">
        <div>
          <h2 id={`${endpointName}-title`}>{title}</h2>
          <p className="card__description">{description}</p>
        </div>
        <span className="status">Read-only</span>
      </div>
      <button
        className="load-button"
        type="button"
        onClick={onLoad}
        disabled={isLoading}
      >
        {isLoading ? "Loading..." : buttonLabel}
      </button>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            No request has been made. Use the manual button to load backend API
            data.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">Loading read-only backend data...</p>
        )}
        {state.status === "error" && (
          <p className="error">Backend unavailable: {state.message}</p>
        )}
        {state.status === "success" && (
          <ResultTable data={state.data} columns={columns} />
        )}
      </div>
    </section>
  );
}

function ResultTable<Row extends { source_record_id: string }>({
  data,
  columns
}: {
  data: EnergyApiResponse<Row>;
  columns: Column<Row>[];
}) {
  return (
    <div>
      <p className="row-count">
        <strong>{data.row_count}</strong> rows returned from{" "}
        <code>{data.table}</code> for <strong>{data.price_area}</strong>
      </p>
      {data.rows.length === 0 ? (
        <p className="muted">No rows returned by the backend endpoint.</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={String(column.key)} scope="col">
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr key={row.source_record_id}>
                  {columns.map((column) => (
                    <td key={String(column.key)}>
                      {formatValue(row[column.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function formatValue(value: unknown): string {
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }

  if (value === null || value === undefined || value === "") {
    return "n/a";
  }

  return String(value);
}

function CurrentRiskCard({
  state,
  onLoad
}: {
  state: RiskRequestState;
  onLoad: () => void;
}) {
  const isLoading = state.status === "loading";

  return (
    <section className="card" aria-labelledby="current-risk-title">
      <div className="card__header">
        <div>
          <h2 id="current-risk-title">Current surplus risk</h2>
          <p className="card__description">
            Manual read-only request to the backend current risk endpoint.
          </p>
        </div>
        <span className="status">Read-only</span>
      </div>
      <button
        className="load-button"
        type="button"
        onClick={onLoad}
        disabled={isLoading}
      >
        {isLoading ? "Loading..." : "Load current risk"}
      </button>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            No request has been made. Use the manual button to load backend API
            risk data.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">Loading read-only backend risk data...</p>
        )}
        {state.status === "error" && (
          <p className="error">Backend unavailable: {state.message}</p>
        )}
        {state.status === "success" && <RiskResult data={state.data} />}
      </div>
    </section>
  );
}

function RiskResult({ data }: { data: CurrentRiskResponse }) {
  return (
    <dl className="risk-list">
      <div>
        <dt>risk_level</dt>
        <dd>{formatValue(data.risk_level)}</dd>
      </div>
      <div>
        <dt>risk_score</dt>
        <dd>{formatValue(data.risk_score)}</dd>
      </div>
      <div>
        <dt>confidence_score</dt>
        <dd>{formatValue(data.confidence_score)}</dd>
      </div>
      <div>
        <dt>reason_codes</dt>
        <dd>
          {data.reason_codes.length > 0
            ? data.reason_codes.join(", ")
            : "n/a"}
        </dd>
      </div>
      <div>
        <dt>explanation</dt>
        <dd>{formatValue(data.explanation)}</dd>
      </div>
      <div>
        <dt>recommended_human_action</dt>
        <dd>{formatValue(data.recommended_human_action)}</dd>
      </div>
      <div>
        <dt>model_version</dt>
        <dd>{formatValue(data.model_version)}</dd>
      </div>
      <div>
        <dt>decision_support_only</dt>
        <dd>{formatValue(data.decision_support_only)}</dd>
      </div>
      <div>
        <dt>metadata.source_tables_used</dt>
        <dd>
          {data.metadata.source_tables_used.length > 0
            ? data.metadata.source_tables_used.join(", ")
            : "n/a"}
        </dd>
      </div>
      <div>
        <dt>metadata.spot_price_row_found</dt>
        <dd>{formatValue(data.metadata.spot_price_row_found)}</dd>
      </div>
      <div>
        <dt>metadata.power_balance_row_found</dt>
        <dd>{formatValue(data.metadata.power_balance_row_found)}</dd>
      </div>
    </dl>
  );
}

function ForecastPreviewCard({
  state,
  onLoad
}: {
  state: ForecastRequestState;
  onLoad: () => void;
}) {
  const isLoading = state.status === "loading";

  return (
    <section className="card" aria-labelledby="forecast-preview-title">
      <div className="card__header">
        <div>
          <h2 id="forecast-preview-title">Forecast preview</h2>
          <p className="card__description">
            Manual request to preview deterministic forecast windows from
            synthetic/caller-provided rows only.
          </p>
        </div>
        <span className="status">Read-only</span>
      </div>
      <button
        className="load-button"
        type="button"
        onClick={onLoad}
        disabled={isLoading}
      >
        {isLoading ? "Loading..." : "Load forecast preview"}
      </button>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            No request has been made. Use the manual button to call{" "}
            <code>POST /api/forecast/preview</code>.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">Loading read-only forecast preview...</p>
        )}
        {state.status === "error" && (
          <p className="error">Backend unavailable: {state.message}</p>
        )}
        {state.status === "success" && (
          <ForecastPreviewResult data={state.data} />
        )}
      </div>
    </section>
  );
}

function EnergyFreshnessCard({
  state,
  onLoadDryRun,
  onLoadRead
}: {
  state: FreshnessRequestState;
  onLoadDryRun: () => void;
  onLoadRead: () => void;
}) {
  const isLoading = state.status === "loading";
  const statusLabel =
    state.status === "success" && !state.data.dry_run
      ? "SELECT-only"
      : "Read-only";

  return (
    <section className="card" aria-labelledby="energy-freshness-title">
      <div className="card__header">
        <div>
          <h2 id="energy-freshness-title">Energy data freshness</h2>
          <p className="card__description">
            DB-backed freshness read for stored local/configured database data,
            with a dry-run query plan preview available.
          </p>
        </div>
        <span className="status">{statusLabel}</span>
      </div>
      <div className="button-row">
        <button
          className="load-button"
          type="button"
          onClick={onLoadRead}
          disabled={isLoading}
        >
          {isLoading ? "Loading..." : "Load DB-backed read"}
        </button>
        <button
          className="load-button load-button--secondary"
          type="button"
          onClick={onLoadDryRun}
          disabled={isLoading}
        >
          {isLoading ? "Loading..." : "Load dry-run plan"}
        </button>
      </div>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            No request has been made. Use the manual button to call{" "}
            <code>GET /api/energy/freshness/read</code> for a SELECT-only
            DB-backed freshness read, or preview the dry-run query plan.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">
            Loading read-only energy freshness data...
          </p>
        )}
        {state.status === "error" && <p className="error">{state.message}</p>}
        {state.status === "success" && (
          <EnergyFreshnessResult data={state.data} />
        )}
      </div>
    </section>
  );
}

function EnergyFreshnessResult({ data }: { data: EnergyFreshnessResponse }) {
  const spotPricePlan =
    data.spot_price_freshness_plan ??
    data.freshness_plans?.queries?.spot_price;
  const powerBalancePlan =
    data.power_balance_freshness_plan ??
    data.freshness_plans?.queries?.power_balance;
  const spotPriceFreshness =
    data.spot_price_freshness ??
    data.freshness_result?.spot_price_freshness;
  const powerBalanceFreshness =
    data.power_balance_freshness ??
    data.freshness_result?.power_balance_freshness;

  return (
    <div>
      <p className="preview-note">
        {data.dry_run
          ? "Dry-run query plan preview only. No database query executed. No database write performed. Does not fetch new EDS/DMI data."
          : "DB-backed freshness read. SELECT-only read. No database write performed. Shows freshness of stored local/configured database data. Does not fetch new EDS/DMI data or imply ingestion has run."}
      </p>
      <dl className="risk-list">
        <div>
          <dt>price_area</dt>
          <dd>{formatValue(data.price_area)}</dd>
        </div>
        <div>
          <dt>dry_run</dt>
          <dd>{formatValue(data.dry_run)}</dd>
        </div>
        <div>
          <dt>database_query_executed</dt>
          <dd>{formatValue(data.database_query_executed)}</dd>
        </div>
        <div>
          <dt>database_write_performed</dt>
          <dd>{formatValue(data.database_write_performed)}</dd>
        </div>
        <div>
          <dt>requires_database_url</dt>
          <dd>{formatValue(data.requires_database_url)}</dd>
        </div>
      </dl>
      {data.dry_run ? (
        <div className="plan-grid">
          <FreshnessPlanSummary label="spot_price" plan={spotPricePlan} />
          <FreshnessPlanSummary
            label="power_balance"
            plan={powerBalancePlan}
          />
        </div>
      ) : (
        <div className="plan-grid">
          <FreshnessReadSummary
            label="spot_price_freshness"
            freshness={spotPriceFreshness}
          />
          <FreshnessReadSummary
            label="power_balance_freshness"
            freshness={powerBalanceFreshness}
          />
        </div>
      )}
      <WarningList warnings={data.warnings} />
      <SafetyBoundarySummary safetyBoundary={data.safety_boundary} />
    </div>
  );
}

function FreshnessPlanSummary({
  label,
  plan
}: {
  label: string;
  plan?: EnergyFreshnessQueryPlan;
}) {
  return (
    <article className="plan-summary">
      <h3>{label}</h3>
      <dl className="risk-list">
        <div>
          <dt>plan_presence</dt>
          <dd>{plan ? "present" : "missing"}</dd>
        </div>
        <div>
          <dt>status</dt>
          <dd>
            {plan?.operation === "select"
              ? "prepared read-only SELECT plan"
              : "not available"}
          </dd>
        </div>
        <div>
          <dt>operation</dt>
          <dd>{formatValue(plan?.operation)}</dd>
        </div>
        <div>
          <dt>table</dt>
          <dd>{formatValue(plan?.table)}</dd>
        </div>
      </dl>
    </article>
  );
}

function FreshnessReadSummary({
  label,
  freshness
}: {
  label: string;
  freshness?: EnergyFreshnessReadResult;
}) {
  return (
    <article className="plan-summary">
      <h3>{label}</h3>
      <dl className="risk-list">
        <div>
          <dt>latest_timestamp</dt>
          <dd>{formatValue(freshness?.latest_timestamp)}</dd>
        </div>
        <div>
          <dt>row_count</dt>
          <dd>{formatValue(freshness?.row_count)}</dd>
        </div>
        <div>
          <dt>database_query_executed</dt>
          <dd>{formatValue(freshness?.database_query_executed)}</dd>
        </div>
        <div>
          <dt>database_write_performed</dt>
          <dd>{formatValue(freshness?.database_write_performed)}</dd>
        </div>
      </dl>
    </article>
  );
}

function WarningList({ warnings }: { warnings?: string[] }) {
  if (!warnings || warnings.length === 0) {
    return <p className="muted freshness-detail">warnings: n/a</p>;
  }

  return (
    <div className="freshness-detail">
      <h3>Warnings</h3>
      <ul className="plain-list">
        {warnings.map((warning) => (
          <li key={warning}>{warning}</li>
        ))}
      </ul>
    </div>
  );
}

function SafetyBoundarySummary({
  safetyBoundary
}: {
  safetyBoundary?: SafetyBoundary;
}) {
  return (
    <div className="freshness-detail">
      <h3>Safety boundary</h3>
      <dl className="risk-list">
        <div>
          <dt>read_only_decision_support</dt>
          <dd>{formatValue(safetyBoundary?.read_only_decision_support)}</dd>
        </div>
        <div>
          <dt>no_automatic_control</dt>
          <dd>{formatValue(safetyBoundary?.no_automatic_control)}</dd>
        </div>
        <div>
          <dt>no_dispatch</dt>
          <dd>{formatValue(safetyBoundary?.no_dispatch)}</dd>
        </div>
        <div>
          <dt>no_activation</dt>
          <dd>{formatValue(safetyBoundary?.no_activation)}</dd>
        </div>
        <div>
          <dt>no_operational_energy_system_integration</dt>
          <dd>
            {formatValue(
              safetyBoundary?.no_operational_energy_system_integration
            )}
          </dd>
        </div>
        <div>
          <dt>human_review_required</dt>
          <dd>{formatValue(safetyBoundary?.human_review_required)}</dd>
        </div>
      </dl>
    </div>
  );
}

function ForecastPreviewResult({ data }: { data: ForecastPreviewResponse }) {
  return (
    <div>
      <p className="preview-note">
        Synthetic/caller-provided preview data only. This is not production
        forecast validation.
      </p>
      <dl className="risk-list">
        <div>
          <dt>model_version</dt>
          <dd>{formatValue(data.model_version)}</dd>
        </div>
        <div>
          <dt>decision_support_only</dt>
          <dd>{formatValue(data.decision_support_only)}</dd>
        </div>
        <div>
          <dt>generated_at_utc</dt>
          <dd>{formatValue(data.generated_at_utc)}</dd>
        </div>
      </dl>
      <div className="forecast-windows">
        {data.windows.map((window) => (
          <ForecastWindow key={window.window_label} window={window} />
        ))}
      </div>
    </div>
  );
}

function ForecastWindow({ window }: { window: ForecastWindowSummary }) {
  return (
    <article className="forecast-window">
      <h3>{window.window_label}</h3>
      <dl className="risk-list">
        <div>
          <dt>risk_level</dt>
          <dd>{formatValue(window.risk_level)}</dd>
        </div>
        <div>
          <dt>row_count</dt>
          <dd>{formatValue(window.row_count)}</dd>
        </div>
        <div>
          <dt>max_risk_score</dt>
          <dd>{formatValue(window.max_risk_score)}</dd>
        </div>
        <div>
          <dt>average_risk_score</dt>
          <dd>{formatValue(window.average_risk_score)}</dd>
        </div>
        <div>
          <dt>top_reason_codes</dt>
          <dd>{formatReasonCodes(window.top_reason_codes)}</dd>
        </div>
        <div>
          <dt>recommended_human_action</dt>
          <dd>{formatValue(window.recommended_human_action)}</dd>
        </div>
      </dl>
    </article>
  );
}

function formatReasonCodes(
  reasonCodes: ForecastWindowSummary["top_reason_codes"]
): string {
  if (reasonCodes.length === 0) {
    return "n/a";
  }

  return reasonCodes
    .map((reasonCode) => `${reasonCode.reason_code} (${reasonCode.count})`)
    .join(", ");
}

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "Request failed";
}

export default function DashboardPage() {
  const [selectedArea, setSelectedArea] = useState<PriceArea>("DK1");
  const [spotPricesState, setSpotPricesState] = useState<
    EnergyRequestState<SpotPriceRow>
  >({ status: "idle" });
  const [powerBalanceState, setPowerBalanceState] = useState<
    EnergyRequestState<PowerBalanceRow>
  >({ status: "idle" });
  const [currentRiskState, setCurrentRiskState] = useState<RiskRequestState>({
    status: "idle"
  });
  const [forecastPreviewState, setForecastPreviewState] =
    useState<ForecastRequestState>({
      status: "idle"
    });
  const [freshnessState, setFreshnessState] = useState<FreshnessRequestState>({
    status: "idle"
  });

  function handleAreaChange(nextArea: PriceArea) {
    setSelectedArea(nextArea);
    setSpotPricesState({ status: "idle" });
    setPowerBalanceState({ status: "idle" });
    setCurrentRiskState({ status: "idle" });
    setForecastPreviewState({ status: "idle" });
    setFreshnessState({ status: "idle" });
  }

  async function handleLoadSpotPrices() {
    setSpotPricesState({ status: "loading" });
    try {
      const data = await fetchSpotPrices(selectedArea);
      setSpotPricesState({ status: "success", data });
    } catch (error) {
      setSpotPricesState({ status: "error", message: errorMessage(error) });
    }
  }

  async function handleLoadPowerBalance() {
    setPowerBalanceState({ status: "loading" });
    try {
      const data = await fetchPowerBalance(selectedArea);
      setPowerBalanceState({ status: "success", data });
    } catch (error) {
      setPowerBalanceState({ status: "error", message: errorMessage(error) });
    }
  }

  async function handleLoadCurrentRisk() {
    setCurrentRiskState({ status: "loading" });
    try {
      const data = await fetchCurrentRisk(selectedArea);
      setCurrentRiskState({ status: "success", data });
    } catch (error) {
      setCurrentRiskState({ status: "error", message: errorMessage(error) });
    }
  }

  async function handleLoadForecastPreview() {
    setForecastPreviewState({ status: "loading" });
    try {
      const data = await fetchForecastPreview(selectedArea);
      setForecastPreviewState({ status: "success", data });
    } catch (error) {
      setForecastPreviewState({
        status: "error",
        message: errorMessage(error)
      });
    }
  }

  async function handleLoadFreshnessDryRun() {
    setFreshnessState({ status: "loading" });
    try {
      const data = await fetchEnergyFreshness(selectedArea);
      setFreshnessState({ status: "success", data });
    } catch (error) {
      setFreshnessState({
        status: "error",
        message: errorMessage(error)
      });
    }
  }

  async function handleLoadFreshnessRead() {
    setFreshnessState({ status: "loading" });
    try {
      const data = await fetchEnergyFreshnessRead(selectedArea);
      setFreshnessState({ status: "success", data });
    } catch (error) {
      setFreshnessState({
        status: "error",
        message: errorMessage(error)
      });
    }
  }

  return (
    <main className="dashboard">
      <div className="dashboard__inner">
        <header className="dashboard__header">
          <div>
            <p className="eyebrow">FlexSignal AI</p>
            <h1>FlexSignal AI</h1>
            <div className="scope-badge">
              Read-only decision support — no automatic control
            </div>
            <p className="lead">
              Minimal dashboard for Danish electricity decision support. Data
              loads only when requested from the backend API helper, and the
              frontend does not dispatch, activate, poll, control energy
              assets, run forecasting logic, or call Energi Data Service
              directly.
            </p>
          </div>
          <div className="selector">
            <label htmlFor="price-area">Price area</label>
            <select
              id="price-area"
              value={selectedArea}
              onChange={(event) =>
                handleAreaChange(event.target.value as PriceArea)
              }
            >
              {priceAreas.map((area) => (
                <option key={area} value={area}>
                  {area}
                </option>
              ))}
            </select>
          </div>
        </header>

        <div className="summary">
          <EnergyCard
            title="Spot prices"
            description="Manual read-only request to backend spot price rows."
            endpointName="spot-prices"
            buttonLabel="Load spot prices"
            state={spotPricesState}
            columns={spotPriceColumns}
            onLoad={handleLoadSpotPrices}
          />
          <EnergyCard
            title="Power balance"
            description="Manual read-only request to backend power balance rows."
            endpointName="power-balance"
            buttonLabel="Load power balance"
            state={powerBalanceState}
            columns={powerBalanceColumns}
            onLoad={handleLoadPowerBalance}
          />
          <CurrentRiskCard
            state={currentRiskState}
            onLoad={handleLoadCurrentRisk}
          />
          <ForecastPreviewCard
            state={forecastPreviewState}
            onLoad={handleLoadForecastPreview}
          />
          <EnergyFreshnessCard
            state={freshnessState}
            onLoadDryRun={handleLoadFreshnessDryRun}
            onLoadRead={handleLoadFreshnessRead}
          />
        </div>

        <p className="api-note">
          Frontend requests use only the backend API base URL helper:{" "}
          <code>{backendApiBaseUrl}</code>. The browser does not call Energi
          Data Service or external data APIs directly, and nothing auto-loads
          or polls.
        </p>
      </div>
    </main>
  );
}
