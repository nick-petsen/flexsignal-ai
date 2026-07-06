#!/usr/bin/env python3
"""Export the canonical public DK1/DK2 surplus-risk snapshot artifact v1."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_PATH = (
    "frontend/src/data/public-surplus-risk-backtest-snapshot.json"
)
DEFAULT_DRY_RUN = "true"
DEFAULT_PRINT = "false"
DEFAULT_WRITE = "false"
SCHEMA_VERSION = "public_surplus_risk_snapshot.v1"
REFERENCE_PRICE_EUR_PER_MWH = 25.0
PRICE_CONTEXT_STATUS_AVAILABLE = "available"
PRICE_CONTEXT_STATUS_NOT_AVAILABLE = "not_available"
PRICE_CONTEXT_UNAVAILABLE_NOTE = (
    "Public DayAheadPrices rows were unavailable or insufficient for this "
    "window."
)
AVAILABLE_PRICE_CONTEXT_NOTE = (
    "Public market/system-level signal only: max(0, public low-price "
    "threshold 25 EUR/MWh - average window DayAheadPrices EUR/MWh). Customer "
    "load, flexibility, tariff, and constraints are excluded."
)
# Verified from public DayAheadPrices rows aggregated to hourly UTC prices for
# the committed top risk-window boundaries.
VERIFIED_PUBLIC_PRICE_CONTEXT: dict[tuple[str, str, str], dict[str, float]] = {
    (
        "DK1",
        "2026-04-04T21:00:00",
        "2026-04-06T23:00:00",
    ): {
        "min_price_eur_per_mwh": -25.4575,
        "average_price_eur_per_mwh": 16.656225,
        "max_price_eur_per_mwh": 115.707498,
        "opportunity_signal_eur_per_mwh": 8.343775,
    },
    (
        "DK1",
        "2026-04-24T06:00:00",
        "2026-04-25T22:00:00",
    ): {
        "min_price_eur_per_mwh": -31.2775,
        "average_price_eur_per_mwh": 43.215732,
        "max_price_eur_per_mwh": 131.535,
        "opportunity_signal_eur_per_mwh": 0.0,
    },
    (
        "DK1",
        "2026-05-29T06:00:00",
        "2026-05-29T16:00:00",
    ): {
        "min_price_eur_per_mwh": -0.005,
        "average_price_eur_per_mwh": 44.875682,
        "max_price_eur_per_mwh": 133.722502,
        "opportunity_signal_eur_per_mwh": 0.0,
    },
    (
        "DK1",
        "2026-06-13T02:00:00",
        "2026-06-15T18:00:00",
    ): {
        "min_price_eur_per_mwh": -28.95,
        "average_price_eur_per_mwh": 31.859961,
        "max_price_eur_per_mwh": 148.744995,
        "opportunity_signal_eur_per_mwh": 0.0,
    },
    (
        "DK1",
        "2026-05-26T10:00:00",
        "2026-05-28T01:00:00",
    ): {
        "min_price_eur_per_mwh": -1.3825,
        "average_price_eur_per_mwh": 77.876813,
        "max_price_eur_per_mwh": 148.340004,
        "opportunity_signal_eur_per_mwh": 0.0,
    },
    (
        "DK2",
        "2026-04-24T21:00:00",
        "2026-04-25T06:00:00",
    ): {
        "min_price_eur_per_mwh": 8.07,
        "average_price_eur_per_mwh": 43.43525,
        "max_price_eur_per_mwh": 104.827501,
        "opportunity_signal_eur_per_mwh": 0.0,
    },
    (
        "DK2",
        "2026-06-14T20:00:00",
        "2026-06-15T04:00:00",
    ): {
        "min_price_eur_per_mwh": 25.5475,
        "average_price_eur_per_mwh": 40.335833,
        "max_price_eur_per_mwh": 78.415,
        "opportunity_signal_eur_per_mwh": 0.0,
    },
    (
        "DK2",
        "2026-01-01T17:00:00",
        "2026-01-02T05:00:00",
    ): {
        "min_price_eur_per_mwh": 6.685,
        "average_price_eur_per_mwh": 14.893846,
        "max_price_eur_per_mwh": 24.9525,
        "opportunity_signal_eur_per_mwh": 10.106154,
    },
    (
        "DK2",
        "2026-04-03T21:00:00",
        "2026-04-04T08:00:00",
    ): {
        "min_price_eur_per_mwh": 3.21,
        "average_price_eur_per_mwh": 17.323125,
        "max_price_eur_per_mwh": 49.612501,
        "opportunity_signal_eur_per_mwh": 7.676875,
    },
    (
        "DK2",
        "2026-03-25T20:00:00",
        "2026-03-26T05:00:00",
    ): {
        "min_price_eur_per_mwh": 14.035,
        "average_price_eur_per_mwh": 22.125,
        "max_price_eur_per_mwh": 63.624999,
        "opportunity_signal_eur_per_mwh": 2.875,
    },
}


class PublicSurplusRiskSnapshotExportError(RuntimeError):
    """Expected safe-fail error for snapshot export configuration."""


@dataclass(frozen=True)
class SnapshotExportConfig:
    output_path: str
    dry_run: bool
    print_snapshot: bool
    write: bool


def load_config(env: Mapping[str, str] | None = None) -> SnapshotExportConfig:
    safe_env = os.environ if env is None else env
    return SnapshotExportConfig(
        output_path=safe_env.get(
            "PUBLIC_SURPLUS_RISK_SNAPSHOT_OUTPUT_PATH",
            DEFAULT_OUTPUT_PATH,
        ).strip()
        or DEFAULT_OUTPUT_PATH,
        dry_run=_parse_bool(
            safe_env.get("PUBLIC_SURPLUS_RISK_SNAPSHOT_DRY_RUN", DEFAULT_DRY_RUN),
            "PUBLIC_SURPLUS_RISK_SNAPSHOT_DRY_RUN",
        ),
        print_snapshot=_parse_bool(
            safe_env.get("PUBLIC_SURPLUS_RISK_SNAPSHOT_PRINT", DEFAULT_PRINT),
            "PUBLIC_SURPLUS_RISK_SNAPSHOT_PRINT",
        ),
        write=_parse_bool(
            safe_env.get("PUBLIC_SURPLUS_RISK_SNAPSHOT_WRITE", DEFAULT_WRITE),
            "PUBLIC_SURPLUS_RISK_SNAPSHOT_WRITE",
        ),
    )


def build_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "title": "Public DK1/DK2 surplus-risk proof-of-work",
        "period_start": "2026-01-01",
        "period_end_label": "now",
        "source": (
            "Energi Data Service DayAheadPrices + "
            "ProductionConsumptionSettlement"
        ),
        "scope": "public market/system-level only",
        "decision_boundary": "read-only decision support",
        "dry_run": True,
        "file_written": False,
        "not_customer_specific_savings": True,
        "no_automatic_control": True,
        "no_dispatch": True,
        "no_activation": True,
        "no_live_control_signals": True,
        "no_asset_integration": True,
        "database_write_performed": False,
        "customer_specific_savings_calculated": False,
        "summary_metrics": {
            "DK1": {
                "joined_hours": 4208,
                "skipped_rows": 233,
                "medium_risk_hours": 1663,
                "high_risk_hours": 174,
                "risk_windows": 129,
                "highest_risk_score": 100,
                "negative_price_hours": 132,
                "low_price_hours": 479,
                "average_renewable_share_percent": 68.8,
                "max_renewable_share_percent": 192.2,
            },
            "DK2": {
                "joined_hours": 4208,
                "skipped_rows": 233,
                "medium_risk_hours": 288,
                "high_risk_hours": 2,
                "risk_windows": 72,
                "highest_risk_score": 85,
                "negative_price_hours": 78,
                "low_price_hours": 491,
                "average_renewable_share_percent": 38.2,
                "max_renewable_share_percent": 108.6,
            },
        },
        "top_risk_windows": {
            "DK1": [
                {
                    "start": "2026-04-04T21:00:00",
                    "end": "2026-04-06T23:00:00",
                    "duration_hours": 51,
                    "score": 100,
                    "level": "high",
                    "low_price_hours": 39,
                    "negative_price_hours": 20,
                    "average_renewable_share_percent": 98.6,
                    "max_renewable_share_percent": 163.3,
                    "reasons": [
                        "low_price",
                        "high_renewable_share",
                        "renewable_generation_above_consumption",
                        "negative_price",
                    ],
                },
                {
                    "start": "2026-04-24T06:00:00",
                    "end": "2026-04-25T22:00:00",
                    "duration_hours": 41,
                    "score": 100,
                    "level": "high",
                    "low_price_hours": 18,
                    "negative_price_hours": 8,
                    "average_renewable_share_percent": 117.3,
                    "max_renewable_share_percent": 192.2,
                    "reasons": [
                        "high_renewable_share",
                        "renewable_generation_above_consumption",
                        "low_price",
                        "negative_price",
                    ],
                },
                {
                    "start": "2026-05-29T06:00:00",
                    "end": "2026-05-29T16:00:00",
                    "duration_hours": 11,
                    "score": 100,
                    "level": "high",
                    "low_price_hours": 6,
                    "negative_price_hours": 1,
                    "average_renewable_share_percent": 108.6,
                    "max_renewable_share_percent": 136.4,
                    "reasons": [
                        "high_renewable_share",
                        "renewable_generation_above_consumption",
                        "low_price",
                        "negative_price",
                    ],
                },
                {
                    "start": "2026-06-13T02:00:00",
                    "end": "2026-06-15T18:00:00",
                    "duration_hours": 65,
                    "score": 95,
                    "level": "high",
                    "low_price_hours": 33,
                    "negative_price_hours": 14,
                    "average_renewable_share_percent": 110.2,
                    "max_renewable_share_percent": 171.3,
                    "reasons": [
                        "high_renewable_share",
                        "renewable_generation_above_consumption",
                        "low_price",
                        "negative_price",
                    ],
                },
                {
                    "start": "2026-05-26T10:00:00",
                    "end": "2026-05-28T01:00:00",
                    "duration_hours": 40,
                    "score": 95,
                    "level": "high",
                    "low_price_hours": 12,
                    "negative_price_hours": 10,
                    "average_renewable_share_percent": 113.2,
                    "max_renewable_share_percent": 162.7,
                    "reasons": [
                        "high_renewable_share",
                        "renewable_generation_above_consumption",
                        "low_price",
                        "negative_price",
                    ],
                },
            ],
            "DK2": [
                {
                    "start": "2026-04-24T21:00:00",
                    "end": "2026-04-25T06:00:00",
                    "duration_hours": 10,
                    "score": 85,
                    "level": "high",
                    "low_price_hours": 3,
                    "negative_price_hours": 0,
                    "average_renewable_share_percent": 98.0,
                    "max_renewable_share_percent": 108.6,
                    "reasons": [
                        "high_renewable_share",
                        "renewable_generation_above_consumption",
                        "low_price",
                    ],
                },
                {
                    "start": "2026-06-14T20:00:00",
                    "end": "2026-06-15T04:00:00",
                    "duration_hours": 9,
                    "score": 65,
                    "level": "medium",
                    "low_price_hours": 0,
                    "negative_price_hours": 0,
                    "average_renewable_share_percent": 92.2,
                    "max_renewable_share_percent": 100.7,
                    "reasons": [
                        "high_renewable_share",
                        "renewable_generation_above_consumption",
                    ],
                },
                {
                    "start": "2026-01-01T17:00:00",
                    "end": "2026-01-02T05:00:00",
                    "duration_hours": 13,
                    "score": 60,
                    "level": "medium",
                    "low_price_hours": 13,
                    "negative_price_hours": 0,
                    "average_renewable_share_percent": 77.1,
                    "max_renewable_share_percent": 85.4,
                    "reasons": [
                        "low_price",
                        "medium_renewable_share",
                        "high_renewable_share",
                    ],
                },
                {
                    "start": "2026-04-03T21:00:00",
                    "end": "2026-04-04T08:00:00",
                    "duration_hours": 12,
                    "score": 60,
                    "level": "medium",
                    "low_price_hours": 10,
                    "negative_price_hours": 0,
                    "average_renewable_share_percent": 90.2,
                    "max_renewable_share_percent": 97.3,
                    "reasons": ["high_renewable_share", "low_price"],
                },
                {
                    "start": "2026-03-25T20:00:00",
                    "end": "2026-03-26T05:00:00",
                    "duration_hours": 10,
                    "score": 60,
                    "level": "medium",
                    "low_price_hours": 8,
                    "negative_price_hours": 0,
                    "average_renewable_share_percent": 84.8,
                    "max_renewable_share_percent": 90.8,
                    "reasons": ["high_renewable_share", "low_price"],
                },
            ],
        },
        "reason_labels": {
            "high_renewable_share": "High renewable share",
            "low_price": "Low price hours",
            "medium_renewable_share": "Medium renewable share",
            "negative_price": "Negative price hours",
            "renewable_generation_above_consumption": (
                "Renewable generation above consumption"
            ),
        },
        "human_review_action": (
            "Review as public evidence and document any decision-support "
            "note manually."
        ),
        "commercial_interpretation": (
            "The verified public backtest shows that DK1/DK2 surplus-risk "
            "windows can be identified from public market, consumption, and "
            "renewable production data. This is public market/system-level "
            "evidence for human review. It is not customer-specific savings."
        ),
        "pilot_next_step": (
            "Review the public proof-of-work with a pilot customer, document "
            "the customer's relevant operational assumptions, and decide "
            "whether a separate customer-specific analysis is warranted. Keep "
            "any pilot review manual and read-only unless a later scoped "
            "phase explicitly changes the boundary."
        ),
        "important_boundaries": [
            "Public market/system-level only.",
            "Not customer-specific savings.",
            "No customer load, asset, tariff, operating schedule, or site constraint data.",
            "Read-only decision support.",
            "No automatic control, dispatch, or activation.",
            "No live control signals.",
            "No asset integration.",
            "Does not establish production readiness.",
        ],
    }
    _add_verified_price_context(snapshot["top_risk_windows"])
    return snapshot


def _add_verified_price_context(
    top_risk_windows: Mapping[str, list[dict[str, Any]]],
) -> None:
    for price_area, windows in top_risk_windows.items():
        for window in windows:
            context = VERIFIED_PUBLIC_PRICE_CONTEXT.get(
                (price_area, window["start"], window["end"])
            )
            if context is None:
                window.update(_unavailable_price_context())
                continue

            window["min_price_eur_per_mwh"] = context["min_price_eur_per_mwh"]
            window["average_price_eur_per_mwh"] = context[
                "average_price_eur_per_mwh"
            ]
            window["max_price_eur_per_mwh"] = context["max_price_eur_per_mwh"]
            window["negative_price_hour_count"] = window.get("negative_price_hours")
            window["low_price_hour_count"] = window.get("low_price_hours")
            window["price_context_status"] = PRICE_CONTEXT_STATUS_AVAILABLE
            window["opportunity_signal_eur_per_mwh"] = context[
                "opportunity_signal_eur_per_mwh"
            ]
            window["opportunity_signal_note"] = AVAILABLE_PRICE_CONTEXT_NOTE


def build_price_context_from_public_prices(
    prices_eur_per_mwh: list[float],
    *,
    low_price_hour_count: int,
    negative_price_hour_count: int,
) -> dict[str, Any]:
    if not prices_eur_per_mwh:
        context = _unavailable_price_context()
        context["low_price_hour_count"] = None
        context["negative_price_hour_count"] = None
        return context

    average_price = sum(prices_eur_per_mwh) / len(prices_eur_per_mwh)
    return {
        "min_price_eur_per_mwh": min(prices_eur_per_mwh),
        "average_price_eur_per_mwh": average_price,
        "max_price_eur_per_mwh": max(prices_eur_per_mwh),
        "negative_price_hour_count": negative_price_hour_count,
        "low_price_hour_count": low_price_hour_count,
        "price_context_status": PRICE_CONTEXT_STATUS_AVAILABLE,
        "opportunity_signal_eur_per_mwh": max(
            0.0,
            REFERENCE_PRICE_EUR_PER_MWH - average_price,
        ),
        "opportunity_signal_note": AVAILABLE_PRICE_CONTEXT_NOTE,
    }


def _unavailable_price_context() -> dict[str, Any]:
    return {
        "min_price_eur_per_mwh": None,
        "average_price_eur_per_mwh": None,
        "max_price_eur_per_mwh": None,
        "negative_price_hour_count": None,
        "low_price_hour_count": None,
        "price_context_status": PRICE_CONTEXT_STATUS_NOT_AVAILABLE,
        "opportunity_signal_eur_per_mwh": None,
        "opportunity_signal_note": PRICE_CONTEXT_UNAVAILABLE_NOTE,
    }


def export_snapshot(
    config: SnapshotExportConfig,
    *,
    stdout: object | None = None,
) -> dict[str, object]:
    snapshot = build_snapshot()
    validate_snapshot(snapshot)
    output = sys.stdout if stdout is None else stdout
    payload = render_snapshot_json(snapshot)

    if config.dry_run:
        print(f"Target path: {config.output_path}", file=output)
        print(
            "Validation summary: "
            f"schema_version={snapshot['schema_version']}; "
            f"summary_areas={len(snapshot['summary_metrics'])}; "
            f"top_risk_windows={_count_risk_windows(snapshot)}; "
            "database_write_performed=false; "
            "customer_specific_savings_calculated=false",
            file=output,
        )

    if config.print_snapshot:
        print(payload, file=output)

    file_written = False
    if config.write:
        path = Path(config.output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload + "\n", encoding="utf-8")
        file_written = True

    return {
        "schema_version": snapshot["schema_version"],
        "output_path": config.output_path,
        "dry_run": config.dry_run,
        "file_written": file_written,
        "database_write_performed": False,
        "customer_specific_savings_calculated": False,
    }


def render_snapshot_json(snapshot: Mapping[str, Any]) -> str:
    return json.dumps(snapshot, indent=2, sort_keys=True)


def validate_snapshot(snapshot: Mapping[str, Any]) -> None:
    required_true_flags = (
        "not_customer_specific_savings",
        "no_automatic_control",
        "no_dispatch",
        "no_activation",
        "no_live_control_signals",
        "no_asset_integration",
    )
    required_false_flags = (
        "database_write_performed",
        "customer_specific_savings_calculated",
    )

    if snapshot.get("schema_version") != SCHEMA_VERSION:
        raise PublicSurplusRiskSnapshotExportError(
            "snapshot schema_version is invalid"
        )
    for key in (
        "period_start",
        "period_end_label",
        "source",
        "scope",
        "decision_boundary",
        "summary_metrics",
        "top_risk_windows",
        "commercial_interpretation",
        "pilot_next_step",
        "important_boundaries",
    ):
        if key not in snapshot:
            raise PublicSurplusRiskSnapshotExportError(
                f"snapshot missing required key: {key}"
            )
    for key in required_true_flags:
        if snapshot.get(key) is not True:
            raise PublicSurplusRiskSnapshotExportError(
                f"snapshot safety flag must be true: {key}"
            )
    for key in required_false_flags:
        if snapshot.get(key) is not False:
            raise PublicSurplusRiskSnapshotExportError(
                f"snapshot safety flag must be false: {key}"
            )

    summary_metrics = snapshot["summary_metrics"]
    risk_windows = snapshot["top_risk_windows"]
    if set(summary_metrics) != {"DK1", "DK2"}:
        raise PublicSurplusRiskSnapshotExportError(
            "snapshot summary_metrics must include DK1 and DK2"
        )
    if set(risk_windows) != {"DK1", "DK2"}:
        raise PublicSurplusRiskSnapshotExportError(
            "snapshot top_risk_windows must include DK1 and DK2"
        )
    if len(risk_windows["DK1"]) != 5 or len(risk_windows["DK2"]) != 5:
        raise PublicSurplusRiskSnapshotExportError(
            "snapshot top_risk_windows must include five DK1 and five DK2 windows"
        )
    required_price_context_keys = (
        "min_price_eur_per_mwh",
        "average_price_eur_per_mwh",
        "max_price_eur_per_mwh",
        "negative_price_hour_count",
        "low_price_hour_count",
        "price_context_status",
        "opportunity_signal_eur_per_mwh",
        "opportunity_signal_note",
    )
    for price_area, area_windows in risk_windows.items():
        for index, window in enumerate(area_windows):
            for key in required_price_context_keys:
                if key not in window:
                    raise PublicSurplusRiskSnapshotExportError(
                        "snapshot top_risk_windows "
                        f"{price_area}[{index}] missing price context key: {key}"
                    )
            if window["price_context_status"] == PRICE_CONTEXT_STATUS_NOT_AVAILABLE:
                for key in (
                    "min_price_eur_per_mwh",
                    "average_price_eur_per_mwh",
                    "max_price_eur_per_mwh",
                    "opportunity_signal_eur_per_mwh",
                ):
                    if window[key] is not None:
                        raise PublicSurplusRiskSnapshotExportError(
                            "unavailable price context must not include "
                            f"calculated value: {price_area}[{index}].{key}"
                        )
            elif window["price_context_status"] == PRICE_CONTEXT_STATUS_AVAILABLE:
                for key in (
                    "min_price_eur_per_mwh",
                    "average_price_eur_per_mwh",
                    "max_price_eur_per_mwh",
                    "opportunity_signal_eur_per_mwh",
                    "negative_price_hour_count",
                    "low_price_hour_count",
                ):
                    if not isinstance(window[key], int | float):
                        raise PublicSurplusRiskSnapshotExportError(
                            "available price context must include numeric "
                            f"value: {price_area}[{index}].{key}"
                        )
            else:
                raise PublicSurplusRiskSnapshotExportError(
                    "snapshot price_context_status must be available or "
                    f"not_available: {price_area}[{index}]"
                )


def main() -> int:
    try:
        config = load_config()
        result = export_snapshot(config)
    except (OSError, PublicSurplusRiskSnapshotExportError) as exc:
        print(f"Public surplus-risk snapshot export failed: {exc}", file=sys.stderr)
        return 1

    if result["file_written"]:
        print(f"Snapshot artifact written: {result['output_path']}")
    return 0


def _count_risk_windows(snapshot: Mapping[str, Any]) -> int:
    windows = snapshot["top_risk_windows"]
    return sum(len(area_windows) for area_windows in windows.values())


def _parse_bool(raw_value: str | None, env_name: str) -> bool:
    normalized = (raw_value or "").strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise PublicSurplusRiskSnapshotExportError(
        f"{env_name} must be true or false"
    )


if __name__ == "__main__":
    raise SystemExit(main())
