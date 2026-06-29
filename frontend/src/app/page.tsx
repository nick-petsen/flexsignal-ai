"use client";

import { useState, type ReactNode } from "react";
import {
  backendApiBaseUrl,
  fetchAuditedReportPdfExport,
  fetchCurrentRisk,
  fetchEnergyFreshness,
  fetchEnergyFreshnessRead,
  fetchForecastPreview,
  fetchPowerBalance,
  fetchReportPdfExport,
  fetchReportMarkdownPreview,
  fetchReportPdfPreview,
  fetchReportSummaryPreview,
  fetchSpotPrices,
  persistAuditPdfExportEvent,
  type AuditPdfExportPersistResponse,
  type AuditedReportPdfExportResponse,
  type CurrentRiskResponse,
  type EnergyApiResponse,
  type EnergyFreshnessQueryPlan,
  type EnergyFreshnessReadResult,
  type EnergyFreshnessResponse,
  type ForecastPreviewResponse,
  type ForecastWindowSummary,
  type PowerBalanceRow,
  type PriceArea,
  type ReportMarkdownPreviewResponse,
  type ReportPdfExportResponse,
  type ReportPdfPreviewResponse,
  type ReportSummaryPreviewResponse,
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

type ReportRequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: ReportSummaryPreviewResponse }
  | { status: "error"; message: string };

type ReportMarkdownRequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: ReportMarkdownPreviewResponse }
  | { status: "error"; message: string };

type ReportPdfRequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: ReportPdfPreviewResponse }
  | { status: "error"; message: string };

type ReportPdfExportRequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: ReportPdfExportResponse; filename: string }
  | { status: "error"; message: string };

type AuditedReportPdfExportRequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: AuditedReportPdfExportResponse; filename: string }
  | { status: "error"; message: string };

type AuditPdfExportPersistRequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: AuditPdfExportPersistResponse }
  | { status: "error"; message: string };

type Column<Row> = {
  key: keyof Row;
  label: string;
};

type DashboardSection =
  | "dashboard"
  | "reports"
  | "audit"
  | "forecast"
  | "data"
  | "weather";

type EnergyCardProps<Row> = {
  title: string;
  description: string;
  endpointName: string;
  buttonLabel: string;
  state: EnergyRequestState<Row>;
  columns: Column<Row>[];
  onLoad: () => void;
  renderAfterTable?: (data: EnergyApiResponse<Row>) => ReactNode;
};

const priceAreas: PriceArea[] = ["DK1", "DK2"];

const navigationItems: {
  id: DashboardSection;
  label: string;
  description: string;
}[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    description: "Overview"
  },
  {
    id: "reports",
    label: "Reports",
    description: "Preview and export"
  },
  {
    id: "audit",
    label: "Audit",
    description: "Manual evidence"
  },
  {
    id: "forecast",
    label: "Forecast",
    description: "Risk windows"
  },
  {
    id: "data",
    label: "Data",
    description: "Stored energy data"
  },
  {
    id: "weather",
    label: "Meteo / Weather",
    description: "Future module"
  }
];

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
  onLoad,
  renderAfterTable
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
          <>
            <ResultTable data={state.data} columns={columns} />
            {renderAfterTable?.(state.data)}
          </>
        )}
      </div>
    </section>
  );
}

