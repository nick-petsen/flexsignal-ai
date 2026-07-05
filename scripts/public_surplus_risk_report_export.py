#!/usr/bin/env python3
"""Export the verified public DK1/DK2 surplus-risk report v1."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


DEFAULT_REPORT_FORMAT = "markdown"
DEFAULT_REPORT_OUTPUT_PATH = ""
DEFAULT_REPORT_DRY_RUN = "true"

TITLE = "Public DK1/DK2 surplus-risk proof-of-work"
PERIOD = "2026-01-01 to now"
SOURCE = (
    "Energi Data Service DayAheadPrices + "
    "ProductionConsumptionSettlement"
)

SAFETY_BOUNDARY = (
    "This report is read-only decision support. It uses public "
    "market/system-level data only, is not customer-specific savings, and "
    "performs no automatic control, dispatch, activation, no live control "
    "signals, and no asset integration."
)


class PublicSurplusRiskReportExportError(RuntimeError):
    """Expected safe-fail error for report export configuration."""


@dataclass(frozen=True)
class ReportExportConfig:
    report_format: str
    output_path: str
    dry_run: bool


@dataclass(frozen=True)
class AreaMetric:
    area: str
    joined_hours: int
    skipped_rows: int
    medium_risk_hours: int
    high_risk_hours: int
    risk_windows: int
    highest_risk_score: int
    negative_price_hours: int
    low_price_hours: int
    average_renewable_share: str


@dataclass(frozen=True)
class RiskWindowSnapshot:
    area: str
    start_timestamp_utc: str
    end_timestamp_utc: str
    duration_hours: int
    highest_risk_score: int
    risk_level: str
    negative_price_hours: int
    low_price_hours: int
    average_renewable_share: str
    max_renewable_share: str
    reasons: tuple[str, ...]
    human_review_action: str


VERIFIED_AREA_METRICS: tuple[AreaMetric, ...] = (
    AreaMetric(
        area="DK1",
        joined_hours=4208,
        skipped_rows=233,
        medium_risk_hours=1663,
        high_risk_hours=174,
        risk_windows=129,
        highest_risk_score=100,
        negative_price_hours=132,
        low_price_hours=479,
        average_renewable_share="68.8%",
    ),
    AreaMetric(
        area="DK2",
        joined_hours=4208,
        skipped_rows=233,
        medium_risk_hours=288,
        high_risk_hours=2,
        risk_windows=72,
        highest_risk_score=85,
        negative_price_hours=78,
        low_price_hours=491,
        average_renewable_share="38.2%",
    ),
)

VERIFIED_TOP_RISK_WINDOWS: tuple[RiskWindowSnapshot, ...] = (
    RiskWindowSnapshot(
        area="DK1",
        start_timestamp_utc="2026-04-04T21:00:00",
        end_timestamp_utc="2026-04-06T23:00:00",
        duration_hours=51,
        highest_risk_score=100,
        risk_level="high",
        negative_price_hours=20,
        low_price_hours=39,
        average_renewable_share="98.6%",
        max_renewable_share="163.3%",
        reasons=(
            "low_price",
            "high_renewable_share",
            "renewable_generation_above_consumption",
            "negative_price",
        ),
        human_review_action=(
            "Review as public evidence and document any decision-support note "
            "manually."
        ),
    ),
    RiskWindowSnapshot(
        area="DK1",
        start_timestamp_utc="2026-04-24T06:00:00",
        end_timestamp_utc="2026-04-25T22:00:00",
        duration_hours=41,
        highest_risk_score=100,
        risk_level="high",
        negative_price_hours=8,
        low_price_hours=18,
        average_renewable_share="117.3%",
        max_renewable_share="192.2%",
        reasons=(
            "high_renewable_share",
            "renewable_generation_above_consumption",
            "low_price",
            "negative_price",
        ),
        human_review_action=(
            "Review as public evidence and document any decision-support note "
            "manually."
        ),
    ),
    RiskWindowSnapshot(
        area="DK1",
        start_timestamp_utc="2026-05-29T06:00:00",
        end_timestamp_utc="2026-05-29T16:00:00",
        duration_hours=11,
        highest_risk_score=100,
        risk_level="high",
        negative_price_hours=1,
        low_price_hours=6,
        average_renewable_share="108.6%",
        max_renewable_share="136.4%",
        reasons=(
            "high_renewable_share",
            "renewable_generation_above_consumption",
            "low_price",
            "negative_price",
        ),
        human_review_action=(
            "Review as public evidence and document any decision-support note "
            "manually."
        ),
    ),
    RiskWindowSnapshot(
        area="DK1",
        start_timestamp_utc="2026-06-13T02:00:00",
        end_timestamp_utc="2026-06-15T18:00:00",
        duration_hours=65,
        highest_risk_score=95,
        risk_level="high",
        negative_price_hours=14,
        low_price_hours=33,
        average_renewable_share="110.2%",
        max_renewable_share="171.3%",
        reasons=(
            "high_renewable_share",
            "renewable_generation_above_consumption",
            "low_price",
            "negative_price",
        ),
        human_review_action=(
            "Review as public evidence and document any decision-support note "
            "manually."
        ),
    ),
    RiskWindowSnapshot(
        area="DK1",
        start_timestamp_utc="2026-05-26T10:00:00",
        end_timestamp_utc="2026-05-28T01:00:00",
        duration_hours=40,
        highest_risk_score=95,
        risk_level="high",
        negative_price_hours=10,
        low_price_hours=12,
        average_renewable_share="113.2%",
        max_renewable_share="162.7%",
        reasons=(
            "high_renewable_share",
            "renewable_generation_above_consumption",
            "low_price",
            "negative_price",
        ),
        human_review_action=(
            "Review as public evidence and document any decision-support note "
            "manually."
        ),
    ),
    RiskWindowSnapshot(
        area="DK2",
        start_timestamp_utc="2026-04-24T21:00:00",
        end_timestamp_utc="2026-04-25T06:00:00",
        duration_hours=10,
        highest_risk_score=85,
        risk_level="high",
        negative_price_hours=0,
        low_price_hours=3,
        average_renewable_share="98.0%",
        max_renewable_share="108.6%",
        reasons=(
            "high_renewable_share",
            "renewable_generation_above_consumption",
            "low_price",
        ),
        human_review_action=(
            "Review as public evidence and document any decision-support note "
            "manually."
        ),
    ),
    RiskWindowSnapshot(
        area="DK2",
        start_timestamp_utc="2026-06-14T20:00:00",
        end_timestamp_utc="2026-06-15T04:00:00",
        duration_hours=9,
        highest_risk_score=65,
        risk_level="medium",
        negative_price_hours=0,
        low_price_hours=0,
        average_renewable_share="92.2%",
        max_renewable_share="100.7%",
        reasons=(
            "high_renewable_share",
            "renewable_generation_above_consumption",
        ),
        human_review_action=(
            "Review as public evidence and document any decision-support note "
            "manually."
        ),
    ),
    RiskWindowSnapshot(
        area="DK2",
        start_timestamp_utc="2026-01-01T17:00:00",
        end_timestamp_utc="2026-01-02T05:00:00",
        duration_hours=13,
        highest_risk_score=60,
        risk_level="medium",
        negative_price_hours=0,
        low_price_hours=13,
        average_renewable_share="77.1%",
        max_renewable_share="85.4%",
        reasons=(
            "low_price",
            "medium_renewable_share",
            "high_renewable_share",
        ),
        human_review_action=(
            "Review as public evidence and document any decision-support note "
            "manually."
        ),
    ),
    RiskWindowSnapshot(
        area="DK2",
        start_timestamp_utc="2026-04-03T21:00:00",
        end_timestamp_utc="2026-04-04T08:00:00",
        duration_hours=12,
        highest_risk_score=60,
        risk_level="medium",
        negative_price_hours=0,
        low_price_hours=10,
        average_renewable_share="90.2%",
        max_renewable_share="97.3%",
        reasons=("high_renewable_share", "low_price"),
        human_review_action=(
            "Review as public evidence and document any decision-support note "
            "manually."
        ),
    ),
    RiskWindowSnapshot(
        area="DK2",
        start_timestamp_utc="2026-03-25T20:00:00",
        end_timestamp_utc="2026-03-26T05:00:00",
        duration_hours=10,
        highest_risk_score=60,
        risk_level="medium",
        negative_price_hours=0,
        low_price_hours=8,
        average_renewable_share="84.8%",
        max_renewable_share="90.8%",
        reasons=("high_renewable_share", "low_price"),
        human_review_action=(
            "Review as public evidence and document any decision-support note "
            "manually."
        ),
    ),
)


def load_config(env: Mapping[str, str] | None = None) -> ReportExportConfig:
    safe_env = os.environ if env is None else env
    report_format = safe_env.get(
        "BACKTEST_REPORT_FORMAT",
        DEFAULT_REPORT_FORMAT,
    ).strip().lower()
    output_path = safe_env.get(
        "BACKTEST_REPORT_OUTPUT_PATH",
        DEFAULT_REPORT_OUTPUT_PATH,
    ).strip()
    dry_run = _parse_bool(
        safe_env.get("BACKTEST_REPORT_DRY_RUN", DEFAULT_REPORT_DRY_RUN),
        "BACKTEST_REPORT_DRY_RUN",
    )

    if report_format != "markdown":
        raise PublicSurplusRiskReportExportError(
            "BACKTEST_REPORT_FORMAT must be markdown"
        )

    return ReportExportConfig(
        report_format=report_format,
        output_path=output_path,
        dry_run=dry_run,
    )


def render_markdown_report(
    area_metrics: Sequence[AreaMetric] = VERIFIED_AREA_METRICS,
    risk_windows: Sequence[RiskWindowSnapshot] = VERIFIED_TOP_RISK_WINDOWS,
) -> str:
    lines: list[str] = [
        f"# {TITLE}",
        "",
        "## Report metadata",
        "",
        f"- Period: `{PERIOD}`",
        f"- Source: {SOURCE}",
        "- Scope: public market/system-level only",
        "- Decision boundary: read-only decision support",
        "",
        "## DK1/DK2 summary",
        "",
        (
            "| Area | Joined hours | Skipped rows | Medium-risk hours | "
            "High-risk hours | Risk windows | Highest risk score | "
            "Negative price hours | Low price hours | Avg renewable share |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for metric in area_metrics:
        lines.append(
            "| "
            f"{metric.area} | "
            f"{_format_int(metric.joined_hours)} | "
            f"{_format_int(metric.skipped_rows)} | "
            f"{_format_int(metric.medium_risk_hours)} | "
            f"{_format_int(metric.high_risk_hours)} | "
            f"{_format_int(metric.risk_windows)} | "
            f"{_format_int(metric.highest_risk_score)} | "
            f"{_format_int(metric.negative_price_hours)} | "
            f"{_format_int(metric.low_price_hours)} | "
            f"{metric.average_renewable_share} |"
        )

    lines.extend(
        [
            "",
            "## Top risk windows",
            "",
            (
                "| Area | Start UTC | End UTC | Duration | Score | Level | "
                "Low price hours | Negative price hours | Avg renewable share | "
                "Max renewable share | Main reasons | Human review action |"
            ),
            (
                "| --- | --- | --- | ---: | ---: | --- | ---: | ---: | "
                "---: | ---: | --- | --- |"
            ),
        ]
    )
    for window in risk_windows:
        lines.append(
            "| "
            f"{window.area} | "
            f"{window.start_timestamp_utc} | "
            f"{window.end_timestamp_utc} | "
            f"{window.duration_hours}h | "
            f"{window.highest_risk_score} | "
            f"{window.risk_level} | "
            f"{_format_int(window.low_price_hours)} | "
            f"{_format_int(window.negative_price_hours)} | "
            f"{window.average_renewable_share} | "
            f"{window.max_renewable_share} | "
            f"{', '.join(window.reasons)} | "
            f"{window.human_review_action} |"
        )

    lines.extend(
        [
            "",
            "## Commercial interpretation",
            "",
            (
                "The verified public v1 backtest shows that deterministic "
                "rules can identify historical DK1/DK2 surplus-risk windows "
                "using public market price, consumption, and renewable "
                "production context. The result is evidence for customer "
                "pilot discussion and human review, not a customer value "
                "calculation."
            ),
            "",
            "## Limitations",
            "",
            "- Public market/system-level only.",
            "- Not customer-specific savings.",
            (
                "- Customer-specific value requires customer load, asset, "
                "tariff, and operational data."
            ),
            "- No customer load, asset, tariff, or operational data is used.",
            "- Not production readiness.",
            "- No trading, dispatch, activation, or control workflow.",
            "",
            "## Next customer pilot step",
            "",
            (
                "Run a read-only pilot with customer load, asset, tariff, "
                "and operational data, then compare the public signal against "
                "customer-specific operational reality under human review."
            ),
            "",
            "## Safety boundary",
            "",
            SAFETY_BOUNDARY,
            "",
        ]
    )

    return "\n".join(lines)


def export_report(
    config: ReportExportConfig,
    *,
    stdout: object | None = None,
) -> dict[str, object]:
    report = render_markdown_report()
    if not config.output_path:
        print(report, file=sys.stdout if stdout is None else stdout)
        return {
            "report_format": config.report_format,
            "output_path": "",
            "dry_run": config.dry_run,
            "file_written": False,
            "database_write_performed": False,
        }

    path = Path(config.output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return {
        "report_format": config.report_format,
        "output_path": str(path),
        "dry_run": config.dry_run,
        "file_written": True,
        "database_write_performed": False,
    }


def main() -> int:
    try:
        config = load_config()
        result = export_report(config)
    except PublicSurplusRiskReportExportError as exc:
        print(f"Public surplus-risk report export failed: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(
            f"Public surplus-risk report export failed: {exc}",
            file=sys.stderr,
        )
        return 1

    if result["file_written"]:
        print(f"Report written: {result['output_path']}")
    return 0


def _parse_bool(raw_value: str | None, env_name: str) -> bool:
    normalized = (raw_value or "").strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise PublicSurplusRiskReportExportError(
        f"{env_name} must be true or false"
    )


def _format_int(value: int) -> str:
    return f"{value:,}"


if __name__ == "__main__":
    raise SystemExit(main())
