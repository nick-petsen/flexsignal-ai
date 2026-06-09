export const backendApiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type PriceArea = "DK1" | "DK2";

export type EnergyApiResponse<Row> = {
  table: string;
  price_area: PriceArea;
  row_count: number;
  rows: Row[];
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

function getApiErrorMessage(body: unknown, status: number): string {
  if (
    body &&
    typeof body === "object" &&
    "detail" in body &&
    typeof body.detail === "string"
  ) {
    return body.detail;
  }

  return `Backend request failed with status ${status}`;
}