function SpotPriceTrendChart({
  data
}: {
  data: EnergyApiResponse<SpotPriceRow>;
}) {
  if (data.rows.length === 0) {
    return null;
  }

  const points = data.rows
    .map((row) => {
      const timestampMs = Date.parse(row.timestamp_utc);
      const price = parseNumber(row.price_eur_per_mwh);

      if (!Number.isFinite(timestampMs) || price === null) {
        return null;
      }

      return {
        timestampUtc: row.timestamp_utc,
        timestampMs,
        price,
        sourceRecordId: row.source_record_id
      };
    })
    .filter((point): point is NonNullable<typeof point> => point !== null)
    .sort((left, right) => left.timestampMs - right.timestampMs);

  const latestPoint = points.at(-1);
  const latestLabel = latestPoint
    ? `${formatNumber(latestPoint.price)} EUR/MWh`
    : "n/a";

  if (points.length === 0) {
    return (
      <section className="spot-chart" aria-labelledby="spot-chart-title">
        <div className="spot-chart__header">
          <div>
            <h3 id="spot-chart-title">Spot price trend</h3>
            <p>
              Manual read-only spot price rows. Trend from loaded backend rows.
            </p>
          </div>
          <span>Latest: {latestLabel}</span>
        </div>
        <p className="muted">
          Manual read-only spot price rows were returned, but none contained a
          valid timestamp and EUR/MWh value for charting.
        </p>
      </section>
    );
  }

  const width = 640;
  const height = 180;
  const padding = {
    top: 16,
    right: 20,
    bottom: 28,
    left: 48
  };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const prices = points.map((point) => point.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice;
  const yMin = priceRange === 0 ? minPrice - 1 : minPrice;
  const yMax = priceRange === 0 ? maxPrice + 1 : maxPrice;
  const yRange = yMax - yMin || 1;
  const plottedPoints = points.map((point, index) => {
    const x =
      points.length === 1
        ? padding.left + chartWidth / 2
        : padding.left + (index / (points.length - 1)) * chartWidth;
    const y =
      padding.top + ((yMax - point.price) / yRange) * chartHeight;

    return { ...point, x, y };
  });
  const polylinePoints = plottedPoints
    .map((point) => `${point.x},${point.y}`)
    .join(" ");
  const firstTimestamp = formatShortTimestamp(points[0].timestampUtc);
  const lastTimestamp = formatShortTimestamp(
    points[points.length - 1].timestampUtc
  );

  return (
    <section className="spot-chart" aria-labelledby="spot-chart-title">
      <div className="spot-chart__header">
        <div>
          <h3 id="spot-chart-title">Spot price trend</h3>
          <p>
            Manual read-only spot price rows. Trend from loaded backend rows.
          </p>
        </div>
        <span>Latest: {latestLabel}</span>
      </div>
      <svg
        className="spot-chart__svg"
        role="img"
        aria-label={`Manual read-only spot price trend for ${data.price_area} in EUR per MWh`}
        viewBox={`0 0 ${width} ${height}`}
      >
        <line
          className="spot-chart__axis"
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={padding.top + chartHeight}
        />
        <line
          className="spot-chart__axis"
          x1={padding.left}
          y1={padding.top + chartHeight}
          x2={padding.left + chartWidth}
          y2={padding.top + chartHeight}
        />
        <text className="spot-chart__label" x="0" y="18">
          EUR/MWh
        </text>
        <text
          className="spot-chart__tick"
          x={padding.left - 8}
          y={padding.top + 5}
          textAnchor="end"
        >
          {formatNumber(yMax)}
        </text>
        <text
          className="spot-chart__tick"
          x={padding.left - 8}
          y={padding.top + chartHeight}
          textAnchor="end"
        >
          {formatNumber(yMin)}
        </text>
        <text
          className="spot-chart__tick"
          x={padding.left}
          y={height - 8}
          textAnchor="start"
        >
          {firstTimestamp}
        </text>
        <text
          className="spot-chart__tick"
          x={padding.left + chartWidth}
          y={height - 8}
          textAnchor="end"
        >
          {lastTimestamp}
        </text>
        {points.length > 1 && (
          <polyline className="spot-chart__line" points={polylinePoints} />
        )}
        {plottedPoints.map((point, index) => (
          <circle
            className="spot-chart__point"
            key={`${point.sourceRecordId}-${index}`}
            cx={point.x}
            cy={point.y}
            r={points.length === 1 ? 4 : 3}
          />
        ))}
      </svg>
    </section>
  );
}

function PowerBalanceTrendChart({
  data
}: {
  data: EnergyApiResponse<PowerBalanceRow>;
}) {
  if (data.rows.length === 0) {
    return null;
  }

  const points = data.rows
    .map((row) => {
      const timestampMs = Date.parse(row.timestamp_utc);
      const productionMw = parseNumber(row.production_mw);

      if (!Number.isFinite(timestampMs) || productionMw === null) {
        return null;
      }

      return {
        timestampUtc: row.timestamp_utc,
        timestampMs,
        productionMw,
        sourceRecordId: row.source_record_id
      };
    })
    .filter((point): point is NonNullable<typeof point> => point !== null)
    .sort((left, right) => left.timestampMs - right.timestampMs);

  const latestPoint = points.at(-1);
  const latestLabel = latestPoint
    ? `${formatNumber(latestPoint.productionMw)} MW`
    : "n/a";

  if (points.length === 0) {
    return (
      <section className="spot-chart" aria-labelledby="power-chart-title">
        <div className="spot-chart__header">
          <div>
            <h3 id="power-chart-title">Power balance trend</h3>
            <p>
              Manual read-only power balance rows. Trend from loaded backend
              rows.
            </p>
          </div>
          <span>Latest production: {latestLabel}</span>
        </div>
        <p className="muted">
          Manual read-only power balance rows were returned, but none contained
          a valid timestamp and production MW value for charting.
        </p>
      </section>
    );
  }

  const width = 640;
  const height = 180;
  const padding = {
    top: 16,
    right: 20,
    bottom: 28,
    left: 48
  };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const productionValues = points.map((point) => point.productionMw);
  const minProduction = Math.min(...productionValues);
  const maxProduction = Math.max(...productionValues);
  const productionRange = maxProduction - minProduction;
  const yMin = productionRange === 0 ? minProduction - 1 : minProduction;
  const yMax = productionRange === 0 ? maxProduction + 1 : maxProduction;
  const yRange = yMax - yMin || 1;
  const plottedPoints = points.map((point, index) => {
    const x =
      points.length === 1
        ? padding.left + chartWidth / 2
        : padding.left + (index / (points.length - 1)) * chartWidth;
    const y =
      padding.top + ((yMax - point.productionMw) / yRange) * chartHeight;

    return { ...point, x, y };
  });
  const polylinePoints = plottedPoints
    .map((point) => `${point.x},${point.y}`)
    .join(" ");
  const firstTimestamp = formatShortTimestamp(points[0].timestampUtc);
  const lastTimestamp = formatShortTimestamp(
    points[points.length - 1].timestampUtc
  );

  return (
    <section className="spot-chart" aria-labelledby="power-chart-title">
      <div className="spot-chart__header">
        <div>
          <h3 id="power-chart-title">Power balance trend</h3>
          <p>
            Manual read-only power balance rows. Trend from loaded backend
            rows.
          </p>
        </div>
        <span>Latest production: {latestLabel}</span>
      </div>
      <svg
        className="spot-chart__svg"
        role="img"
        aria-label={`Manual read-only power balance trend for ${data.price_area} in production MW`}
        viewBox={`0 0 ${width} ${height}`}
      >
        <line
          className="spot-chart__axis"
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={padding.top + chartHeight}
        />
        <line
          className="spot-chart__axis"
          x1={padding.left}
          y1={padding.top + chartHeight}
          x2={padding.left + chartWidth}
          y2={padding.top + chartHeight}
        />
        <text className="spot-chart__label" x="0" y="18">
          MW
        </text>
        <text
          className="spot-chart__tick"
          x={padding.left - 8}
          y={padding.top + 5}
          textAnchor="end"
        >
          {formatNumber(yMax)}
        </text>
        <text
          className="spot-chart__tick"
          x={padding.left - 8}
          y={padding.top + chartHeight}
          textAnchor="end"
        >
          {formatNumber(yMin)}
        </text>
        <text
          className="spot-chart__tick"
          x={padding.left}
          y={height - 8}
          textAnchor="start"
        >
          {firstTimestamp}
        </text>
        <text
          className="spot-chart__tick"
          x={padding.left + chartWidth}
          y={height - 8}
          textAnchor="end"
        >
          {lastTimestamp}
        </text>
        {points.length > 1 && (
          <polyline
            className="spot-chart__line spot-chart__line--power"
            points={polylinePoints}
          />
        )}
        {plottedPoints.map((point, index) => (
          <circle
            className="spot-chart__point spot-chart__point--power"
            key={`${point.sourceRecordId}-${index}`}
            cx={point.x}
            cy={point.y}
            r={points.length === 1 ? 4 : 3}
          />
        ))}
      </svg>
    </section>
  );
}

function parseNumber(value: string | number | null): number | null {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }

  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en", {
    maximumFractionDigits: 2
  }).format(value);
}

function formatShortTimestamp(timestampUtc: string): string {
  const timestampMs = Date.parse(timestampUtc);

  if (!Number.isFinite(timestampMs)) {
    return "n/a";
  }

  return new Date(timestampMs).toISOString().slice(5, 16).replace("T", " ");
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
  const reasonCodes = Array.isArray(data.reason_codes)
    ? data.reason_codes
    : [];
  const sourceTablesUsed = Array.isArray(data.metadata?.source_tables_used)
    ? data.metadata.source_tables_used
    : [];

  return (
    <div>
      <CurrentRiskScoreVisual data={data} />
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
          <dd>{reasonCodes.length > 0 ? reasonCodes.join(", ") : "n/a"}</dd>
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
            {sourceTablesUsed.length > 0 ? sourceTablesUsed.join(", ") : "n/a"}
          </dd>
        </div>
        <div>
          <dt>metadata.spot_price_row_found</dt>
          <dd>{formatValue(data.metadata?.spot_price_row_found)}</dd>
        </div>
        <div>
          <dt>metadata.power_balance_row_found</dt>
          <dd>{formatValue(data.metadata?.power_balance_row_found)}</dd>
        </div>
      </dl>
    </div>
  );
}

