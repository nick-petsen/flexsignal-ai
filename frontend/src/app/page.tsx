"use client";

import { useState } from "react";
import {
  backendApiBaseUrl,
  fetchPowerBalance,
  fetchSpotPrices,
  type EnergyApiResponse,
  type PowerBalanceRow,
  type PriceArea,
  type SpotPriceRow
} from "../lib/api";

type RequestState<Row> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: EnergyApiResponse<Row> }
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
  state: RequestState<Row>;
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
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }

  return String(value);
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
    RequestState<SpotPriceRow>
  >({ status: "idle" });
  const [powerBalanceState, setPowerBalanceState] = useState<
    RequestState<PowerBalanceRow>
  >({ status: "idle" });

  function handleAreaChange(nextArea: PriceArea) {
    setSelectedArea(nextArea);
    setSpotPricesState({ status: "idle" });
    setPowerBalanceState({ status: "idle" });
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
              frontend does not dispatch, activate, forecast, poll, control
              energy assets, or call Energi Data Service directly.
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
        </div>

        <p className="api-note">
          Frontend requests use only the backend API base URL helper:{" "}
          <code>{backendApiBaseUrl}</code>. The browser does not call Energi
          Data Service directly.
        </p>
      </div>
    </main>
  );
}
