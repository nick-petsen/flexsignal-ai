"use client";

import { useState, type ReactNode } from "react";
import {
  backendApiBaseUrl,
  fetchAuditedReportPdfExport,
  fetchCurrentRisk,
  fetchDashboardDecisionSummaryPreview,
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
  type DashboardDecisionSummaryPreviewResponse,
  type DashboardDecisionSummaryStatus,
  type DashboardDecisionSummaryValue,
  type EnergyApiResponse,
  type EnergyFreshnessQueryPlan,
  type EnergyFreshnessReadResult,
  type EnergyFreshnessResponse,
  type ForecastPreviewResponse,
  type ForecastPreviewRow,
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
  | {
      status: "success";
      data: ForecastPreviewResponse;
      rows: ForecastPreviewRow[];
    }
  | { status: "error"; message: string };

type DecisionSummaryRequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: DashboardDecisionSummaryPreviewResponse }
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

type CockpitKpi = {
  label: string;
  value: string;
  detail: string;
  tone?: "neutral" | "good" | "warning" | "danger";
};

type PublicBacktestSnapshotArea = {
  area: PriceArea;
  joinedHours: number;
  skippedRows: number;
  mediumRiskHours: number;
  highRiskHours: number;
  riskWindows: number;
  highestRiskScore: number;
  negativePriceHours: number;
  lowPriceHours: number;
  averageRenewableShare: string;
  maxRenewableShare: string;
};

type PublicRiskWindowSnapshot = {
  area: PriceArea;
  start: string;
  end: string;
  durationHours: number;
  score: number;
  level: "medium" | "high";
  negativePriceHours: number;
  lowPriceHours: number;
  averageRenewableShare: string;
  maxRenewableShare: string;
  reasons: string[];
};

const priceAreas: PriceArea[] = ["DK1", "DK2"];
const forecastPreviewNumericFields: (keyof ForecastPreviewRow)[] = [
  "price_dkk_per_mwh",
  "production_mw",
  "consumption_mw",
  "wind_onshore_mw",
  "wind_offshore_mw",
  "solar_mw",
  "exchange_net_mw"
];

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

const publicBacktestSnapshotAreas: PublicBacktestSnapshotArea[] = [
  {
    area: "DK1",
    joinedHours: 4208,
    skippedRows: 233,
    mediumRiskHours: 1663,
    highRiskHours: 174,
    riskWindows: 129,
    highestRiskScore: 100,
    negativePriceHours: 132,
    lowPriceHours: 479,
    averageRenewableShare: "68.8%",
    maxRenewableShare: "192.2%"
  },
  {
    area: "DK2",
    joinedHours: 4208,
    skippedRows: 233,
    mediumRiskHours: 288,
    highRiskHours: 2,
    riskWindows: 72,
    highestRiskScore: 85,
    negativePriceHours: 78,
    lowPriceHours: 491,
    averageRenewableShare: "38.2%",
    maxRenewableShare: "108.6%"
  }
];

const publicRiskWindowSnapshots: PublicRiskWindowSnapshot[] = [
  {
    area: "DK1",
    start: "2026-04-04T21:00:00",
    end: "2026-04-06T23:00:00",
    durationHours: 51,
    score: 100,
    level: "high",
    negativePriceHours: 20,
    lowPriceHours: 39,
    averageRenewableShare: "98.6%",
    maxRenewableShare: "163.3%",
    reasons: [
      "low_price",
      "high_renewable_share",
      "renewable_generation_above_consumption",
      "negative_price"
    ]
  },
  {
    area: "DK1",
    start: "2026-04-24T06:00:00",
    end: "2026-04-25T22:00:00",
    durationHours: 41,
    score: 100,
    level: "high",
    negativePriceHours: 8,
    lowPriceHours: 18,
    averageRenewableShare: "117.3%",
    maxRenewableShare: "192.2%",
    reasons: [
      "high_renewable_share",
      "renewable_generation_above_consumption",
      "low_price",
      "negative_price"
    ]
  },
  {
    area: "DK1",
    start: "2026-05-29T06:00:00",
    end: "2026-05-29T16:00:00",
    durationHours: 11,
    score: 100,
    level: "high",
    negativePriceHours: 1,
    lowPriceHours: 6,
    averageRenewableShare: "108.6%",
    maxRenewableShare: "136.4%",
    reasons: [
      "high_renewable_share",
      "renewable_generation_above_consumption",
      "low_price",
      "negative_price"
    ]
  },
  {
    area: "DK1",
    start: "2026-06-13T02:00:00",
    end: "2026-06-15T18:00:00",
    durationHours: 65,
    score: 95,
    level: "high",
    negativePriceHours: 14,
    lowPriceHours: 33,
    averageRenewableShare: "110.2%",
    maxRenewableShare: "171.3%",
    reasons: [
      "high_renewable_share",
      "renewable_generation_above_consumption",
      "low_price",
      "negative_price"
    ]
  },
  {
    area: "DK1",
    start: "2026-05-26T10:00:00",
    end: "2026-05-28T01:00:00",
    durationHours: 40,
    score: 95,
    level: "high",
    negativePriceHours: 10,
    lowPriceHours: 12,
    averageRenewableShare: "113.2%",
    maxRenewableShare: "162.7%",
    reasons: [
      "high_renewable_share",
      "renewable_generation_above_consumption",
      "low_price",
      "negative_price"
    ]
  },
  {
    area: "DK2",
    start: "2026-04-24T21:00:00",
    end: "2026-04-25T06:00:00",
    durationHours: 10,
    score: 85,
    level: "high",
    negativePriceHours: 0,
    lowPriceHours: 3,
    averageRenewableShare: "98.0%",
    maxRenewableShare: "108.6%",
    reasons: [
      "high_renewable_share",
      "renewable_generation_above_consumption",
      "low_price"
    ]
  },
  {
    area: "DK2",
    start: "2026-06-14T20:00:00",
    end: "2026-06-15T04:00:00",
    durationHours: 9,
    score: 65,
    level: "medium",
    negativePriceHours: 0,
    lowPriceHours: 0,
    averageRenewableShare: "92.2%",
    maxRenewableShare: "100.7%",
    reasons: [
      "high_renewable_share",
      "renewable_generation_above_consumption"
    ]
  },
  {
    area: "DK2",
    start: "2026-01-01T17:00:00",
    end: "2026-01-02T05:00:00",
    durationHours: 13,
    score: 60,
    level: "medium",
    negativePriceHours: 0,
    lowPriceHours: 13,
    averageRenewableShare: "77.1%",
    maxRenewableShare: "85.4%",
    reasons: ["low_price", "medium_renewable_share", "high_renewable_share"]
  },
  {
    area: "DK2",
    start: "2026-04-03T21:00:00",
    end: "2026-04-04T08:00:00",
    durationHours: 12,
    score: 60,
    level: "medium",
    negativePriceHours: 0,
    lowPriceHours: 10,
    averageRenewableShare: "90.2%",
    maxRenewableShare: "97.3%",
    reasons: ["high_renewable_share", "low_price"]
  },
  {
    area: "DK2",
    start: "2026-03-25T20:00:00",
    end: "2026-03-26T05:00:00",
    durationHours: 10,
    score: 60,
    level: "medium",
    negativePriceHours: 0,
    lowPriceHours: 8,
    averageRenewableShare: "84.8%",
    maxRenewableShare: "90.8%",
    reasons: ["high_renewable_share", "low_price"]
  }
];