function CurrentRiskScoreVisual({ data }: { data: CurrentRiskResponse }) {
  const riskScore = parseRiskScore(data.risk_score);
  const riskLevel = formatValue(data.risk_level);
  const scoreLabel =
    riskScore === null ? "Unavailable" : `${formatNumber(riskScore)}/100`;
  const barWidth = riskScore === null ? 0 : riskScore;
  const riskLevelClass = getRiskLevelClass(data.risk_level);

  return (
    <section
      className="risk-score"
      aria-labelledby="current-risk-score-title"
    >
      <div className="risk-score__header">
        <div>
          <h3 id="current-risk-score-title">Decision-support risk score</h3>
          <p className="risk-score__review">Human review required</p>
        </div>
        <div className="risk-score__summary">
          <div
            className="risk-score__value"
            aria-label={`Risk score ${scoreLabel}`}
          >
            {scoreLabel}
          </div>
          <span className={`risk-score__level ${riskLevelClass}`}>
            {riskLevel}
          </span>
        </div>
      </div>
      <div
        className="risk-score__bar"
        role="meter"
        aria-label="Decision-support surplus risk score from 0 to 100"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={riskScore ?? undefined}
        aria-valuetext={
          riskScore === null
            ? `Risk score unavailable. Risk level ${riskLevel}.`
            : `Risk score ${formatNumber(
                riskScore
              )} out of 100. Risk level ${riskLevel}.`
        }
      >
        <div
          className="risk-score__fill"
          style={{ width: `${barWidth}%` }}
        />
      </div>
      <div className="risk-score__scale" aria-hidden="true">
        <span>0</span>
        <span>100</span>
      </div>
      {riskScore === null && (
        <p className="muted risk-score__fallback">
          risk_score is missing or outside the expected 0-100 range.
        </p>
      )}
    </section>
  );
}

function parseRiskScore(value: unknown): number | null {
  const parsed = parseNumber(
    typeof value === "string" || typeof value === "number" ? value : null
  );

  if (parsed === null || parsed < 0 || parsed > 100) {
    return null;
  }

  return parsed;
}

function getRiskLevelClass(value: unknown): string {
  if (value === "low" || value === "medium" || value === "high") {
    return `risk-score__level--${value}`;
  }

  return "risk-score__level--unknown";
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

function ReportSummaryPreviewCard({
  state,
  onLoad
}: {
  state: ReportRequestState;
  onLoad: () => void;
}) {
  const isLoading = state.status === "loading";

  return (
    <section className="card" aria-labelledby="report-summary-preview-title">
      <div className="card__header">
        <div>
          <h2 id="report-summary-preview-title">Report summary preview</h2>
          <p className="card__description">
            JSON preview only from the backend report summary preview endpoint.
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
        {isLoading ? "Loading..." : "Load report summary preview"}
      </button>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            No request has been made. Use the manual button to call{" "}
            <code>POST /api/report/summary/preview</code>.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">Loading report summary preview...</p>
        )}
        {state.status === "error" && (
          <p className="error">Backend unavailable: {state.message}</p>
        )}
        {state.status === "success" && (
          <ReportSummaryPreviewResult data={state.data} />
        )}
      </div>
    </section>
  );
}

function ReportMarkdownPreviewCard({
  state,
  onLoad
}: {
  state: ReportMarkdownRequestState;
  onLoad: () => void;
}) {
  const isLoading = state.status === "loading";

  return (
    <section className="card" aria-labelledby="report-markdown-preview-title">
      <div className="card__header">
        <div>
          <h2 id="report-markdown-preview-title">
            Report Markdown preview
          </h2>
          <p className="card__description">
            Markdown preview only from the backend report Markdown preview
            endpoint.
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
        {isLoading ? "Loading..." : "Load report Markdown preview"}
      </button>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            No request has been made. Use the manual button to call{" "}
            <code>POST /api/report/markdown/preview</code>.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">Loading report Markdown preview...</p>
        )}
        {state.status === "error" && (
          <p className="error">Backend unavailable: {state.message}</p>
        )}
        {state.status === "success" && (
          <ReportMarkdownPreviewResult data={state.data} />
        )}
      </div>
    </section>
  );
}

function ReportPdfPreviewCard({
  state,
  onLoad
}: {
  state: ReportPdfRequestState;
  onLoad: () => void;
}) {
  const isLoading = state.status === "loading";

  return (
    <section className="card" aria-labelledby="report-pdf-preview-title">
      <div className="card__header">
        <div>
          <h2 id="report-pdf-preview-title">
            Report PDF dry-run preview
          </h2>
          <p className="card__description">
            PDF dry-run preview only from the backend report PDF preview
            endpoint.
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
        {isLoading ? "Loading..." : "Load PDF dry-run preview"}
      </button>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            No request has been made. Use the manual button to call{" "}
            <code>POST /api/report/pdf/preview</code>.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">Loading PDF dry-run preview only...</p>
        )}
        {state.status === "error" && (
          <p className="error">Backend unavailable: {state.message}</p>
        )}
        {state.status === "success" && (
          <ReportPdfPreviewResult data={state.data} />
        )}
      </div>
    </section>
  );
}

function ReportPdfExportCard({
  state,
  onDownload
}: {
  state: ReportPdfExportRequestState;
  onDownload: () => void;
}) {
  const isLoading = state.status === "loading";

  return (
    <section className="card" aria-labelledby="report-pdf-export-title">
      <div className="card__header">
        <div>
          <h2 id="report-pdf-export-title">Report PDF export</h2>
          <p className="card__description">
            Manual PDF download from backend generated PDF bytes in memory.
          </p>
        </div>
        <span className="status">Read-only</span>
      </div>
      <button
        className="load-button"
        type="button"
        onClick={onDownload}
        disabled={isLoading}
      >
        {isLoading ? "Downloading..." : "Download PDF report"}
      </button>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            No request has been made. Use the manual button to call{" "}
            <code>POST /api/report/pdf/export</code>.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">Requesting manual PDF download...</p>
        )}
        {state.status === "error" && (
          <p className="error">Backend unavailable: {state.message}</p>
        )}
        {state.status === "success" && (
          <ReportPdfExportResult
            data={state.data}
            filename={state.filename}
          />
        )}
      </div>
    </section>
  );
}

