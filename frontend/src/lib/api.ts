export const backendApiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type PriceArea = "DK1" | "DK2";

export type EnergyApiResponse<Row> = {
  table: string;
  price_area: PriceArea;
  row_count: number;
  rows: Row[];
};

export type CurrentRiskResponse = {
  price_area: PriceArea;
  timestamp_utc: string;
  risk_level: "low" | "medium" | "high";
  risk_score: number;
  confidence_score: number;
  reason_codes: string[];
  explanation: string;
  recommended_human_action: string;
  model_version: string;
  decision_support_only: boolean;
  metadata: {
    source_tables_used: string[];
    spot_price_row_found: boolean;
    power_balance_row_found: boolean;
  };
};

export type ForecastRiskLevel = "low" | "medium" | "high" | "unknown";

export type ForecastPreviewRow = {
  price_area: PriceArea;
  timestamp_utc: string;
  price_dkk_per_mwh: number | null;
  production_mw: number | null;
  consumption_mw: number | null;
  wind_onshore_mw: number | null;
  wind_offshore_mw: number | null;
  solar_mw: number | null;
  exchange_net_mw?: number | null;
};

export type ForecastPreviewRequest = {
  price_area: PriceArea;
  generated_at_utc: string;
  rows: ForecastPreviewRow[];
};

export type ForecastReasonCodeCount = {
  reason_code: string;
  count: number;
};

export type ForecastWindowSummary = {
  window_label: string;
  start_utc: string;
  end_utc: string;
  row_count: number;
  risk_level: ForecastRiskLevel;
  max_risk_score: number | null;
  average_risk_score: number | null;
  average_confidence_score: number;
  risk_level_counts: Record<string, number>;
  top_reason_codes: ForecastReasonCodeCount[];
  recommended_human_action: string;
  explanation: string;
  decision_support_only: boolean;
};

export type ForecastPreviewResponse = {
  price_area: PriceArea;
  generated_at_utc: string;
  model_version: string;
  decision_support_only: boolean;
  safety: string;
  windows: ForecastWindowSummary[];
};

export type EnergyFreshnessQueryPlan = {
  read_model?: string;
  part?: "spot_price" | "power_balance" | string;
  price_area?: PriceArea;
  table?: string;
  operation?: string;
  sql?: string;
  params?: Record<string, unknown>;
  expected_result_fields?: string[];
};

export type EnergyFreshnessPlans = {
  read_model?: string;
  price_area?: PriceArea;
  operation?: string;
  queries?: {
    spot_price?: EnergyFreshnessQueryPlan;
    power_balance?: EnergyFreshnessQueryPlan;
  };
};

export type SafetyBoundary = {
  read_only_decision_support?: boolean;
  no_automatic_control?: boolean;
  no_dispatch?: boolean;
  no_activation?: boolean;
  no_operational_energy_system_integration?: boolean;
  human_review_required?: boolean;
};

export type EnergyFreshnessReadResult = {
  price_area?: PriceArea;
  database_query_executed?: boolean;
  database_write_performed?: boolean;
  source_label?: string;
  earliest_timestamp?: string | null;
  latest_timestamp?: string | null;
  row_count?: number;
  warning?: string | null;
  safety_boundary?: SafetyBoundary;
};

export type EnergyFreshnessResponse = {
  price_area: PriceArea;
  dry_run: boolean;
  database_query_executed: boolean;
  database_write_performed: boolean;
  requires_database_url: boolean;
  freshness_plans?: EnergyFreshnessPlans;
  freshness_result?: {
    price_area?: PriceArea;
    database_query_executed?: boolean;
    database_write_performed?: boolean;
    spot_price_freshness?: EnergyFreshnessReadResult;
    power_balance_freshness?: EnergyFreshnessReadResult;
    warnings?: string[];
    safety_boundary?: SafetyBoundary;
  };
  spot_price_freshness_plan?: EnergyFreshnessQueryPlan;
  power_balance_freshness_plan?: EnergyFreshnessQueryPlan;
  spot_price_freshness?: EnergyFreshnessReadResult;
  power_balance_freshness?: EnergyFreshnessReadResult;
  warnings?: string[];
  safety_boundary?: SafetyBoundary;
};

export type SpotPriceRow = {
  id: number;
  price_area: PriceArea;
  timestamp_utc: string;
  price_eur_per_mwh: string | number | null;
  price_dkk_per_mwh: string | number | null;
  source: string;
  source_record_id: string;
  ingested_at_utc: string;
};