const publicRiskReasonLabels: Record<string, string> = {
  high_renewable_share: "High renewable share",
  low_price: "Low price hours",
  medium_renewable_share: "Medium renewable share",
  negative_price: "Negative price hours",
  renewable_generation_above_consumption:
    "Renewable generation above consumption"
};

const PUBLIC_PROOF_OF_WORK_REPORT_FILENAME =
  "public-surplus-risk-proof-of-work.md";

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
            Awaiting manual load. Use the button to load read-only data for
            review.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">Loading read-only data...</p>
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
            Manual read-only risk view for human review.
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
        {isLoading ? "Loading..." : "Load latest risk view"}
      </button>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            Awaiting manual load. Use the button to load the latest risk view.
          </p>
        )}
        {state.status === "loading" && (
          <p className="muted">Loading read-only risk view...</p>
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

function formatRiskLabel(value: unknown): string {
  if (value === "low" || value === "medium" || value === "high") {
    return value.charAt(0).toUpperCase() + value.slice(1);
  }

  return "Not available";
}

function formatConfidence(value: unknown): string {
  const parsed = parseNumber(
    typeof value === "string" || typeof value === "number" ? value : null
  );

  if (parsed === null) {
    return "Not available";
  }

  return parsed >= 0 && parsed <= 1
    ? `${formatNumber(parsed * 100)}%`
    : formatNumber(parsed);
}

function formatSummaryStatus(
  status: DashboardDecisionSummaryStatus | undefined,
  availableLabel = "Available"
): string {
  switch (status) {
    case "available":
      return availableLabel;
    case "limited":
      return "Limited";
    case "not_available":
      return "Not available";
    case "not_calculated":
      return "Not calculated yet";
    case undefined:
    case "":
      return "Not available";
    default:
      return status
        .split("_")
        .filter(Boolean)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
  }
}

function getDecisionSummaryIdleKpis(): CockpitKpi[] {
  return [
    {
      label: "Current risk",
      value: "Awaiting manual refresh",
      detail: "Use Load decision summary to refresh this view."
    },
    {
      label: "Next surplus window",
      value: "Not calculated yet",
      detail: "Forecast window is not available in this summary yet."
    },
    {
      label: "Confidence",
      value: "Not available",
      detail: "Awaiting manual refresh."
    },
    {
      label: "Expected impact",
      value: "Not calculated yet",
      detail: "Expected impact model is not enabled yet."
    },
    {
      label: "Economic potential",
      value: "Not calculated yet",
      detail: "Economic potential model is not enabled yet."
    },
    {
      label: "Data freshness",
      value: "Not available",
      detail: "Awaiting manual refresh."
    },
    {
      label: "Recommended action",
      value: "Human review required",
      detail: "Decision support only."
    }
  ];
}

function getDecisionSummaryLoadingKpis(): CockpitKpi[] {
  return getDecisionSummaryIdleKpis().map((item) => ({
    ...item,
    value: "Loading...",
    detail: "Decision summary is being loaded."
  }));
}

function getDecisionSummaryErrorKpis(message: string): CockpitKpi[] {
  return getDecisionSummaryIdleKpis().map((item) => ({
    ...item,
    detail:
      item.label === "Current risk"
        ? `Decision summary unavailable: ${message}`
        : "Awaiting manual refresh."
  }));
}

function getDecisionSummaryKpis(
  state: DecisionSummaryRequestState
): CockpitKpi[] {
  if (state.status === "loading") {
    return getDecisionSummaryLoadingKpis();
  }

  if (state.status === "error") {
    return getDecisionSummaryErrorKpis(state.message);
  }

  if (state.status !== "success") {
    return getDecisionSummaryIdleKpis();
  }

  return [
    getDecisionSummaryCurrentRiskKpi(state.data),
    getDecisionSummaryWindowKpi(state.data),
    getDecisionSummaryConfidenceKpi(state.data),
    getDecisionSummaryExpectedImpactKpi(state.data.expected_impact),
    getDecisionSummaryEconomicPotentialKpi(state.data.economic_potential),
    getDecisionSummaryFreshnessKpi(state.data),
    getDecisionSummaryRecommendedActionKpi(state.data)
  ];
}

function getDecisionSummaryCurrentRiskKpi(
  data: DashboardDecisionSummaryPreviewResponse
): CockpitKpi {
  const currentRisk = data.current_risk;

  if (currentRisk.status === "not_available") {
    return {
      label: "Current risk",
      value: "Not available",
      detail: "Awaiting manual refresh."
    };
  }

  const riskLevel = currentRisk.risk_level;
  const riskScore = parseRiskScore(currentRisk.risk_score);
  const detail =
    riskScore === null
      ? "Risk score not available. Human review required."
      : `Risk score ${formatNumber(riskScore)}. Human review required.`;

  return {
    label: "Current risk",
    value: formatRiskLabel(riskLevel),
    detail,
    tone:
      riskLevel === "high"
        ? "danger"
        : riskLevel === "medium"
          ? "warning"
          : riskLevel === "low"
            ? "good"
            : undefined
  };
}

function getDecisionSummaryWindowKpi(
  data: DashboardDecisionSummaryPreviewResponse
): CockpitKpi {
  const window = data.next_surplus_window;

  if (window.status === "not_calculated") {
    return {
      label: "Next surplus window",
      value: "Not calculated yet",
      detail: "Forecast window is not available in this summary yet."
    };
  }

  if (window.status === "not_available") {
    return {
      label: "Next surplus window",
      value: "Not available",
      detail: "Forecast window is not available in this summary yet."
    };
  }

  return {
    label: "Next surplus window",
    value:
      getSummaryValue(window) ??
      formatSummaryStatus(window.status, "Data available"),
    detail: "Human review required."
  };
}

function getDecisionSummaryConfidenceKpi(
  data: DashboardDecisionSummaryPreviewResponse
): CockpitKpi {
  const confidenceValue =
    data.confidence.value ?? data.current_risk.confidence_score;

  if (confidenceValue !== undefined && confidenceValue !== null) {
    return {
      label: "Confidence",
      value: formatConfidence(confidenceValue),
      detail: "Human review required."
    };
  }

  return {
    label: "Confidence",
    value: formatSummaryStatus(data.confidence.status),
    detail: "Awaiting manual refresh."
  };
}

function getDecisionSummaryExpectedImpactKpi(
  expectedImpact: DashboardDecisionSummaryValue
): CockpitKpi {
  return getDecisionSummaryMetricKpi(
    "Expected impact",
    expectedImpact,
    "Expected impact model is not enabled yet."
  );
}

function getDecisionSummaryEconomicPotentialKpi(
  economicPotential: DashboardDecisionSummaryValue
): CockpitKpi {
  if (economicPotential.status === "calculated") {
    const value =
      typeof economicPotential.value === "string" &&
      economicPotential.value.trim()
        ? economicPotential.value.trim()
        : typeof economicPotential.value === "number" &&
            Number.isFinite(economicPotential.value)
          ? String(economicPotential.value)
          : "Not available";

    return {
      label: "Economic potential",
      value,
      detail:
        "Estimated €/MWh opportunity based on forecast inputs. Not a revenue forecast."
    };
  }

  return getDecisionSummaryMetricKpi(
    "Economic potential",
    economicPotential,
    "Economic potential model is not enabled yet."
  );
}

function getDecisionSummaryMetricKpi(
  label: string,
  metric: DashboardDecisionSummaryValue,
  fallbackDetail: string
): CockpitKpi {
  if (metric.status === "not_calculated") {
    return {
      label,
      value: "Not calculated yet",
      detail: fallbackDetail
    };
  }

  if (metric.status === "not_available") {
    return {
      label,
      value: "Not available",
      detail: fallbackDetail
    };
  }

  return {
    label,
    value:
      getSummaryValue(metric) ??
      formatSummaryStatus(metric.status, "Data available"),
    detail: "Human review required."
  };
}

function getDecisionSummaryFreshnessKpi(
  data: DashboardDecisionSummaryPreviewResponse
): CockpitKpi {
  const freshness = data.data_freshness;
  const rowCounts =
    typeof freshness.spot_price_row_count === "number" &&
    typeof freshness.power_balance_row_count === "number"
      ? `Rows available: spot prices ${freshness.spot_price_row_count}, power balance ${freshness.power_balance_row_count}.`
      : null;

  return {
    label: "Data freshness",
    value: formatSummaryStatus(freshness.status, "Data available"),
    detail: rowCounts || "Awaiting manual refresh.",
    tone:
      freshness.status === "available"
        ? "good"
        : freshness.status === "limited" || freshness.status === "not_available"
          ? "warning"
          : undefined
  };
}

function getDecisionSummaryRecommendedActionKpi(
  data: DashboardDecisionSummaryPreviewResponse
): CockpitKpi {
  const action = data.recommended_human_action.trim();

  return {
    label: "Recommended action",
    value: action || "Human review required",
    detail: "Decision support only. Human review required."
  };
}

function getSummaryValue(
  metric: DashboardDecisionSummaryValue & { window_label?: string }
): string | null {
  if (typeof metric.window_label === "string" && metric.window_label.trim()) {
    return metric.window_label.trim();
  }

  if (typeof metric.value === "string" && metric.value.trim()) {
    return metric.value.trim();
  }

  if (typeof metric.value === "number" && Number.isFinite(metric.value)) {
    return formatNumber(metric.value);
  }

  if (typeof metric.label === "string" && metric.label.trim()) {
    return metric.label.trim();
  }

  if (typeof metric.summary === "string" && metric.summary.trim()) {
    return metric.summary.trim();
  }

  return null;
}

function getDecisionSummarySourceNotes(
  data: DashboardDecisionSummaryPreviewResponse
): string[] {
  const notes = Object.values(data.source_notes ?? {}).filter(
    (note): note is string => typeof note === "string" && note.trim().length > 0
  );
  const warnings = (data.warnings ?? [])
    .filter((warning) => warning.trim().length > 0)
    .map((warning) => `Backend note: ${warning.replaceAll("_", " ")}.`);

  return [...notes, ...warnings].slice(0, 8);
}

function getCurrentRiskKpi(state: RiskRequestState): CockpitKpi {
  if (state.status === "loading") {
    return {
      label: "Current risk",
      value: "Loading...",
      detail: "Manual risk view is being loaded."
    };
  }

  if (state.status === "error") {
    return {
      label: "Current risk",
      value: "Not loaded yet",
      detail: "Awaiting manual refresh."
    };
  }

  if (state.status === "success") {
    const riskLevel = state.data.risk_level;
    const riskScore = parseRiskScore(state.data.risk_score);
    const riskDetail =
      riskScore === null
        ? "Risk score not available. Human review required."
        : `Risk score ${formatNumber(riskScore)}. Human review required.`;

    return {
      label: "Current risk",
      value: formatRiskLabel(riskLevel),
      detail: riskDetail,
      tone:
        riskLevel === "high"
          ? "danger"
          : riskLevel === "medium"
            ? "warning"
            : riskLevel === "low"
              ? "good"
              : undefined
    };
  }

  return {
    label: "Current risk",
    value: "Not loaded yet",
    detail: "Awaiting manual refresh."
  };
}

function getForecastWindowKpi(state: ForecastRequestState): CockpitKpi {
  if (state.status === "loading") {
    return {
      label: "Next surplus window",
      value: "Loading...",
      detail: "Manual forecast window review is running."
    };
  }

  if (state.status === "error") {
    return {
      label: "Next surplus window",
      value: "Not calculated yet",
      detail: "Forecast window is not available in this summary yet."
    };
  }

  if (state.status === "success") {
    const nextWindow = getNextForecastWindow(state.data);

    return {
      label: "Next surplus window",
      value: nextWindow?.window_label
        ? formatValue(nextWindow.window_label)
        : "Not calculated yet",
      detail: nextWindow
        ? `Risk ${formatValue(nextWindow.risk_level)}. Human review required.`
        : "Forecast window is not available in this summary yet."
    };
  }

  return {
    label: "Next surplus window",
    value: "Not calculated yet",
    detail: "Forecast window is not available in this summary yet."
  };
}

function getConfidenceKpi(
  riskState: RiskRequestState,
  forecastState: ForecastRequestState
): CockpitKpi {
  if (riskState.status === "loading" || forecastState.status === "loading") {
    return {
      label: "Confidence",
      value: "Loading...",
      detail: "Manual review is being loaded."
    };
  }

  if (forecastState.status === "success") {
    const nextWindow = getNextForecastWindow(forecastState.data);
    const confidence = nextWindow?.average_confidence_score;

    return {
      label: "Confidence",
      value: formatConfidence(confidence),
      detail: nextWindow
        ? "From the reviewed forecast window."
        : "Forecast window is not available in this summary yet."
    };
  }

  if (riskState.status === "success") {
    return {
      label: "Confidence",
      value: formatConfidence(riskState.data.confidence_score),
      detail: "From the loaded risk view."
    };
  }

  return {
    label: "Confidence",
    value: "Not available",
    detail: "Awaiting manual refresh."
  };
}

function getNextForecastWindow(
  data: ForecastPreviewResponse
): ForecastWindowSummary | undefined {
  const windows = Array.isArray(data.windows) ? data.windows : [];

  return windows[0];
}

function getExpectedImpactKpi(state: ForecastRequestState): CockpitKpi {
  if (state.status === "loading") {
    return {
      label: "Expected impact",
      value: "Loading...",
      detail: "Manual forecast window review is running."
    };
  }

  if (state.status === "success") {
    const nextWindow = getNextForecastWindow(state.data);
    const impact = getExistingStringOrNumberField(
      nextWindow,
      "expected_impact",
      "impact",
      "estimated_impact"
    );

    return {
      label: "Expected impact",
      value: impact ?? "Not calculated yet",
      detail: impact
        ? "From the reviewed forecast window."
        : "Expected impact model is not enabled yet."
    };
  }

  return {
    label: "Expected impact",
    value: "Not calculated yet",
    detail: "Expected impact model is not enabled yet."
  };
}

function getExistingStringOrNumberField(
  source: unknown,
  ...fieldNames: string[]
): string | null {
  if (!source || typeof source !== "object") {
    return null;
  }

  const record = source as Record<string, unknown>;

  for (const fieldName of fieldNames) {
    const value = record[fieldName];

    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }

    if (typeof value === "number" && Number.isFinite(value)) {
      return formatNumber(value);
    }
  }

  return null;
}

function getLatestFreshnessTimestamp(data: EnergyFreshnessResponse): string | null {
  const spotPriceFreshness =
    data.spot_price_freshness ??
    data.freshness_result?.spot_price_freshness;
  const powerBalanceFreshness =
    data.power_balance_freshness ??
    data.freshness_result?.power_balance_freshness;
  const timestamps = [
    spotPriceFreshness?.latest_timestamp,
    powerBalanceFreshness?.latest_timestamp
  ].filter((timestamp): timestamp is string => Boolean(timestamp));

  if (timestamps.length === 0) {
    return null;
  }

  return timestamps.sort().at(-1) ?? null;
}

function getFreshnessReadResults(
  data: EnergyFreshnessResponse
): EnergyFreshnessReadResult[] {
  const results = [
    data.spot_price_freshness ??
      data.freshness_result?.spot_price_freshness,
    data.power_balance_freshness ??
      data.freshness_result?.power_balance_freshness
  ].filter((result): result is EnergyFreshnessReadResult => Boolean(result));

  return results;
}

function getFreshnessStatus(data: EnergyFreshnessResponse): {
  label: "OK" | "stale" | "missing" | "not available";
  tone?: CockpitKpi["tone"];
} {
  const results = getFreshnessReadResults(data);

  if (data.dry_run || results.length === 0) {
    return { label: "not available" };
  }

  const warnings = [
    ...(data.warnings ?? []),
    ...(data.freshness_result?.warnings ?? []),
    ...results
      .map((result) => result.warning)
      .filter((warning): warning is string => Boolean(warning))
  ];
  const warningText = warnings.join(" ").toLowerCase();
  const hasMissingRows = results.some((result) => result.row_count === 0);
  const hasTimestamp = results.some((result) => Boolean(result.latest_timestamp));

  if (hasMissingRows || warningText.includes("missing") || warningText.includes("no ")) {
    return { label: "missing", tone: "warning" };
  }

  if (warningText.includes("stale") || warningText.includes("outdated")) {
    return { label: "stale", tone: "warning" };
  }

  if (hasTimestamp) {
    return { label: "OK", tone: "good" };
  }

  return { label: "not available" };
}

function getFreshnessKpi(state: FreshnessRequestState): CockpitKpi {
  if (state.status === "loading") {
    return {
      label: "Data freshness",
      value: "Loading...",
      detail: "Manual freshness check is running."
    };
  }

  if (state.status === "error") {
    return {
      label: "Data freshness",
      value: "Not loaded yet",
      detail: "Awaiting manual refresh."
    };
  }

  if (state.status === "success") {
    if (state.data.dry_run) {
      return {
        label: "Data freshness",
        value: "not available",
        detail: "Dry-run plan only. No freshness result calculated."
      };
    }

    const latestTimestamp = getLatestFreshnessTimestamp(state.data);
    const freshnessStatus = getFreshnessStatus(state.data);
    const timestampDetail = latestTimestamp
      ? `Last updated ${formatShortTimestamp(latestTimestamp)}.`
      : "No stored timestamp returned.";

    return {
      label: "Data freshness",
      value: freshnessStatus.label,
      detail: `${timestampDetail} Manual freshness read only.`,
      tone: freshnessStatus.tone
    };
  }

  return {
    label: "Data freshness",
    value: "Not loaded yet",
    detail: "Awaiting manual refresh."
  };
}

function getRecommendedActionKpi(state: RiskRequestState): CockpitKpi {
  if (state.status === "loading") {
    return {
      label: "Recommended action",
      value: "Loading...",
      detail: "Awaiting manual risk view."
    };
  }

  if (state.status === "success") {
    const action =
      typeof state.data.recommended_human_action === "string"
        ? state.data.recommended_human_action.trim()
        : "";

    return {
      label: "Recommended action",
      value: action || "No recommendation available yet",
      detail: "Decision support only. Human review required."
    };
  }

  return {
    label: "Recommended action",
    value: "No recommendation available yet",
    detail: "Awaiting manual refresh."
  };
}

function getRiskActionStatus(state: RiskRequestState): string {
  switch (state.status) {
    case "loading":
      return "Loading latest risk view...";
    case "success":
      return "Latest risk view loaded.";
    case "error":
      return `Risk view unavailable: ${state.message}`;
    case "idle":
    default:
      return "Awaiting manual review.";
  }
}

function getForecastActionStatus(state: ForecastRequestState): string {
  switch (state.status) {
    case "loading":
      return "Reviewing forecast window...";
    case "success":
      return "Forecast window reviewed.";
    case "error":
      return `Forecast window unavailable: ${state.message}`;
    case "idle":
    default:
      return "Awaiting manual review.";
  }
}

function getFreshnessActionStatus(state: FreshnessRequestState): string {
  switch (state.status) {
    case "loading":
      return "Checking data freshness...";
    case "success":
      return "Data freshness checked.";
    case "error":
      return `Data freshness unavailable: ${state.message}`;
    case "idle":
    default:
      return "Awaiting manual review.";
  }
}

function getDecisionSummaryActionStatus(
  state: DecisionSummaryRequestState
): string {
  switch (state.status) {
    case "loading":
      return "Loading decision summary...";
    case "success":
      return "Decision summary loaded.";
    case "error":
      return `Decision summary unavailable: ${state.message}`;
    case "idle":
    default:
      return "Awaiting manual refresh.";
  }
}

function getActionStatusClass(
  state:
    | RiskRequestState
    | ForecastRequestState
    | FreshnessRequestState
    | DecisionSummaryRequestState
): string {
  const baseClass = "decision-overview__action-status-item";

  if (state.status === "success") {
    return `${baseClass} ${baseClass}--success`;
  }

  if (state.status === "error") {
    return `${baseClass} ${baseClass}--error`;
  }

  return baseClass;
}

function getDecisionOverviewItemClass(item: CockpitKpi): string {
  const classNames = ["decision-overview__item"];

  if (item.label === "Current risk" || item.label === "Next surplus window") {
    classNames.push("decision-overview__item--primary");
  }

  if (item.label === "Economic potential") {
    classNames.push("decision-overview__item--secondary-feature");
  }

  if (item.tone) {
    classNames.push(`decision-overview__item--${item.tone}`);
  }

  return classNames.join(" ");
}

function getForecastRowsForDecisionSummary(
  state: ForecastRequestState,
  selectedArea: PriceArea
): ForecastPreviewRow[] | undefined {
  if (
    state.status !== "success" ||
    state.data.price_area !== selectedArea ||
    state.rows.length === 0
  ) {
    return undefined;
  }

  const rows = state.rows.filter((row) =>
    isValidForecastPreviewRowForArea(row, selectedArea)
  );

  return rows.length === state.rows.length ? rows : undefined;
}

function isValidForecastPreviewRowForArea(
  row: ForecastPreviewRow,
  selectedArea: PriceArea
): boolean {
  return (
    row.price_area === selectedArea &&
    isTimezoneAwareTimestamp(row.timestamp_utc) &&
    forecastPreviewNumericFields.every((field) =>
      isNullableFiniteNumber(row[field])
    )
  );
}

function isTimezoneAwareTimestamp(value: string): boolean {
  return (
    value.trim().length > 0 &&
    /(?:Z|[+-]\d{2}:\d{2})$/.test(value) &&
    Number.isFinite(Date.parse(value))
  );
}

function isNullableFiniteNumber(value: unknown): boolean {
  return value === undefined || value === null || Number.isFinite(value);
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
            Manual review of deterministic forecast windows from provided rows.
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
        {isLoading ? "Loading..." : "Review forecast window"}
      </button>
      <div className="result" aria-live="polite">
        {state.status === "idle" && (
          <p className="muted">
            Not calculated. Use the manual button to review the forecast
            window.
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

function PublicBacktestSnapshot() {
  return (
    <section
      className="public-backtest"
      aria-labelledby="public-backtest-title"
    >
      <div className="public-backtest__header">
        <div>
          <p className="eyebrow">Public surplus-risk proof-of-work</p>
          <h2 id="public-backtest-title">
            Identified historical DK1/DK2 risk windows
          </h2>
          <p>
            Documented verified public backtest snapshot from Energi Data
            Service DayAheadPrices and ProductionConsumptionSettlement data.
            Not customer-specific savings.
          </p>
        </div>
        <span className="status">Read-only snapshot</span>
      </div>

      <dl className="public-backtest__meta" aria-label="Snapshot metadata">
        <div>
          <dt>Period</dt>
          <dd>2026-01-01 to now</dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>
            Energi Data Service DayAheadPrices +
            ProductionConsumptionSettlement
          </dd>
        </div>
        <div>
          <dt>dry_run</dt>
          <dd>true</dd>
        </div>
        <div>
          <dt>file_written</dt>
          <dd>false</dd>
        </div>
        <div>
          <dt>database_write_performed</dt>
          <dd>false</dd>
        </div>
      </dl>

      <div className="public-backtest__cards">
        {publicBacktestSnapshotAreas.map((snapshot) => (
          <PublicBacktestSnapshotCard
            key={snapshot.area}
            snapshot={snapshot}
          />
        ))}
      </div>

      <div className="public-backtest__download">
        <button
          className="load-button load-button--secondary"
          type="button"
          onClick={downloadPublicProofOfWorkReport}
        >
          Download proof-of-work report
        </button>
        <p>
          Downloads a static verified public backtest report. No backend call
          is made.
        </p>
      </div>

      <div className="public-backtest__explanation">
        <section>
          <h3>Interpretation</h3>
          <p>
            The result shows that the system can identify historical
            surplus-risk windows using public market, consumption, and
            renewable production data.
          </p>
        </section>
        <section>
          <h3>Limitations</h3>
          <ul className="plain-list">
            <li>Public market/system-level only.</li>
            <li>Not customer-specific savings.</li>
            <li>No customer load/asset/tariff data.</li>
            <li>Read-only decision support.</li>
            <li>No automatic control, dispatch, or activation.</li>
          </ul>
        </section>
      </div>
    </section>
  );
}

function buildPublicProofOfWorkMarkdownReport(): string {
  const summaryRows = publicBacktestSnapshotAreas
    .map(
      (snapshot) =>
        `| ${snapshot.area} | ${formatNumber(
          snapshot.joinedHours
        )} | ${formatNumber(snapshot.skippedRows)} | ${formatNumber(
          snapshot.mediumRiskHours
        )} | ${formatNumber(snapshot.highRiskHours)} | ${formatNumber(
          snapshot.riskWindows
        )} | ${formatNumber(snapshot.highestRiskScore)} | ${formatNumber(
          snapshot.negativePriceHours
        )} | ${formatNumber(snapshot.lowPriceHours)} | ${
          snapshot.averageRenewableShare
        } | ${snapshot.maxRenewableShare} |`
    )
    .join("\n");
  const windowRows = publicRiskWindowSnapshots
    .map(
      (snapshot) =>
        `| ${snapshot.area} | ${snapshot.start} | ${snapshot.end} | ${
          snapshot.durationHours
        }h | ${formatNumber(snapshot.score)} | ${snapshot.level} | ${formatNumber(
          snapshot.lowPriceHours
        )} | ${formatNumber(snapshot.negativePriceHours)} | ${
          snapshot.averageRenewableShare
        } | ${snapshot.maxRenewableShare} | ${snapshot.reasons
          .map((reason) => publicRiskReasonLabels[reason] ?? reason)
          .join(", ")} |`
    )
    .join("\n");

  return [
    "# Public DK1/DK2 surplus-risk proof-of-work",
    "",
    "title: Public DK1/DK2 surplus-risk proof-of-work",
    "period: 2026-01-01 to now",
    "source: Energi Data Service DayAheadPrices + ProductionConsumptionSettlement",
    "",
    "## DK1/DK2 summary metrics",
    "",
    "| Area | Joined hours | Skipped rows | Medium-risk hours | High-risk hours | Risk windows | Highest score | Negative price hours | Low price hours | Average renewable share | Max renewable share |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    summaryRows,
    "",
    "## Verified top risk windows",
    "",
    "| Area | Start | End | Duration | Score | Level | Low price hours | Negative price hours | Average renewable share | Max renewable share | Main reasons |",
    "| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |",
    windowRows,
    "",
    "## Commercial interpretation",
    "",
    "The verified public backtest shows that DK1/DK2 surplus-risk windows can be identified from public market, consumption, and renewable production data. This is public market/system-level evidence for human review. It is not customer-specific savings and does not say customers saved money.",
    "",
    "## Limitations",
    "",
    "- Public market/system-level only.",
    "- Not customer-specific savings.",
    "- No customer load, asset, tariff, operating schedule, or site constraint data.",
    "- Read-only decision support only.",
    "- Does not establish production readiness.",
    "",
    "## Next customer pilot step",
    "",
    "Review the public proof-of-work with a pilot customer, document the customer's relevant operational assumptions, and decide whether a separate customer-specific analysis is warranted. Keep any pilot review manual and read-only unless a later scoped phase explicitly changes the boundary.",
    "",
    "## Safety boundary",
    "",
    "- Public market/system-level only.",
    "- Not customer-specific savings.",
    "- Read-only decision support.",
    "- No automatic control, dispatch, activation.",
    "- No live control signals.",
    "- No asset integration.",
    ""
  ].join("\n");
}

function downloadPublicProofOfWorkReport() {
  const markdown = buildPublicProofOfWorkMarkdownReport();
  const blob = new Blob([markdown], {
    type: "text/markdown;charset=utf-8"
  });

  downloadBrowserBlob(blob, PUBLIC_PROOF_OF_WORK_REPORT_FILENAME);
}

function PublicBacktestSnapshotCard({
  snapshot
}: {
  snapshot: PublicBacktestSnapshotArea;
}) {
  return (
    <article className="public-backtest-card">
      <div className="public-backtest-card__header">
        <div>
          <span>{snapshot.area}</span>
          <strong>{formatNumber(snapshot.riskWindows)}</strong>
        </div>
        <p>Risk windows</p>
      </div>
      <dl className="public-backtest-card__metrics">
        <div>
          <dt>Joined hours</dt>
          <dd>{formatNumber(snapshot.joinedHours)}</dd>
        </div>
        <div>
          <dt>Skipped rows</dt>
          <dd>{formatNumber(snapshot.skippedRows)}</dd>
        </div>
        <div>
          <dt>Medium-risk hours</dt>
          <dd>{formatNumber(snapshot.mediumRiskHours)}</dd>
        </div>
        <div>
          <dt>High-risk hours</dt>
          <dd>{formatNumber(snapshot.highRiskHours)}</dd>
        </div>
        <div>
          <dt>Highest score</dt>
          <dd>{formatNumber(snapshot.highestRiskScore)}</dd>
        </div>
        <div>
          <dt>Negative price hours</dt>
          <dd>{formatNumber(snapshot.negativePriceHours)}</dd>
        </div>
        <div>
          <dt>Low price hours</dt>
          <dd>{formatNumber(snapshot.lowPriceHours)}</dd>
        </div>
        <div>
          <dt>Avg / max renewable share</dt>
          <dd>
            {snapshot.averageRenewableShare} / {snapshot.maxRenewableShare}
          </dd>
        </div>
      </dl>
    </article>
  );
}

function VerifiedPublicRiskWindowSnapshot() {
  return (
    <section
      className="public-risk-windows"
      aria-labelledby="public-risk-windows-title"
    >
      <div className="public-risk-windows__header">
        <div>
          <p className="eyebrow">Public surplus-risk proof-of-work</p>
          <h2 id="public-risk-windows-title">
            Verified public risk-window snapshot
          </h2>
          <p>
            Top public DK1/DK2 surplus-risk windows from the verified snapshot.
            This is market and system-level evidence for human review, not a
            customer savings calculation.
          </p>
        </div>
        <span className="status">Read-only snapshot</span>
      </div>

      <div className="table-wrap">
        <table className="risk-window-table">
          <thead>
            <tr>
              <th scope="col">Area</th>
              <th scope="col">Window</th>
              <th scope="col">Duration</th>
              <th scope="col">Score</th>
              <th scope="col">Level</th>
              <th scope="col">Low price hours</th>
              <th scope="col">Negative price hours</th>
              <th scope="col">Avg renewable share</th>
              <th scope="col">Main reasons</th>
              <th scope="col">Human review action</th>
            </tr>
          </thead>
          <tbody>
            {publicRiskWindowSnapshots.map((snapshot) => (
              <tr
                key={`${snapshot.area}-${snapshot.start}-${snapshot.end}`}
              >
                <td>
                  <strong>{snapshot.area}</strong>
                </td>
                <td>
                  <span className="risk-window-table__window">
                    {formatRiskWindowTimestamp(snapshot.start)}
                    <span>to</span>
                    {formatRiskWindowTimestamp(snapshot.end)}
                  </span>
                </td>
                <td>{snapshot.durationHours}h</td>
                <td>{formatNumber(snapshot.score)}</td>
                <td>
                  <span
                    className={`risk-score__level risk-score__level--${snapshot.level}`}
                  >
                    {formatRiskLabel(snapshot.level)}
                  </span>
                </td>
                <td>{formatNumber(snapshot.lowPriceHours)}</td>
                <td>{formatNumber(snapshot.negativePriceHours)}</td>
                <td>
                  <span className="risk-window-table__renewables">
                    {snapshot.averageRenewableShare}
                    <small>Max {snapshot.maxRenewableShare}</small>
                  </span>
                </td>
                <td>
                  <span className="risk-window-table__reasons">
                    {snapshot.reasons.map((reason) => (
                      <span key={reason}>
                        {publicRiskReasonLabels[reason] ?? reason}
                      </span>
                    ))}
                  </span>
                </td>
                <td className="risk-window-table__review">
                  Review as public evidence and document any decision-support
                  note manually.
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="public-risk-windows__limits">
        <p>Limitations</p>
        <ul className="plain-list">
          <li>Public market/system-level only.</li>
          <li>Not customer-specific savings.</li>
          <li>No customer load/asset/tariff data.</li>
          <li>Read-only decision support.</li>
          <li>No automatic control, dispatch, or activation.</li>
        </ul>
      </div>
    </section>
  );
}

function formatRiskWindowTimestamp(timestamp: string): string {
  const [date = "", time = ""] = timestamp.split("T");
  const [year = "", month = "", day = ""] = date.split("-");
  const hourMinute = time.slice(0, 5);

  if (!year || !month || !day || !hourMinute) {
    return timestamp;
  }

  return `${day}.${month}.${year} ${hourMinute}`;
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
        <li>Does not call EDS/DMI APIs.</li>
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
        <li>Does not call EDS/DMI APIs.</li>
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
        energy data tables, call EDS/DMI APIs, or control, dispatch, or
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

function downloadBrowserBlob(blob: Blob, filename: string) {
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

function downloadReportPdfBlob(blob: Blob, filename: string) {
  downloadBrowserBlob(blob, filename);
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
        Future DMI/weather forecast module. This screen does not show fake
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

function DecisionOverview({
  selectedArea,
  decisionSummaryState,
  onLoadDecisionSummary
}: {
  selectedArea: PriceArea;
  decisionSummaryState: DecisionSummaryRequestState;
  onLoadDecisionSummary: () => void;
}) {
  const isLoading = decisionSummaryState.status === "loading";
  const overviewItems = getDecisionSummaryKpis(decisionSummaryState);
  const sourceNotes =
    decisionSummaryState.status === "success"
      ? getDecisionSummarySourceNotes(decisionSummaryState.data)
      : [];

  return (
    <section className="decision-overview" aria-labelledby="decision-overview-title">
      <div className="decision-overview__header">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h2 id="decision-overview-title">Decision overview</h2>
          <p>
            Calm manual decision-support view for {selectedArea}. Values stay
            empty until a reviewer loads or calculates them.
          </p>
        </div>
      </div>
      <div className="decision-overview__actions" aria-label="Manual cockpit actions">
        <button
          className="load-button load-button--cockpit"
          type="button"
          onClick={onLoadDecisionSummary}
          disabled={isLoading}
        >
          {isLoading ? "Loading..." : "Load decision summary"}
        </button>
      </div>
      <div className="decision-overview__action-status" aria-live="polite">
        <span className={getActionStatusClass(decisionSummaryState)}>
          {getDecisionSummaryActionStatus(decisionSummaryState)}
        </span>
      </div>
      <div className="decision-overview__grid">
        {overviewItems.map((item) => (
          <article
            className={getDecisionOverviewItemClass(item)}
            key={item.label}
          >
            <span>{item.label}</span>
            <strong>{item.value}</strong>
            <p>{item.detail}</p>
          </article>
        ))}
      </div>
      {sourceNotes.length > 0 && (
        <div className="decision-overview__notes" aria-label="Data notes">
          <span>Data notes</span>
          <ul>
            {sourceNotes.map((note, index) => (
              <li key={`${index}-${note}`}>{note}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="decision-overview__boundary" aria-label="Cockpit safety boundary">
        <span>Safety boundary</span>
        <p>
          Read-only decision support. No automatic control, no dispatch, no
          activation. Human review remains required.
        </p>
      </div>
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
  const [decisionSummaryState, setDecisionSummaryState] =
    useState<DecisionSummaryRequestState>({
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
    setDecisionSummaryState({ status: "idle" });
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

  async function handleLoadDecisionSummary() {
    setDecisionSummaryState({ status: "loading" });
    try {
      const forecastRows = getForecastRowsForDecisionSummary(
        forecastPreviewState,
        selectedArea
      );
      const data = await fetchDashboardDecisionSummaryPreview(
        selectedArea,
        forecastRows
      );
      setDecisionSummaryState({ status: "success", data });
    } catch (error) {
      setDecisionSummaryState({
        status: "error",
        message: errorMessage(error)
      });
    }
  }

  async function handleLoadForecastPreview() {
    setForecastPreviewState({ status: "loading" });
    try {
      const result = await fetchForecastPreview(selectedArea);
      setForecastPreviewState({
        status: "success",
        data: result.data,
        rows: result.rows
      });
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
      description="Manual read-only spot price rows for the selected price area."
      endpointName="spot-prices"
      buttonLabel="Load spot price view"
      state={spotPricesState}
      columns={spotPriceColumns}
      onLoad={handleLoadSpotPrices}
      renderAfterTable={(data) => <SpotPriceTrendChart data={data} />}
    />
  );
  const powerBalanceCard = (
    <EnergyCard
      title="Power balance"
      description="Manual read-only power balance rows for the selected price area."
      endpointName="power-balance"
      buttonLabel="Load power balance view"
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
              description="Manual report summary, Markdown, PDF dry-run, and unaudited PDF download flows. No files are written by the frontend and no external data APIs are called."
            />
            <PublicBacktestSnapshot />
            <VerifiedPublicRiskWindowSnapshot />
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
              title="Operations cockpit"
              description="Executive and operations view for Danish electricity decision support. Values appear only after manual review actions; unavailable values remain clearly marked until calculated."
            />
            <DecisionOverview
              selectedArea={selectedArea}
              decisionSummaryState={decisionSummaryState}
              onLoadDecisionSummary={handleLoadDecisionSummary}
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
          <img
            className="sidebar__logo"
            src="/branding/no-predict-logo.png"
            alt=""
            aria-hidden="true"
          />
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
        <div className="sidebar__safety" aria-label="v0.1 safety boundary">
          <span>v0.1 boundary</span>
          <strong>Read-only decision support</strong>
          <p>
            No automatic control, dispatch, or activation. Human review
            required.
          </p>
        </div>
      </aside>

      <div className="dashboard">
        <header className="topbar">
          <div className="topbar__section">
            <p className="topbar__label">Current section</p>
            <h2>{activeNavigationItem.label}</h2>
          </div>
          <div className="topbar__meta">
            <div className="topbar__product">N&amp;O Predict</div>
            <div
              className="system-status"
              aria-label="System status: manual refresh mode"
            >
              <span className="system-status__dot" aria-hidden="true" />
              <span>Manual refresh mode</span>
            </div>
          </div>
        </header>

        <div className="dashboard__inner">
          <header className="dashboard__controls">
            <div className="safety-boundary" aria-label="Safety boundary">
              <div className="mode-indicator">
                <span>Decision support mode</span>
                <strong>Read-only · Human review required</strong>
              </div>
              <div className="safety-boundary__details">
                <span>Safety constraints:</span>
                <ul>
                  <li>No automatic control</li>
                  <li>No dispatch</li>
                  <li>No activation</li>
                  <li>Human review required</li>
                </ul>
              </div>
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