function AuditedReportPdfExportCard({
  state,
  onDownload
}: {
  state: AuditedReportPdfExportRequestState;
  onDownload: () => void;
}) {
  const isLoading = state.status === "loading";

  return (
    <section className="card" aria-labelledby="audited-report-pdf-export-title">
      <div className="card__header">
        <div>
          <h2 id="audited-report-pdf-export-title">Audited PDF export</h2>
          <p className="card__description">
            Manual DK1 audited PDF download from backend generated PDF bytes.
          </p>
        </div>
        <span className="status status--warning">Audit DB write</span>
      </div>
      <ul className="safety-copy">
        <li>Generates PDF in memory.</li>
        <li>Persists one audit event to audit_events.</li>
        <li>Writes no server-side PDF file.</li>
        <li>Database write scope is audit_events only.</li>
        <li>Does not read/write energy data tables.</li>
        <li>Does not call live EDS/DMI APIs.</li>
        <li>Does not control, dispatch, or activate anything.</li>
        <li>Human review remains required.</li>
      </ul>
      <button
        className="load-button"
        type="button"
        onClick={onDownload}
        disabled={isLoading}
      >
        {isLoading ? "Downloading..." : "Download audited PDF"}
      </button>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            No request has been made. Use the manual button to call{" "}
            <code>POST /api/report/pdf/export/audited</code> with{" "}
            <code>{"{\"price_area\":\"DK1\"}"}</code>. The unaudited PDF
            export remains available separately.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">
            Requesting audited PDF download and audit event persistence...
          </p>
        )}
        {state.status === "error" && (
          <p className="error">Audited PDF export unavailable: {state.message}</p>
        )}
        {state.status === "success" && (
          <AuditedReportPdfExportResult
            data={state.data}
            filename={state.filename}
          />
        )}
      </div>
    </section>
  );
}

function AuditPdfExportPersistCard({
  state,
  onPersist
}: {
  state: AuditPdfExportPersistRequestState;
  onPersist: () => void;
}) {
  const isLoading = state.status === "loading";

  return (
    <section className="card" aria-labelledby="audit-pdf-export-persist-title">
      <div className="card__header">
        <div>
          <h2 id="audit-pdf-export-persist-title">
            Audit PDF export persistence
          </h2>
          <p className="card__description">
            Manual audit logging only for a DK1 PDF export request event.
          </p>
        </div>
        <span className="status status--warning">Audit DB write</span>
      </div>
      <ul className="safety-copy">
        <li>Audit DB write only.</li>
        <li>Writes only to audit_events.</li>
        <li>Does not generate PDF.</li>
        <li>Does not write files.</li>
        <li>Does not read/write energy data tables.</li>
        <li>Does not call live EDS/DMI APIs.</li>
        <li>Does not control, dispatch, or activate anything.</li>
        <li>Human review remains required.</li>
      </ul>
      <button
        className="load-button"
        type="button"
        onClick={onPersist}
        disabled={isLoading}
      >
        {isLoading ? "Persisting..." : "Persist audit event"}
      </button>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            No request has been made. Use the manual button to call{" "}
            <code>POST /api/audit/pdf-export/persist</code> with{" "}
            <code>{"{\"price_area\":\"DK1\"}"}</code>. This is not wired to
            PDF download.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">Persisting one manual audit event...</p>
        )}
        {state.status === "error" && (
          <p className="error">Audit persistence unavailable: {state.message}</p>
        )}
        {state.status === "success" && (
          <AuditPdfExportPersistResult data={state.data} />
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

function ReportSummaryPreviewResult({
  data
}: {
  data: ReportSummaryPreviewResponse;
}) {
  const summary = data.report_summary ?? {};

  return (
    <div>
      <p className="preview-note">
        JSON preview only. No PDF generated. No file written. Read-only
        decision support. Human review required.
      </p>
      <dl className="risk-list">
        <div>
          <dt>report_preview_generated</dt>
          <dd>{formatValue(data.report_preview_generated)}</dd>
        </div>
        <div>
          <dt>pdf_generated</dt>
          <dd>{formatValue(data.pdf_generated)}</dd>
        </div>
        <div>
          <dt>file_written</dt>
          <dd>{formatValue(data.file_written)}</dd>
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
        <div>
          <dt>decision_support_only</dt>
          <dd>{formatValue(data.decision_support_only)}</dd>
        </div>
      </dl>

      <section className="report-preview-section">
        <h3>Report</h3>
        <dl className="risk-list">
          <div>
            <dt>report title</dt>
            <dd>{formatValue(summary.title)}</dd>
          </div>
          <div>
            <dt>price_area</dt>
            <dd>{formatValue(summary.price_area)}</dd>
          </div>
          <div>
            <dt>generated_at_utc</dt>
            <dd>{formatValue(summary.generated_at_utc)}</dd>
          </div>
        </dl>
      </section>

      <ReportCurrentRiskSummary data={summary.current_risk_summary} />
      <ReportForecastWindowSummary data={summary.forecast_window_summary} />
      <StringList title="key_findings" values={summary.key_findings} />
      <StringList
        title="recommended_human_actions"
        values={summary.recommended_human_actions}
      />
      <StringList title="safety_notes" values={summary.safety_notes} />
      <StringList title="limitations" values={summary.limitations} />

      <section className="report-preview-section">
        <h3>explanation</h3>
        <p className="muted">{formatValue(data.explanation)}</p>
      </section>
      <SafetyBoundarySummary safetyBoundary={data.safety_boundary} />
    </div>
  );
}

function ReportMarkdownPreviewResult({
  data
}: {
  data: ReportMarkdownPreviewResponse;
}) {
  const summary = data.report_summary ?? {};

  return (
    <div>
      <p className="preview-note">
        Markdown preview only. No PDF generated. No file written. Read-only
        decision support. Human review required.
      </p>
      <dl className="risk-list">
        <div>
          <dt>markdown_preview_generated</dt>
          <dd>{formatValue(data.markdown_preview_generated)}</dd>
        </div>
        <div>
          <dt>pdf_generated</dt>
          <dd>{formatValue(data.pdf_generated)}</dd>
        </div>
        <div>
          <dt>file_written</dt>
          <dd>{formatValue(data.file_written)}</dd>
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
        <div>
          <dt>decision_support_only</dt>
          <dd>{formatValue(data.decision_support_only)}</dd>
        </div>
      </dl>

      <section className="report-preview-section">
        <h3>Report</h3>
        <dl className="risk-list">
          <div>
            <dt>report title</dt>
            <dd>{formatValue(summary.title)}</dd>
          </div>
          <div>
            <dt>price_area</dt>
            <dd>{formatValue(summary.price_area)}</dd>
          </div>
          <div>
            <dt>generated_at_utc</dt>
            <dd>{formatValue(summary.generated_at_utc)}</dd>
          </div>
        </dl>
      </section>

      <section className="report-preview-section">
        <h3>Rendered markdown</h3>
        <pre className="markdown-preview"><code>{formatValue(data.markdown)}</code></pre>
      </section>

      <SafetyBoundarySummary safetyBoundary={data.safety_boundary} />
    </div>
  );
}

function ReportPdfPreviewResult({
  data
}: {
  data: ReportPdfPreviewResponse;
}) {
  const summary = data.report_summary ?? {};

  return (
    <div>
      <p className="preview-note">
        PDF dry-run preview only. No PDF generated. No file written. No
        download available. Read-only decision support. Human review required.
      </p>
      <dl className="risk-list">
        <div>
          <dt>pdf_preview_planned</dt>
          <dd>{formatValue(data.pdf_preview_planned)}</dd>
        </div>
        <div>
          <dt>pdf_generated</dt>
          <dd>{formatValue(data.pdf_generated)}</dd>
        </div>
        <div>
          <dt>file_written</dt>
          <dd>{formatValue(data.file_written)}</dd>
        </div>
        <div>
          <dt>markdown_preview_generated</dt>
          <dd>{formatValue(data.markdown_preview_generated)}</dd>
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
        <div>
          <dt>decision_support_only</dt>
          <dd>{formatValue(data.decision_support_only)}</dd>
        </div>
        <div>
          <dt>planned_source</dt>
          <dd>{formatValue(data.planned_source)}</dd>
        </div>
        <div>
          <dt>planned_output_format</dt>
          <dd>{formatValue(data.planned_output_format)}</dd>
        </div>
        <div>
          <dt>markdown_character_count</dt>
          <dd>{formatValue(data.markdown_character_count)}</dd>
        </div>
      </dl>

      <section className="report-preview-section">
        <h3>Report</h3>
        <dl className="risk-list">
          <div>
            <dt>report title</dt>
            <dd>{formatValue(summary.title)}</dd>
          </div>
          <div>
            <dt>price_area</dt>
            <dd>{formatValue(summary.price_area)}</dd>
          </div>
          <div>
            <dt>generated_at_utc</dt>
            <dd>{formatValue(summary.generated_at_utc)}</dd>
          </div>
        </dl>
      </section>

      {data.markdown_excerpt ? (
        <section className="report-preview-section">
          <h3>markdown_excerpt</h3>
          <pre className="markdown-preview">
            <code>{data.markdown_excerpt}</code>
          </pre>
        </section>
      ) : null}

      <WarningList warnings={data.warnings} />
      <SafetyBoundarySummary safetyBoundary={data.safety_boundary} />
    </div>
  );
}

function ReportPdfExportResult({
  data,
  filename
}: {
  data: ReportPdfExportResponse;
  filename: string;
}) {
  return (
    <div>
      <p className="preview-note">
        PDF download requested/generated from backend in-memory response.
        Backend generated PDF bytes in memory. No server-side file written.
        Read-only decision support. Human review required. No database query
        or write.
      </p>
      <dl className="risk-list">
        <div>
          <dt>download_filename</dt>
          <dd>{filename}</dd>
        </div>
        <div>
          <dt>content-type</dt>
          <dd>{formatValue(data.contentType)}</dd>
        </div>
        <div>
          <dt>content-disposition</dt>
          <dd>{formatValue(data.contentDisposition)}</dd>
        </div>
        <div>
          <dt>byteLength</dt>
          <dd>{formatValue(data.byteLength)}</dd>
        </div>
        <div>
          <dt>decision_support_only header</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-decision-support-only"]
            )}
          </dd>
        </div>
        <div>
          <dt>file_written header</dt>
          <dd>
            {formatValue(data.safetyHeaders["x-flexsignal-file-written"])}
          </dd>
        </div>
        <div>
          <dt>database_query_executed header</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-database-query-executed"]
            )}
          </dd>
        </div>
        <div>
          <dt>database_write_performed header</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-database-write-performed"]
            )}
          </dd>
        </div>
        <div>
          <dt>requires_database_url header</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-requires-database-url"]
            )}
          </dd>
        </div>
      </dl>
    </div>
  );
}

