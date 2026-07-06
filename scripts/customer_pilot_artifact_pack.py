#!/usr/bin/env python3
"""Create a local read-only customer pilot artifact pack."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
BACKEND_ROOT = REPO_ROOT / "backend"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from customer_pilot_pdf_export import (  # noqa: E402
    CustomerPilotIntakeValidationError,
    CustomerPilotOpportunityEstimateError,
    CustomerPilotPdfExportError,
    CustomerPilotSignalMatchError,
    CustomerPilotWorkflowPreviewConfig,
    CustomerPilotWorkflowPreviewError,
    render_pdf_bytes,
    render_pdf_report_text,
    run_customer_pilot_workflow_preview,
)
from customer_pilot_report_export import render_markdown_report  # noqa: E402


DEFAULT_ARTIFACT_DIR = "artifacts/customer-pilots"
DEFAULT_ARTIFACT_WRITE = "false"
DEFAULT_DRY_RUN = "true"
DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH = (
    "frontend/src/data/public-surplus-risk-backtest-snapshot.json"
)
GENERATED_ARTIFACT_FILENAMES = (
    "workflow-summary.json",
    "customer-pilot-preview.md",
    "customer-pilot-preview.pdf",
    "README.txt",
)
MANIFEST_FILENAME = "MANIFEST.json"
ARTIFACT_FILENAMES = GENERATED_ARTIFACT_FILENAMES + (MANIFEST_FILENAME,)
MANIFEST_SCHEMA_VERSION = "customer_pilot_artifact_manifest.v1"
ARTIFACT_SAFETY_BOUNDARY = (
    "local read-only pilot artifact pack",
    "public price signal only",
    "indicative gross opportunity signal only",
    "not a customer value claim",
    "not financial advice",
    "no automatic control",
    "no dispatch",
    "no activation",
    "no live control signals",
    "no asset integration",
    "no database writes",
    "no external API calls",
    "human review required",
)


class CustomerPilotArtifactPackError(RuntimeError):
    """Expected safe-fail error for customer pilot artifact pack export."""


@dataclass(frozen=True)
class CustomerPilotArtifactPackConfig:
    workflow_config: CustomerPilotWorkflowPreviewConfig
    artifact_dir: Path
    run_id: str | None
    artifact_write: bool


@dataclass(frozen=True)
class CustomerPilotArtifactPackContents:
    workflow_summary: dict[str, Any]
    markdown_report: str
    pdf_bytes: bytes
    readme_text: str
    input_path: Path
    snapshot_path: Path


def load_config(
    env: Mapping[str, str] | None = None,
) -> CustomerPilotArtifactPackConfig:
    safe_env = os.environ if env is None else env
    raw_input_path = safe_env.get("CUSTOMER_PILOT_INPUT_PATH")
    if raw_input_path is None or not raw_input_path.strip():
        raise CustomerPilotArtifactPackError("CUSTOMER_PILOT_INPUT_PATH is required")

    input_path = Path(raw_input_path).expanduser()
    if input_path.suffix.lower() != ".csv":
        raise CustomerPilotArtifactPackError(
            "Customer pilot artifact pack accepts CSV only"
        )

    snapshot_path = Path(
        (
            safe_env.get(
                "PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH",
                DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH,
            ).strip()
            or DEFAULT_PUBLIC_SURPLUS_RISK_SNAPSHOT_PATH
        )
    ).expanduser()
    artifact_dir = Path(
        (
            safe_env.get(
                "CUSTOMER_PILOT_ARTIFACT_DIR",
                DEFAULT_ARTIFACT_DIR,
            ).strip()
            or DEFAULT_ARTIFACT_DIR
        )
    ).expanduser()
    raw_run_id = safe_env.get("CUSTOMER_PILOT_ARTIFACT_RUN_ID")
    run_id = raw_run_id.strip() if raw_run_id and raw_run_id.strip() else None
    artifact_write = _parse_bool(
        safe_env.get("CUSTOMER_PILOT_ARTIFACT_WRITE", DEFAULT_ARTIFACT_WRITE),
        "CUSTOMER_PILOT_ARTIFACT_WRITE",
    )
    dry_run = _parse_bool(
        safe_env.get("CUSTOMER_PILOT_DRY_RUN", DEFAULT_DRY_RUN),
        "CUSTOMER_PILOT_DRY_RUN",
    )

    workflow_config = CustomerPilotWorkflowPreviewConfig(
        input_path=input_path,
        snapshot_path=snapshot_path,
        customer_type=(
            safe_env.get("CUSTOMER_PILOT_CUSTOMER_TYPE", "common").strip()
            or "common"
        ),
        price_area=_optional_price_area(safe_env.get("CUSTOMER_PILOT_PRICE_AREA")),
        dry_run=dry_run,
    )
    return CustomerPilotArtifactPackConfig(
        workflow_config=workflow_config,
        artifact_dir=artifact_dir,
        run_id=run_id,
        artifact_write=artifact_write,
    )


def create_customer_pilot_artifact_pack(
    config: CustomerPilotArtifactPackConfig,
    *,
    stdout: object | None = None,
) -> dict[str, Any]:
    output_stream = sys.stdout if stdout is None else stdout

    if not config.artifact_write:
        summary = run_customer_pilot_workflow_preview(config.workflow_config)
        workflow_summary = _workflow_summary_payload(summary, file_written=False)
        print(_dry_run_summary(workflow_summary), file=output_stream)
        return {
            "workflow_status": workflow_summary["workflow_status"],
            "artifact_write": False,
            "file_written": False,
            "database_write_performed": False,
            "external_api_calls_performed": False,
            "run_dir": "",
        }

    contents = build_artifact_pack_contents(config)
    run_id = _safe_run_id(config.run_id)
    run_dir = _safe_run_dir(config.artifact_dir, run_id)
    config.artifact_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=False, exist_ok=False)
    generated_at_utc = _utc_timestamp()
    _write_artifacts(
        run_dir,
        contents,
        run_id=run_id,
        generated_at_utc=generated_at_utc,
    )

    print("Customer pilot artifact pack written.", file=output_stream)
    return {
        "workflow_status": contents.workflow_summary["workflow_status"],
        "artifact_write": True,
        "file_written": True,
        "database_write_performed": False,
        "external_api_calls_performed": False,
        "run_dir": str(run_dir),
        "files": list(ARTIFACT_FILENAMES),
    }


def build_artifact_pack_contents(
    config: CustomerPilotArtifactPackConfig,
) -> CustomerPilotArtifactPackContents:
    summary = run_customer_pilot_workflow_preview(config.workflow_config)
    workflow_summary = _workflow_summary_payload(summary, file_written=True)
    return CustomerPilotArtifactPackContents(
        workflow_summary=workflow_summary,
        markdown_report=render_markdown_report(summary),
        pdf_bytes=render_pdf_bytes(summary),
        readme_text=_readme_text(),
        input_path=config.workflow_config.input_path,
        snapshot_path=config.workflow_config.snapshot_path,
    )


def main() -> int:
    try:
        config = load_config()
        result = create_customer_pilot_artifact_pack(config)
    except (
        CustomerPilotArtifactPackError,
        CustomerPilotPdfExportError,
        CustomerPilotWorkflowPreviewError,
        CustomerPilotIntakeValidationError,
        CustomerPilotSignalMatchError,
        CustomerPilotOpportunityEstimateError,
        OSError,
    ) as exc:
        print(_safe_error_message(exc))
        return 1

    if result["workflow_status"] == "invalid":
        return 1
    return 0


def _write_artifacts(
    run_dir: Path,
    contents: CustomerPilotArtifactPackContents,
    *,
    run_id: str,
    generated_at_utc: str,
) -> None:
    artifact_bytes = _artifact_bytes(contents)
    for filename, payload in artifact_bytes.items():
        (run_dir / filename).write_bytes(payload)

    manifest = _manifest_payload(
        contents.workflow_summary,
        input_path=contents.input_path,
        snapshot_path=contents.snapshot_path,
        run_id=run_id,
        generated_at_utc=generated_at_utc,
        artifact_bytes=artifact_bytes,
    )
    (run_dir / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _workflow_summary_payload(summary: Any, *, file_written: bool) -> dict[str, Any]:
    workflow_summary = summary.to_dict()
    workflow_summary.update(
        {
            "file_written": file_written,
            "database_write_performed": False,
            "external_api_calls_performed": False,
            "safety_boundary": list(ARTIFACT_SAFETY_BOUNDARY),
            "safety_flags": _artifact_safety_flags(file_written),
        }
    )
    return workflow_summary


def _artifact_bytes(contents: CustomerPilotArtifactPackContents) -> dict[str, bytes]:
    return {
        "workflow-summary.json": (
            json.dumps(contents.workflow_summary, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8"),
        "customer-pilot-preview.md": contents.markdown_report.encode("utf-8"),
        "customer-pilot-preview.pdf": contents.pdf_bytes,
        "README.txt": contents.readme_text.encode("utf-8"),
    }


def _manifest_payload(
    workflow_summary: Mapping[str, Any],
    *,
    input_path: Path,
    snapshot_path: Path,
    run_id: str,
    generated_at_utc: str,
    artifact_bytes: Mapping[str, bytes],
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at_utc": generated_at_utc,
        "artifact_type": "customer_pilot_preview_pack",
        "decision_boundary": "read-only decision support",
        "human_review_required": True,
        "public_price_signal_only": True,
        "indicative_gross_opportunity_signal_only": True,
        "not_customer_value_claim": True,
        "database_write_performed": False,
        "external_api_calls_performed": False,
        "no_automatic_control": True,
        "no_dispatch": True,
        "no_activation": True,
        "no_live_control_signals": True,
        "no_asset_integration": True,
        "input_file_sha256": _file_sha256(input_path),
        "input_file_size_bytes": input_path.stat().st_size,
        "workflow_status": workflow_summary["workflow_status"],
        "validation_status": workflow_summary["validation_status"],
        "signal_match_status": workflow_summary["signal_match_status"],
        "opportunity_estimate_status": workflow_summary[
            "opportunity_estimate_status"
        ],
        "generated_files": [
            {
                "filename": filename,
                "sha256": _bytes_sha256(payload),
                "size_bytes": len(payload),
            }
            for filename, payload in artifact_bytes.items()
        ],
    }
    public_snapshot_schema_version = _public_snapshot_schema_version(snapshot_path)
    if public_snapshot_schema_version is not None:
        manifest["public_snapshot_schema_version"] = public_snapshot_schema_version
    return manifest


def _public_snapshot_schema_version(snapshot_path: Path) -> str | None:
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    schema_version = payload.get("schema_version")
    if isinstance(schema_version, str) and schema_version.strip():
        return schema_version
    return None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bytes_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _dry_run_summary(workflow_summary: Mapping[str, Any]) -> str:
    payload = {
        "artifact_pack_status": "dry_run",
        "artifact_write": False,
        "file_written": False,
        "database_write_performed": False,
        "external_api_calls_performed": False,
        "workflow_status": workflow_summary["workflow_status"],
        "validation_status": workflow_summary["validation_status"],
        "signal_match_status": workflow_summary["signal_match_status"],
        "opportunity_estimate_status": workflow_summary[
            "opportunity_estimate_status"
        ],
        "would_create_files": list(ARTIFACT_FILENAMES),
        "safety_boundary": list(ARTIFACT_SAFETY_BOUNDARY),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def _artifact_safety_flags(file_written: bool) -> dict[str, bool]:
    return {
        "file_written": file_written,
        "database_write_performed": False,
        "external_api_calls_performed": False,
        "automatic_control_performed": False,
        "dispatch_performed": False,
        "activation_performed": False,
        "live_control_signals_performed": False,
        "asset_integration_performed": False,
        "human_review_required": True,
    }


def _readme_text() -> str:
    return "\n".join(
        [
            "Customer pilot artifact pack",
            "",
            "This is a local read-only pilot artifact pack.",
            "It uses public price signal only.",
            "It shows an indicative gross opportunity signal only.",
            "It is not a customer value claim.",
            "It is not financial advice.",
            "",
            "Files:",
            "- workflow-summary.json: workflow preview output and artifact safety flags.",
            "- customer-pilot-preview.md: Markdown pilot preview for human review.",
            "- customer-pilot-preview.pdf: PDF pilot preview for human review.",
            "- README.txt: this file.",
            "- MANIFEST.json: audit metadata and reproducibility hashes.",
            "",
            (
                "MANIFEST.json records the input file hash and generated file "
                "hashes, not raw customer data."
            ),
            (
                "Customer-specific assessment requires tariff, constraints, "
                "operating costs, and human validation."
            ),
            (
                "Customer data and generated reports must not be committed to "
                "git unless anonymized and explicitly approved."
            ),
            "",
        ]
    )


def _safe_run_id(raw_run_id: str | None) -> str:
    if raw_run_id is None:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", raw_run_id.strip())
    sanitized = sanitized.strip(".-")
    if not sanitized:
        raise CustomerPilotArtifactPackError(
            "CUSTOMER_PILOT_ARTIFACT_RUN_ID is invalid"
        )
    return sanitized[:80]


def _safe_run_dir(artifact_dir: Path, run_id: str) -> Path:
    base_dir = artifact_dir.resolve()
    run_dir = (base_dir / run_id).resolve()
    try:
        run_dir.relative_to(base_dir)
    except ValueError as exc:
        raise CustomerPilotArtifactPackError(
            "CUSTOMER_PILOT_ARTIFACT_RUN_ID must stay inside artifact directory"
        ) from exc
    if run_dir == base_dir:
        raise CustomerPilotArtifactPackError(
            "CUSTOMER_PILOT_ARTIFACT_RUN_ID must create a child run folder"
        )
    return run_dir


def _optional_price_area(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None
    value = raw_value.strip()
    return value or None


def _parse_bool(raw_value: str | None, env_name: str) -> bool:
    normalized = (raw_value or "").strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise CustomerPilotArtifactPackError(f"{env_name} must be true or false")


def _safe_error_message(exc: BaseException) -> str:
    return f"Customer pilot artifact pack failed safely: {exc.__class__.__name__}."


if __name__ == "__main__":
    raise SystemExit(main())
