import snapshotArtifact from "../data/public-surplus-risk-backtest-snapshot.json";
import type { PriceArea } from "./api";

type RiskLevel = "medium" | "high";

type PublicSnapshotSummaryMetric = {
  joined_hours: number;
  skipped_rows: number;
  medium_risk_hours: number;
  high_risk_hours: number;
  risk_windows: number;
  highest_risk_score: number;
  negative_price_hours: number;
  low_price_hours: number;
  average_renewable_share_percent: number;
  max_renewable_share_percent: number;
};

type PublicSnapshotRiskWindow = {
  start: string;
  end: string;
  duration_hours: number;
  score: number;
  level: RiskLevel;
  low_price_hours: number;
  negative_price_hours: number;
  average_renewable_share_percent: number;
  max_renewable_share_percent: number;
  reasons: string[];
};

export type PublicSurplusRiskBacktestSnapshot = {
  schema_version: "public_surplus_risk_snapshot.v1";
  title: string;
  period_start: string;
  period_end_label: string;
  source: string;
  scope: string;
  decision_boundary: string;
  dry_run: boolean;
  file_written: boolean;
  not_customer_specific_savings: boolean;
  no_automatic_control: boolean;
  no_dispatch: boolean;
  no_activation: boolean;
  no_live_control_signals: boolean;
  no_asset_integration: boolean;
  database_write_performed: boolean;
  customer_specific_savings_calculated: boolean;
  summary_metrics: Record<PriceArea, PublicSnapshotSummaryMetric>;
  top_risk_windows: Record<PriceArea, PublicSnapshotRiskWindow[]>;
  reason_labels: Record<string, string>;
  human_review_action: string;
  commercial_interpretation: string;
  pilot_next_step: string;
  important_boundaries: string[];
};

export type PublicBacktestSnapshotArea = {
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

export type PublicRiskWindowSnapshot = {
  area: PriceArea;
  start: string;
  end: string;
  durationHours: number;
  score: number;
  level: RiskLevel;
  negativePriceHours: number;
  lowPriceHours: number;
  averageRenewableShare: string;
  maxRenewableShare: string;
  reasons: string[];
};

const priceAreas: PriceArea[] = ["DK1", "DK2"];

export const publicBacktestSnapshot =
  snapshotArtifact as PublicSurplusRiskBacktestSnapshot;

export const publicBacktestPeriod = `${publicBacktestSnapshot.period_start} to ${publicBacktestSnapshot.period_end_label}`;

export const publicRiskReasonLabels = publicBacktestSnapshot.reason_labels;

export const publicBacktestSnapshotAreas: PublicBacktestSnapshotArea[] =
  priceAreas.map((area) => {
    const metric = publicBacktestSnapshot.summary_metrics[area];

    return {
      area,
      joinedHours: metric.joined_hours,
      skippedRows: metric.skipped_rows,
      mediumRiskHours: metric.medium_risk_hours,
      highRiskHours: metric.high_risk_hours,
      riskWindows: metric.risk_windows,
      highestRiskScore: metric.highest_risk_score,
      negativePriceHours: metric.negative_price_hours,
      lowPriceHours: metric.low_price_hours,
      averageRenewableShare: formatSnapshotPercent(
        metric.average_renewable_share_percent,
      ),
      maxRenewableShare: formatSnapshotPercent(
        metric.max_renewable_share_percent,
      ),
    };
  });

export const publicRiskWindowSnapshots: PublicRiskWindowSnapshot[] =
  priceAreas.flatMap((area) =>
    publicBacktestSnapshot.top_risk_windows[area].map((window) => ({
      area,
      start: window.start,
      end: window.end,
      durationHours: window.duration_hours,
      score: window.score,
      level: window.level,
      negativePriceHours: window.negative_price_hours,
      lowPriceHours: window.low_price_hours,
      averageRenewableShare: formatSnapshotPercent(
        window.average_renewable_share_percent,
      ),
      maxRenewableShare: formatSnapshotPercent(
        window.max_renewable_share_percent,
      ),
      reasons: window.reasons,
    })),
  );

function formatSnapshotPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}