function AuditedReportPdfExportResult({
  data,
  filename
}: {
  data: AuditedReportPdfExportResponse;
  filename: string;
}) {
  return (
    <div>
      <p className="preview-note">
        Audited PDF download requested manually. PDF bytes were generated in
        memory, one audit event was persisted to audit_events, no server-side
        PDF file was written, no energy data tables were read or written, and
        human review remains required.
      </p>
      <dl className="risk-list">
        <div>
          <dt>download_filename</dt>
          <dd>{filename}</dd>
        </div>
        <div>
          <dt>content-type</dt>
          <dd>{formatValue(data.contentType)}</dd>
        </div>
        <div>
          <dt>content-disposition</dt>
          <dd>{formatValue(data.contentDisposition)}</dd>
        </div>
        <div>
          <dt>byteLength</dt>
          <dd>{formatValue(data.byteLength)}</dd>
        </div>
        <div>
          <dt>starts_with_pdf</dt>
          <dd>{formatValue(data.startsWithPdf)}</dd>
        </div>
        <div>
          <dt>x-flexsignal-decision-support-only</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-decision-support-only"]
            )}
          </dd>
        </div>
        <div>
          <dt>x-flexsignal-file-written</dt>
          <dd>
            {formatValue(data.safetyHeaders["x-flexsignal-file-written"])}
          </dd>
        </div>
        <div>
          <dt>x-flexsignal-pdf-generated-in-memory</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-pdf-generated-in-memory"]
            )}
          </dd>
        </div>
        <div>
          <dt>x-flexsignal-audit-event-created</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-audit-event-created"]
            )}
          </dd>
        </div>
        <div>
          <dt>x-flexsignal-audit-event-persisted</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-audit-event-persisted"]
            )}
          </dd>
        </div>
        <div>
          <dt>x-flexsignal-audit-event-type</dt>
          <dd>
            {formatValue(data.safetyHeaders["x-flexsignal-audit-event-type"])}
          </dd>
        </div>
        <div>
          <dt>x-flexsignal-audit-event-id</dt>
          <dd>
            {formatValue(data.safetyHeaders["x-flexsignal-audit-event-id"])}
          </dd>
        </div>
        <div>
          <dt>x-flexsignal-audit-table</dt>
          <dd>{formatValue(data.safetyHeaders["x-flexsignal-audit-table"])}</dd>
        </div>
        <div>
          <dt>x-flexsignal-database-query-executed</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-database-query-executed"]
            )}
          </dd>
        </div>
        <div>
          <dt>x-flexsignal-database-write-performed</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-database-write-performed"]
            )}
          </dd>
        </div>
        <div>
          <dt>x-flexsignal-database-write-scope</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-database-write-scope"]
            )}
          </dd>
        </div>
        <div>
          <dt>x-flexsignal-requires-database-url</dt>
          <dd>
            {formatValue(
              data.safetyHeaders["x-flexsignal-requires-database-url"]
            )}
          </dd>
        </div>
        <div>
          <dt>x-flexsignal-no-control-dispatch-activation</dt>
          <dd>
            {formatValue(
              data.safetyHeaders[
                "x-flexsignal-no-control-dispatch-activation"
              ]
            )}
          </dd>
        </div>
      </dl>
    </div>
  );
}

