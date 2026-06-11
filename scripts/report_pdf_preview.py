#!/usr/bin/env python3
"""Manual synthetic local PDF preview for report-summary-v0."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.reporting.markdown import render_report_summary_markdown  # noqa: E402
from app.reporting.pdf import render_report_markdown_pdf_bytes  # noqa: E402
from app.reporting.summary import build_report_summary  # noqa: E402
from report_summary_preview import (  # noqa: E402
    GENERATED_AT_UTC,
    SCENARIOS,
    build_inputs,
)


SOURCE_NOTES = (
    "synthetic local PDF preview only",
    "caller-provided sample current-risk and forecast-window data only",
    "does not fetch data, access databases, run SQL, start servers, use ML, or use LLMs",
    "must not be used for automatic control, dispatch, or activation",
    "human review required before planning",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a manual synthetic local report-summary-v0 PDF preview to "
            "an explicit local output path."
        )
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Explicit local PDF output path. Required.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the explicit output path if it already exists.",
    )
    parser.add_argument(
        "--price-area",
        choices=("DK1", "DK2"),
        default="DK1",
        help="Danish price area to include in the preview. Default: DK1.",
    )
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS,
        default="standard",
        help="Synthetic local report scenario to preview. Default: standard.",
    )
    return parser


def print_scope_warning() -> None:
    print(
        "WARNING: synthetic local PDF preview only. Read-only decision support "
        "only. Human review required. Must not be used for automatic control, "
        "dispatch, or activation.",
        file=sys.stderr,
    )


def _format_utc_timestamp(value: Any) -> Any:
    if hasattr(value, "astimezone"):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return value


def _write_pdf(path: Path, pdf_bytes: bytes, *, force: bool) -> int:
    if path.exists() and not force:
        print(
            f"Refusing to overwrite existing output path without --force: {path}",
            file=sys.stderr,
        )
        return 2
    if path.exists() and path.is_dir():
        print(f"Output path is a directory, not a PDF file path: {path}", file=sys.stderr)
        return 2
    path.write_bytes(pdf_bytes)
    return 0


def main() -> int:
    args = build_parser().parse_args()
    print_scope_warning()

    output_path = Path(args.output)
    current_risk, forecast = build_inputs(args.scenario)
    report = build_report_summary(
        price_area=args.price_area,
        generated_at_utc=GENERATED_AT_UTC,
        current_risk=current_risk,
        forecast=forecast,
        source_notes=SOURCE_NOTES,
    )
    markdown = render_report_summary_markdown(report)
    pdf_bytes = render_report_markdown_pdf_bytes(
        markdown,
        title=str(report["title"]),
    )

    write_result = _write_pdf(output_path, pdf_bytes, force=args.force)
    if write_result != 0:
        return write_result

    summary = {
        "output_path": str(output_path),
        "bytes_written": len(pdf_bytes),
        "price_area": args.price_area,
        "scenario": args.scenario,
        "report_version": report["report_version"],
        "decision_support_only": report["decision_support_only"],
        "synthetic_preview_only": True,
        "generated_at_utc": _format_utc_timestamp(report["generated_at_utc"]),
    }
    print(json.dumps(summary, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