export type PowerBalanceRow = {
  id: number;
  price_area: PriceArea;
  timestamp_utc: string;
  production_mw: string | number | null;
  consumption_mw: string | number | null;
  wind_onshore_mw: string | number | null;
  wind_offshore_mw: string | number | null;
  solar_mw: string | number | null;
  exchange_net_mw: string | number | null;
  source: string;
  source_record_id: string;
  ingested_at_utc: string;
};

export type ReportCurrentRiskSummary = {
  status?: string;
  risk_level?: string;
  risk_score?: number | null;
  confidence_score?: number | null;
  reason_codes?: string[];
  recommended_human_action?: string;
  model_version?: string;
  decision_support_only?: boolean;
};

export type ReportForecastWindowSummary = {
  status?: string;
  model_version?: string;
  windows?: ForecastWindowSummary[];
  highest_risk_level?: string;
  highest_risk_window_label?: string | null;
  decision_support_only?: boolean;
};

export type ReportSummary = {
  title?: string;
  price_area?: PriceArea;
  generated_at_utc?: string;
  decision_support_only?: boolean;
  human_review_required?: boolean;
  current_risk_summary?: ReportCurrentRiskSummary;
  forecast_window_summary?: ReportForecastWindowSummary;
  key_findings?: string[];
  recommended_human_actions?: string[];
  safety_notes?: string[];
  limitations?: string[];
};

export type ReportSummaryPreviewResponse = {
  report_preview_generated: boolean;
  pdf_generated: boolean;
  file_written: boolean;
  database_query_executed: boolean;
  database_write_performed: boolean;
  requires_database_url: boolean;
  decision_support_only: boolean;
  report_summary: ReportSummary;
  recommendations: string[];
  explanation: string;
  safety_boundary: SafetyBoundary;
};

const READ_LIMIT = 5;

export async function fetchSpotPrices(
  priceArea: PriceArea
): Promise<EnergyApiResponse<SpotPriceRow>> {
  return fetchEnergyApi<SpotPriceRow>("/api/energy/spot-prices", priceArea);
}

export async function fetchPowerBalance(
  priceArea: PriceArea
): Promise<EnergyApiResponse<PowerBalanceRow>> {
  return fetchEnergyApi<PowerBalanceRow>(
    "/api/energy/power-balance",
    priceArea
  );
}

export async function fetchCurrentRisk(
  priceArea: PriceArea
): Promise<CurrentRiskResponse> {
  const url = new URL(
    `${backendApiBaseUrl.replace(/\/+$/, "")}/api/risk/current`
  );
  url.searchParams.set("price_area", priceArea);

  const response = await fetch(url);
  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getApiErrorMessage(body, response.status));
  }

  return body as CurrentRiskResponse;
}

export async function fetchForecastPreview(
  priceArea: PriceArea
): Promise<ForecastPreviewResponse> {
  const url = new URL(
    `${backendApiBaseUrl.replace(/\/+$/, "")}/api/forecast/preview`
  );
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(buildForecastPreviewRequest(priceArea))
  });
  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getApiErrorMessage(body, response.status));
  }

  return body as ForecastPreviewResponse;
}

export async function fetchEnergyFreshness(
  priceArea: PriceArea
): Promise<EnergyFreshnessResponse> {
  const url = new URL(
    `${backendApiBaseUrl.replace(/\/+$/, "")}/api/energy/freshness`
  );
  url.searchParams.set("price_area", priceArea);

  const response = await fetch(url);
  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getApiErrorMessage(body, response.status));
  }

  if (!isEnergyFreshnessResponse(body)) {
    throw new Error("Backend returned an unexpected freshness preview shape");
  }

  return body;
}

export async function fetchEnergyFreshnessRead(
  priceArea: PriceArea
): Promise<EnergyFreshnessResponse> {
  const url = new URL(
    `${backendApiBaseUrl.replace(/\/+$/, "")}/api/energy/freshness/read`
  );
  url.searchParams.set("price_area", priceArea);

  const response = await fetch(url);
  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getApiErrorMessage(body, response.status));
  }

  if (!isEnergyFreshnessResponse(body)) {
    throw new Error("Backend returned an unexpected freshness read shape");
  }

  return body;
}