function AuditPdfExportPersistResult({
  data
}: {
  data: AuditPdfExportPersistResponse;
}) {
  return (
    <div>
      <p className="preview-note">
        Manual audit DB write only. Persisted response is limited to
        audit_events. This does not generate a PDF, write files, read/write
        energy data tables, call live EDS/DMI APIs, or control, dispatch, or
        activate anything. Human review remains required.
      </p>
      <dl className="risk-list">
        <div>
          <dt>audit_event_created</dt>
          <dd>{formatValue(data.audit_event_created)}</dd>
        </div>
        <div>
          <dt>audit_event_persisted</dt>
          <dd>{formatValue(data.audit_event_persisted)}</dd>
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
        <div>
          <dt>event_id</dt>
          <dd>{formatValue(data.event_id)}</dd>
        </div>
        <div>
          <dt>event_type</dt>
          <dd>{formatValue(data.event_type)}</dd>
        </div>
        <div>
          <dt>table</dt>
          <dd>{formatValue(data.table)}</dd>
        </div>
        <div>
          <dt>conflict_behavior</dt>
          <dd>{formatValue(data.conflict_behavior)}</dd>
        </div>
        <div>
          <dt>event.action</dt>
          <dd>{formatValue(data.event.action)}</dd>
        </div>
        <div>
          <dt>event.resource_type</dt>
          <dd>{formatValue(data.event.resource_type)}</dd>
        </div>
        <div>
          <dt>event.resource_id</dt>
          <dd>{formatValue(data.event.resource_id)}</dd>
        </div>
      </dl>
      <WarningList warnings={data.warnings} />
    </div>
  );
}

function ReportCurrentRiskSummary({
  data
}: {
  data: ReportSummaryPreviewResponse["report_summary"]["current_risk_summary"];
}) {
  const reasonCodes = Array.isArray(data?.reason_codes)
    ? data.reason_codes
    : [];

  return (
    <section className="report-preview-section">
      <h3>current risk summary</h3>
      <dl className="risk-list">
        <div>
          <dt>status</dt>
          <dd>{formatValue(data?.status)}</dd>
        </div>
        <div>
          <dt>risk_level</dt>
          <dd>{formatValue(data?.risk_level)}</dd>
        </div>
        <div>
          <dt>risk_score</dt>
          <dd>{formatValue(data?.risk_score)}</dd>
        </div>
        <div>
          <dt>confidence_score</dt>
          <dd>{formatValue(data?.confidence_score)}</dd>
        </div>
        <div>
          <dt>reason_codes</dt>
          <dd>{reasonCodes.length > 0 ? reasonCodes.join(", ") : "n/a"}</dd>
        </div>
        <div>
          <dt>recommended_human_action</dt>
          <dd>{formatValue(data?.recommended_human_action)}</dd>
        </div>
        <div>
          <dt>model_version</dt>
          <dd>{formatValue(data?.model_version)}</dd>
        </div>
        <div>
          <dt>decision_support_only</dt>
          <dd>{formatValue(data?.decision_support_only)}</dd>
        </div>
      </dl>
    </section>
  );
}

function ReportForecastWindowSummary({
  data
}: {
  data: ReportSummaryPreviewResponse["report_summary"]["forecast_window_summary"];
}) {
  const windows = Array.isArray(data?.windows) ? data.windows : [];

  return (
    <section className="report-preview-section">
      <h3>forecast window summary</h3>
      <dl className="risk-list">
        <div>
          <dt>status</dt>
          <dd>{formatValue(data?.status)}</dd>
        </div>
        <div>
          <dt>model_version</dt>
          <dd>{formatValue(data?.model_version)}</dd>
        </div>
        <div>
          <dt>decision_support_only</dt>
          <dd>{formatValue(data?.decision_support_only)}</dd>
        </div>
      </dl>
      <div className="forecast-windows">
        {windows.length === 0 ? (
          <p className="muted">windows: n/a</p>
        ) : (
          windows.map((window, index) => (
            <ForecastWindow
              key={`${formatValue(window.window_label)}-${index}`}
              window={window}
            />
          ))
        )}
      </div>
    </section>
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

function StringList({
  title,
  values
}: {
  title: string;
  values?: string[];
}) {
  return (
    <section className="report-preview-section">
      <h3>{title}</h3>
      {!values || values.length === 0 ? (
        <p className="muted">n/a</p>
      ) : (
        <ul className="plain-list">
          {values.map((value) => (
            <li key={value}>{value}</li>
          ))}
        </ul>
      )}
    </section>
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
  const windows = Array.isArray(data.windows) ? data.windows : [];

  return (
    <div>
      <p className="preview-note">
        Synthetic/caller-provided preview data only. Deterministic preview for
        read-only decision support. Human review required.
      </p>
      {windows.length > 0 && <ForecastWindowVisual windows={windows} />}
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
        {windows.map((window, index) => (
          <ForecastWindow
            key={`${formatValue(window.window_label)}-${index}`}
            window={window}
          />
        ))}
      </div>
    </div>
  );
}

function ForecastWindowVisual({
  windows
}: {
  windows: ForecastWindowSummary[];
}) {
  return (
    <section
      className="forecast-visual"
      aria-labelledby="forecast-visual-title"
    >
      <div className="forecast-visual__header">
        <div>
          <h3 id="forecast-visual-title">Forecast window visual</h3>
          <p>Deterministic preview. Human review required.</p>
        </div>
        <span>Read-only decision support</span>
      </div>
      <div className="forecast-visual__windows">
        {windows.map((window, index) => (
          <ForecastWindowVisualItem
            key={`${formatValue(window.window_label)}-${index}`}
            window={window}
          />
        ))}
      </div>
    </section>
  );
}

function ForecastWindowVisualItem({
  window
}: {
  window: ForecastWindowSummary;
}) {
  const riskScore = parseForecastRiskScore(window);
  const scoreLabel =
    riskScore === null ? "Score unavailable" : `${formatNumber(riskScore)}/100`;
  const scoreSource =
    parseRiskScore(window.max_risk_score) !== null
      ? "max_risk_score"
      : "average_risk_score";
  const riskLevel = formatValue(window.risk_level);
  const riskLevelClass = getRiskLevelClass(window.risk_level);
  const reasonCodes = formatReasonCodes(window.top_reason_codes);

  return (
    <article className="forecast-visual__window">
      <div className="forecast-visual__window-header">
        <div>
          <h4>{formatValue(window.window_label)}</h4>
          <span className={`risk-score__level ${riskLevelClass}`}>
            {riskLevel}
          </span>
        </div>
        <div className="forecast-visual__score">
          <strong>{scoreLabel}</strong>
          <span>{scoreSource}</span>
        </div>
      </div>
      <div
        className="forecast-visual__bar"
        role="meter"
        aria-label={`${formatValue(
          window.window_label
        )} forecast preview risk score from 0 to 100`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={riskScore ?? undefined}
        aria-valuetext={
          riskScore === null
            ? `${formatValue(window.window_label)} risk score unavailable.`
            : `${formatValue(window.window_label)} risk score ${formatNumber(
                riskScore
              )} out of 100.`
        }
      >
        <div
          className="forecast-visual__fill"
          style={{ width: `${riskScore ?? 0}%` }}
        />
      </div>
      <dl className="forecast-visual__details">
        <div>
          <dt>top_reason_codes</dt>
          <dd>{reasonCodes}</dd>
        </div>
        <div>
          <dt>recommended_human_action</dt>
          <dd>{formatValue(window.recommended_human_action)}</dd>
        </div>
      </dl>
    </article>
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
  if (!Array.isArray(reasonCodes) || reasonCodes.length === 0) {
    return "n/a";
  }

  return reasonCodes
    .filter((reasonCode) => reasonCode && typeof reasonCode === "object")
    .slice(0, 3)
    .map((reasonCode) => {
      const reasonCodeLabel = formatValue(reasonCode.reason_code);
      const countLabel = formatValue(reasonCode.count);

      return countLabel === "n/a"
        ? reasonCodeLabel
        : `${reasonCodeLabel} (${countLabel})`;
    })
    .filter((reasonCodeLabel) => reasonCodeLabel !== "n/a")
    .join(", ") || "n/a";
}

function parseForecastRiskScore(window: ForecastWindowSummary): number | null {
  return (
    parseRiskScore(window.max_risk_score) ??
    parseRiskScore(window.average_risk_score)
  );
}

const REPORT_PDF_FALLBACK_FILENAME = "flexsignal-report-preview.pdf";

function getSafeReportPdfFilename(contentDisposition: string | null): string {
  const filename = parseContentDispositionFilename(contentDisposition);

  if (!filename) {
    return REPORT_PDF_FALLBACK_FILENAME;
  }

  const trimmed = filename.trim();
  const hasUnsafeCharacter = /[\/\\:\x00-\x1f\x7f]/.test(trimmed);
  const isPdf = trimmed.toLowerCase().endsWith(".pdf");

  if (
    trimmed.length === 0 ||
    trimmed.length > 120 ||
    hasUnsafeCharacter ||
    !isPdf
  ) {
    return REPORT_PDF_FALLBACK_FILENAME;
  }

  return trimmed;
}

function parseContentDispositionFilename(
  contentDisposition: string | null
): string | null {
  if (!contentDisposition) {
    return null;
  }

  const filenameStarMatch = contentDisposition.match(
    /filename\*=UTF-8''([^;]+)/i
  );

  if (filenameStarMatch?.[1]) {
    try {
      return decodeURIComponent(filenameStarMatch[1].trim());
    } catch {
      return null;
    }
  }

  const filenameMatch = contentDisposition.match(
    /filename=(?:"([^"]+)"|([^;]+))/i
  );

  return filenameMatch?.[1] ?? filenameMatch?.[2]?.trim() ?? null;
}

function downloadReportPdfBlob(blob: Blob, filename: string) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");

  try {
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
  } finally {
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
  }
}

function errorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "Request failed";
}

function SectionIntro({
  eyebrow,
  title,
  description
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="section-intro">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      <p className="lead">{description}</p>
    </div>
  );
}

function WeatherPlaceholder() {
  return (
    <section className="placeholder-panel" aria-labelledby="weather-title">
      <span className="status">Placeholder</span>
      <h2 id="weather-title">Weather integration not implemented yet</h2>
      <p>
        Future DMI/weather forecast module. This screen does not show fake live
        weather data, fake Denmark maps, or AI congestion claims.
      </p>
      <ul className="safety-copy safety-copy--compact">
        <li>Read-only decision support.</li>
        <li>No automatic control.</li>
        <li>No dispatch.</li>
        <li>No activation.</li>
        <li>Human review required.</li>
      </ul>
    </section>
  );
}

export default function DashboardPage() {
  const [activeSection, setActiveSection] =
    useState<DashboardSection>("dashboard");
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
  const [reportPreviewState, setReportPreviewState] =
    useState<ReportRequestState>({
      status: "idle"
    });
  const [reportMarkdownPreviewState, setReportMarkdownPreviewState] =
    useState<ReportMarkdownRequestState>({
      status: "idle"
    });
  const [reportPdfPreviewState, setReportPdfPreviewState] =
    useState<ReportPdfRequestState>({
      status: "idle"
    });
  const [reportPdfExportState, setReportPdfExportState] =
    useState<ReportPdfExportRequestState>({
      status: "idle"
    });
  const [auditedReportPdfExportState, setAuditedReportPdfExportState] =
    useState<AuditedReportPdfExportRequestState>({
      status: "idle"
    });
  const [auditPdfExportPersistState, setAuditPdfExportPersistState] =
    useState<AuditPdfExportPersistRequestState>({
      status: "idle"
    });

  function handleAreaChange(nextArea: PriceArea) {
    setSelectedArea(nextArea);
    setSpotPricesState({ status: "idle" });
    setPowerBalanceState({ status: "idle" });
    setCurrentRiskState({ status: "idle" });
    setForecastPreviewState({ status: "idle" });
    setFreshnessState({ status: "idle" });
    setReportPreviewState({ status: "idle" });
    setReportMarkdownPreviewState({ status: "idle" });
    setReportPdfPreviewState({ status: "idle" });
    setReportPdfExportState({ status: "idle" });
    setAuditedReportPdfExportState({ status: "idle" });
    setAuditPdfExportPersistState({ status: "idle" });
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

  async function handleLoadReportSummaryPreview() {
    setReportPreviewState({ status: "loading" });
    try {
      const data = await fetchReportSummaryPreview();
      setReportPreviewState({ status: "success", data });
    } catch (error) {
      setReportPreviewState({
        status: "error",
        message: errorMessage(error)
      });
    }
  }

  async function handleLoadReportMarkdownPreview() {
    setReportMarkdownPreviewState({ status: "loading" });
    try {
      const data = await fetchReportMarkdownPreview();
      setReportMarkdownPreviewState({ status: "success", data });
    } catch (error) {
      setReportMarkdownPreviewState({
        status: "error",
        message: errorMessage(error)
      });
    }
  }

  async function handleLoadReportPdfPreview() {
    setReportPdfPreviewState({ status: "loading" });
    try {
      const data = await fetchReportPdfPreview();
      setReportPdfPreviewState({ status: "success", data });
    } catch (error) {
      setReportPdfPreviewState({
        status: "error",
        message: errorMessage(error)
      });
    }
  }

  async function handleDownloadReportPdf() {
    setReportPdfExportState({ status: "loading" });
    try {
      const data = await fetchReportPdfExport();
      const filename = getSafeReportPdfFilename(data.contentDisposition);
      downloadReportPdfBlob(data.blob, filename);
      setReportPdfExportState({ status: "success", data, filename });
    } catch (error) {
      setReportPdfExportState({
        status: "error",
        message: errorMessage(error)
      });
    }
  }

  async function handleDownloadAuditedReportPdf() {
    setAuditedReportPdfExportState({ status: "loading" });
    try {
      const data = await fetchAuditedReportPdfExport();
      const filename = getSafeReportPdfFilename(data.contentDisposition);
      downloadReportPdfBlob(data.blob, filename);
      setAuditedReportPdfExportState({ status: "success", data, filename });
    } catch (error) {
      setAuditedReportPdfExportState({
        status: "error",
        message: errorMessage(error)
      });
    }
  }

  async function handlePersistAuditPdfExportEvent() {
    setAuditPdfExportPersistState({ status: "loading" });
    try {
      const data = await persistAuditPdfExportEvent();
      setAuditPdfExportPersistState({ status: "success", data });
    } catch (error) {
      setAuditPdfExportPersistState({
        status: "error",
        message: errorMessage(error)
      });
    }
  }

  const activeNavigationItem =
    navigationItems.find((item) => item.id === activeSection) ??
    navigationItems[0];

  const spotPriceCard = (
    <EnergyCard
      title="Spot prices"
      description="Manual read-only spot price rows from the backend request."
      endpointName="spot-prices"
      buttonLabel="Load spot prices"
      state={spotPricesState}
      columns={spotPriceColumns}
      onLoad={handleLoadSpotPrices}
      renderAfterTable={(data) => <SpotPriceTrendChart data={data} />}
    />
  );
  const powerBalanceCard = (
    <EnergyCard
      title="Power balance"
      description="Manual read-only power balance rows from the backend request."
      endpointName="power-balance"
      buttonLabel="Load power balance"
      state={powerBalanceState}
      columns={powerBalanceColumns}
      onLoad={handleLoadPowerBalance}
      renderAfterTable={(data) => <PowerBalanceTrendChart data={data} />}
    />
  );
  const currentRiskCard = (
    <CurrentRiskCard
      state={currentRiskState}
      onLoad={handleLoadCurrentRisk}
    />
  );
  const forecastPreviewCard = (
    <ForecastPreviewCard
      state={forecastPreviewState}
      onLoad={handleLoadForecastPreview}
    />
  );
  const freshnessCard = (
    <EnergyFreshnessCard
      state={freshnessState}
      onLoadDryRun={handleLoadFreshnessDryRun}
      onLoadRead={handleLoadFreshnessRead}
    />
  );
  const reportCards = (
    <>
      <ReportSummaryPreviewCard
        state={reportPreviewState}
        onLoad={handleLoadReportSummaryPreview}
      />
      <ReportMarkdownPreviewCard
        state={reportMarkdownPreviewState}
        onLoad={handleLoadReportMarkdownPreview}
      />
      <ReportPdfPreviewCard
        state={reportPdfPreviewState}
        onLoad={handleLoadReportPdfPreview}
      />
      <ReportPdfExportCard
        state={reportPdfExportState}
        onDownload={handleDownloadReportPdf}
      />
    </>
  );
  const auditCards = (
    <>
      <AuditedReportPdfExportCard
        state={auditedReportPdfExportState}
        onDownload={handleDownloadAuditedReportPdf}
      />
      <AuditPdfExportPersistCard
        state={auditPdfExportPersistState}
        onPersist={handlePersistAuditPdfExportEvent}
      />
    </>
  );

  function renderSectionContent() {
    switch (activeSection) {
      case "reports":
        return (
          <>
            <SectionIntro
              eyebrow="Reports"
              title="Report previews and PDF export"
              description="Manual report summary, Markdown, PDF dry-run, and unaudited PDF download flows. No files are written by the frontend and no live external data APIs are called."
            />
            <div className="summary summary--two">{reportCards}</div>
          </>
        );
      case "audit":
        return (
          <>
            <SectionIntro
              eyebrow="Audit"
              title="Audit evidence"
              description="Manual audit-focused flows for PDF export evidence. Audit writes remain explicit, scoped, and visible to the reviewer."
            />
            <div className="summary summary--two">{auditCards}</div>
          </>
        );
      case "forecast":
        return (
          <>
            <SectionIntro
              eyebrow="Forecast"
              title="Surplus risk forecast"
              description="Read-only current risk and deterministic forecast-window preview for human review. Forecasting remains explainable and manual."
            />
            <div className="summary summary--two">
              {currentRiskCard}
              {forecastPreviewCard}
            </div>
          </>
        );
      case "data":
        return (
          <>
            <SectionIntro
              eyebrow="Data"
              title="Stored energy data"
              description="Manual spot price, power balance, and freshness reads. The browser does not call Energi Data Service, DMI, or weather APIs directly."
            />
            <div className="summary">
              {spotPriceCard}
              {powerBalanceCard}
              {freshnessCard}
            </div>
          </>
        );
      case "weather":
        return (
          <>
            <SectionIntro
              eyebrow="Meteo / Weather"
              title="Weather module placeholder"
              description="A reserved frontend section for future weather forecast work. No weather integration is implemented in v0.1."
            />
            <WeatherPlaceholder />
          </>
        );
      case "dashboard":
      default:
        return (
          <>
            <SectionIntro
              eyebrow="Dashboard"
              title="FlexSignal AI overview"
              description="Minimal dashboard for Danish electricity decision support. Data loads only when requested from the backend API helper, and the frontend does not dispatch, activate, poll, control energy assets, run forecasting logic, or call external data APIs directly."
            />
            <div className="summary">
              {spotPriceCard}
              {powerBalanceCard}
              {currentRiskCard}
              {forecastPreviewCard}
            </div>
          </>
        );
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="sidebar__brand">
          <span className="sidebar__mark">FS</span>
          <div>
            <strong>N&amp;O Predict</strong>
            <span>FlexSignal AI</span>
          </div>
        </div>
        <nav className="sidebar__nav">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              className={
                item.id === activeSection
                  ? "nav-item nav-item--active"
                  : "nav-item"
              }
              type="button"
              onClick={() => setActiveSection(item.id)}
              aria-current={item.id === activeSection ? "page" : undefined}
            >
              <span>{item.label}</span>
              <small>{item.description}</small>
            </button>
          ))}
        </nav>
        <div className="sidebar__safety">
          <span>v0.1 boundary</span>
          <strong>Read-only decision support</strong>
          <p>No automatic control, dispatch, or activation.</p>
        </div>
      </aside>

      <div className="dashboard">
        <header className="topbar">
          <div>
            <p className="topbar__label">Current section</p>
            <h2>{activeNavigationItem.label}</h2>
          </div>
          <div className="topbar__meta">
            <div className="topbar__product">
              N&amp;O Predict / FlexSignal AI
            </div>
            <div className="system-status" aria-label="System Status: LIVE">
              <span className="system-status__dot" aria-hidden="true" />
              <span>System Status: LIVE</span>
            </div>
          </div>
        </header>

        <div className="dashboard__inner">
          <header className="dashboard__controls">
            <div className="safety-strip" aria-label="Safety boundary">
              <span>Read-only decision support</span>
              <span>No automatic control</span>
              <span>No dispatch</span>
              <span>No activation</span>
              <span>Human review required</span>
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

          {renderSectionContent()}

          <p className="api-note">
            Frontend requests use only the backend API base URL helper:{" "}
            <code>{backendApiBaseUrl}</code>. The browser does not call Energi
            Data Service, DMI, weather, or external data APIs directly, and
            nothing auto-loads or polls.
          </p>
        </div>
      </div>
    </main>
  );
}