export async function fetchReportSummaryPreview(): Promise<ReportSummaryPreviewResponse> {
  const url = new URL(
    `${backendApiBaseUrl.replace(/\/+$/, "")}/api/report/summary/preview`
  );
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({})
  });
  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getApiErrorMessage(body, response.status));
  }

  return body as ReportSummaryPreviewResponse;
}

async function fetchEnergyApi<Row>(
  path: string,
  priceArea: PriceArea
): Promise<EnergyApiResponse<Row>> {
  const url = new URL(`${backendApiBaseUrl.replace(/\/+$/, "")}${path}`);
  url.searchParams.set("price_area", priceArea);
  url.searchParams.set("limit", String(READ_LIMIT));

  const response = await fetch(url);
  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getApiErrorMessage(body, response.status));
  }

  return body as EnergyApiResponse<Row>;
}

function buildForecastPreviewRequest(
  priceArea: PriceArea
): ForecastPreviewRequest {
  const generatedAtUtc = "2026-01-01T00:00:00+00:00";

  return {
    price_area: priceArea,
    generated_at_utc: generatedAtUtc,
    rows: [
      {
        price_area: priceArea,
        timestamp_utc: "2026-01-01T01:00:00+00:00",
        price_dkk_per_mwh: 100,
        production_mw: 5000,
        consumption_mw: 4500,
        wind_onshore_mw: 2000,
        wind_offshore_mw: 1000,
        solar_mw: 100,
        exchange_net_mw: 50
      },
      {
        price_area: priceArea,
        timestamp_utc: "2026-01-02T01:00:00+00:00",
        price_dkk_per_mwh: -25,
        production_mw: 5000,
        consumption_mw: 4200,
        wind_onshore_mw: 2500,
        wind_offshore_mw: 1500,
        solar_mw: 400,
        exchange_net_mw: -100
      },
      {
        price_area: priceArea,
        timestamp_utc: "2026-01-03T01:00:00+00:00",
        price_dkk_per_mwh: 320,
        production_mw: 5000,
        consumption_mw: 4700,
        wind_onshore_mw: 1200,
        wind_offshore_mw: 800,
        solar_mw: 150,
        exchange_net_mw: 20
      }
    ]
  };
}

function isEnergyFreshnessResponse(
  value: unknown
): value is EnergyFreshnessResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const candidate = value as Partial<EnergyFreshnessResponse>;

  return (
    isPriceArea(candidate.price_area) &&
    typeof candidate.dry_run === "boolean" &&
    typeof candidate.database_query_executed === "boolean" &&
    typeof candidate.database_write_performed === "boolean" &&
    typeof candidate.requires_database_url === "boolean" &&
    isOptionalRecord(candidate.freshness_plans) &&
    isOptionalRecord(candidate.freshness_result) &&
    isOptionalStringArray(candidate.warnings) &&
    isOptionalRecord(candidate.safety_boundary) &&
    isOptionalRecord(candidate.spot_price_freshness_plan) &&
    isOptionalRecord(candidate.power_balance_freshness_plan) &&
    isOptionalRecord(candidate.spot_price_freshness) &&
    isOptionalRecord(candidate.power_balance_freshness) &&
    (isRecord(candidate.freshness_plans) ||
      isRecord(candidate.spot_price_freshness) ||
      isRecord(candidate.power_balance_freshness))
  );
}

function isPriceArea(value: unknown): value is PriceArea {
  return value === "DK1" || value === "DK2";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isOptionalRecord(value: unknown): value is Record<string, unknown> {
  return value === undefined || isRecord(value);
}

function isOptionalStringArray(value: unknown): value is string[] {
  return (
    value === undefined ||
    (Array.isArray(value) && value.every((item) => typeof item === "string"))
  );
}

function getApiErrorMessage(body: unknown, status: number): string {
  if (
    body &&
    typeof body === "object" &&
    "detail" in body
  ) {
    if (typeof body.detail === "string") {
      return body.detail;
    }

    if (
      status === 503 &&
      isRecord(body.detail) &&
      body.detail.requires_database_url === true
    ) {
      return "DB-backed freshness read requires backend DATABASE_URL.";
    }

    if (
      isRecord(body.detail) &&
      "warning" in body.detail &&
      typeof body.detail.warning === "string"
    ) {
      return body.detail.warning;
    }
  }

  return `Backend request failed with status ${status}`;
}
