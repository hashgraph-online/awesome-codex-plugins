#!/usr/bin/env python3
"""Build and screen against dated publication-export planning snapshots."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from _common import CliError, emit_json, positive_float

SCHEMA_VERSION = "1.0"
PROFILE_PATH = Path(__file__).resolve().parents[1] / "assets" / "publisher_profiles.json"


def load_profiles() -> dict[str, Any]:
    """Load profiles."""
    try:
        document = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CliError(f"cannot load publisher profile asset: {exc}") from exc
    if not isinstance(document.get("profiles"), dict):
        raise CliError("publisher profile asset does not contain profiles")
    return document


def build_plan(
    publisher: str,
    *,
    figure_type: str,
    width: str | None = None,
    phase: str | None = None,
) -> dict[str, Any]:
    """Build an explicit plan without exporting or claiming compliance."""
    document = load_profiles()
    try:
        profile = document["profiles"][publisher]
    except KeyError as exc:
        raise CliError(
            f"unknown publisher profile {publisher!r}; "
            f"available: {', '.join(sorted(document['profiles']))}"
        ) from exc
    widths = profile.get("widths_mm") or {}
    if width is not None and width not in widths:
        raise CliError(
            f"unknown width {width!r} for {publisher}; "
            f"available: {', '.join(sorted(widths))}"
        )
    format_map = profile.get("formats") or {}
    dpi_map = profile.get("raster_dpi") or {}
    available_types = sorted(set(format_map) | set(dpi_map))
    if figure_type not in available_types and available_types:
        raise CliError(
            f"unknown figure type {figure_type!r} for {publisher}; "
            f"available: {', '.join(available_types)}"
        )

    profile_phase = profile.get("phase")
    phase_matches = phase is None or phase == profile_phase
    selected_width = float(widths[width]) if width is not None else None
    return {
        "schema_version": SCHEMA_VERSION,
        "publisher": publisher,
        "label": profile["label"],
        "scope": profile["scope"],
        "profile_accessed": document["accessed"],
        "profile_phase": profile_phase,
        "requested_phase": phase,
        "phase_matches_snapshot": phase_matches,
        "journal_specific": profile.get("journal_specific"),
        "figure_type": figure_type,
        "width": {
            "name": width,
            "millimeters": selected_width,
            "available": widths,
        },
        "max_height_mm": profile.get("max_height_mm"),
        "formats": format_map.get(figure_type) if format_map else None,
        "raster_dpi": dpi_map.get(figure_type) if dpi_map else None,
        "color_modes": profile.get("color_modes"),
        "preferred_color_mode": profile.get("preferred_color_mode"),
        "max_file_bytes": profile.get("max_file_bytes"),
        "max_file_bytes_exclusive": profile.get("max_file_bytes_exclusive"),
        "width_range_px_at_300_dpi": profile.get("width_range_px_at_300_dpi"),
        "max_height_px_at_300_dpi": profile.get("max_height_px_at_300_dpi"),
        "sources": profile["sources"],
        "notes": profile.get("notes", []),
        "notice": document["notice"],
    }


def _finding(
    name: str,
    status: str,
    *,
    actual: Any,
    expected: Any,
    detail: str,
) -> dict[str, Any]:
    """Handle finding."""
    return {
        "name": name,
        "status": status,
        "actual": actual,
        "expected": expected,
        "detail": detail,
    }


def _normalized_mode(mode: str | None) -> str | None:
    """Handle normalized mode."""
    if mode is None:
        return None
    if mode in {"RGB", "RGBA"}:
        return "RGB"
    if mode in {"L", "LA", "1", "I", "I;16", "F"}:
        return "L"
    return mode


def _effective_dimensions(
    metadata: dict[str, Any], target_width_mm: float | None
) -> tuple[float | None, float | None, float | None]:
    """Return effective DPI, width mm, and height mm."""
    width_px = metadata.get("width_px")
    height_px = metadata.get("height_px")
    if target_width_mm is not None and width_px:
        dpi = float(width_px) / (target_width_mm / 25.4)
        height_mm = (
            float(height_px) / float(width_px) * target_width_mm
            if height_px
            else None
        )
        return dpi, target_width_mm, height_mm
    width_mm = metadata.get("width_mm") or metadata.get("width_mm_from_metadata")
    height_mm = metadata.get("height_mm") or metadata.get("height_mm_from_metadata")
    dpi_values = [
        float(value)
        for value in (metadata.get("dpi_x"), metadata.get("dpi_y"))
        if value
    ]
    return (
        min(dpi_values) if dpi_values else None,
        float(width_mm) if width_mm is not None else None,
        float(height_mm) if height_mm is not None else None,
    )


def _below_limit(value: float, limit: Any) -> bool:
    """Return True when value is below limit beyond float rounding noise."""
    bound = float(limit)
    return value < bound and not math.isclose(value, bound, rel_tol=1e-12, abs_tol=1e-9)


def _above_limit(value: float, limit: Any) -> bool:
    """Return True when value is above limit beyond float rounding noise."""
    bound = float(limit)
    return value > bound and not math.isclose(value, bound, rel_tol=1e-12, abs_tol=1e-9)


def _dpi_status(dpi_rule: dict[str, Any], effective_dpi: float | None) -> str:
    """Classify an effective DPI against a profile's min/max rule."""
    if effective_dpi is None:
        return "unknown"
    if dpi_rule.get("min") is not None and _below_limit(effective_dpi, dpi_rule["min"]):
        return "fail"
    if (
        dpi_rule.get("min_exclusive") is not None
        and effective_dpi <= float(dpi_rule["min_exclusive"])
    ):
        return "fail"
    if dpi_rule.get("max") is not None and _above_limit(effective_dpi, dpi_rule["max"]):
        return "fail"
    return "pass"


def _format_finding(plan: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """Compare the file format with the formats recorded in the plan."""
    formats = plan.get("formats")
    actual_format = str(metadata.get("format", "")).lower()
    if formats is None:
        return _finding(
            "format",
            "unknown",
            actual=actual_format,
            expected=None,
            detail="The profile does not state a universal format for this type.",
        )
    if not formats:
        return _finding(
            "format",
            "unknown",
            actual=actual_format,
            expected=[],
            detail="No raster format was stated on the cited profile page.",
        )
    return _finding(
        "format",
        "pass" if actual_format in formats else "fail",
        actual=actual_format,
        expected=formats,
        detail="Compared with formats explicitly recorded in the snapshot.",
    )


def _dpi_finding(
    plan: dict[str, Any],
    metadata: dict[str, Any],
    effective_dpi: float | None,
) -> dict[str, Any]:
    """Screen the effective raster DPI against the profile's DPI rule."""
    dpi_rule = plan.get("raster_dpi")
    if metadata.get("kind") == "raster" and dpi_rule:
        return _finding(
            "effective_raster_dpi",
            _dpi_status(dpi_rule, effective_dpi),
            actual=effective_dpi,
            expected=dpi_rule,
            detail=(
                "Calculated at the selected final width when supplied; "
                "otherwise uses embedded DPI metadata. Upsampling is not "
                "evidence of added detail."
            ),
        )
    if dpi_rule and metadata.get("kind") != "raster":
        return _finding(
            "effective_raster_dpi",
            "unknown",
            actual=None,
            expected=dpi_rule,
            detail=(
                "Vector-container DPI is not meaningful and embedded raster "
                "objects were not individually inspected."
            ),
        )
    return _finding(
        "effective_raster_dpi",
        "unknown",
        actual=effective_dpi,
        expected=dpi_rule,
        detail="No binding DPI rule was recorded for this figure type.",
    )


def _width_finding(
    target_width: float,
    effective_width: float | None,
    width_tolerance_mm: float,
) -> dict[str, Any]:
    """Compare the effective final width with the requested target width."""
    if effective_width is None:
        width_status = "unknown"
    elif abs(effective_width - target_width) <= width_tolerance_mm:
        width_status = "pass"
    else:
        width_status = "fail"
    return _finding(
        "final_width_mm",
        width_status,
        actual=effective_width,
        expected={"target": target_width, "tolerance": width_tolerance_mm},
        detail=(
            "Raster inputs are evaluated at the requested target width; "
            "vector containers use their page dimensions."
        ),
    )


def _height_finding(max_height: Any, effective_height: float | None) -> dict[str, Any]:
    """Compare the effective final height with the profile's maximum height."""
    if effective_height is None:
        height_status = "unknown"
    elif effective_height <= float(max_height):
        height_status = "pass"
    else:
        height_status = "fail"
    return _finding(
        "final_height_mm",
        height_status,
        actual=effective_height,
        expected={"max": max_height},
        detail="Height includes the exported page/canvas, not a caption.",
    )


def _pixel_width_finding(pixel_range: Any, width_px: Any) -> dict[str, Any]:
    """Compare the pixel width with a publisher's width range stated at 300 dpi."""
    actual_width_px = int(width_px)
    return _finding(
        "pixel_width_snapshot",
        "pass" if int(pixel_range[0]) <= actual_width_px <= int(pixel_range[1]) else "fail",
        actual=actual_width_px,
        expected={"min": pixel_range[0], "max": pixel_range[1]},
        detail="This publisher expresses its width range at 300 dpi.",
    )


def _file_size_finding(plan: dict[str, Any], actual_bytes: Any) -> dict[str, Any]:
    """Compare the file size with the profile's inclusive or exclusive limit."""
    max_bytes_exclusive = plan.get("max_file_bytes_exclusive")
    if max_bytes_exclusive is not None:
        size_status = "pass" if actual_bytes < int(max_bytes_exclusive) else "fail"
        expected_size = {"less_than": max_bytes_exclusive}
    else:
        max_bytes = plan.get("max_file_bytes")
        size_status = "pass" if actual_bytes <= int(max_bytes) else "fail"
        expected_size = {"max": max_bytes}
    return _finding(
        "file_size",
        size_status,
        actual=actual_bytes,
        expected=expected_size,
        detail="Compared with the dated snapshot's file-size limit.",
    )


def _color_mode_finding(allowed_modes: Any, actual_mode: Any) -> dict[str, Any]:
    """Screen the raster color mode coarsely against the allowed modes."""
    normalized_mode = _normalized_mode(actual_mode)
    if normalized_mode is None:
        mode_status = "unknown"
    elif normalized_mode in allowed_modes:
        mode_status = "pass"
    else:
        mode_status = "fail"
    return _finding(
        "color_mode",
        mode_status,
        actual=actual_mode,
        expected=allowed_modes,
        detail=(
            "Raster mode is screened coarsely. ICC profiles and print "
            "conversion require separate color-management review."
        ),
    )


def _transparency_finding() -> dict[str, Any]:
    """Flag alpha transparency for manual review."""
    return _finding(
        "transparency",
        "review",
        actual=True,
        expected="verify against target journal/background",
        detail=(
            "The raster has alpha/transparency. Blending can change "
            "contrast, and no universal publisher rule is assumed."
        ),
    )


def _screen_findings(
    plan: dict[str, Any],
    inspected: dict[str, Any],
    width_tolerance_mm: float,
) -> list[dict[str, Any]]:
    """Build the ordered findings for one inspected file against a plan."""
    metadata = inspected["metadata"]
    findings = [_format_finding(plan, metadata)]

    target_width = plan["width"]["millimeters"]
    effective_dpi, effective_width, effective_height = _effective_dimensions(
        metadata, target_width
    )
    findings.append(_dpi_finding(plan, metadata, effective_dpi))
    if target_width is not None:
        findings.append(_width_finding(target_width, effective_width, width_tolerance_mm))

    max_height = plan.get("max_height_mm")
    if max_height is not None:
        findings.append(_height_finding(max_height, effective_height))

    pixel_range = plan.get("width_range_px_at_300_dpi")
    if pixel_range and metadata.get("width_px") is not None:
        findings.append(_pixel_width_finding(pixel_range, metadata["width_px"]))

    if (
        plan.get("max_file_bytes") is not None
        or plan.get("max_file_bytes_exclusive") is not None
    ):
        findings.append(_file_size_finding(plan, inspected["input"]["size_bytes"]))

    allowed_modes = plan.get("color_modes")
    if allowed_modes:
        findings.append(_color_mode_finding(allowed_modes, metadata.get("mode")))

    if metadata.get("has_alpha") is True:
        findings.append(_transparency_finding())
    return findings


def validate_against_plan(
    plan: dict[str, Any],
    input_path: str | Path,
    *,
    width_tolerance_mm: float = 1.0,
) -> dict[str, Any]:
    """Screen inspectable file properties against one explicit plan."""
    try:
        from image_metadata import inspect_file
    except ImportError as exc:
        raise CliError(f"cannot import image_metadata.py: {exc}") from exc
    inspected = inspect_file(input_path)
    findings = _screen_findings(plan, inspected, width_tolerance_mm)

    counts = {
        status: sum(item["status"] == status for item in findings)
        for status in ("pass", "fail", "review", "unknown")
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "plan": plan,
        "inspection": inspected,
        "findings": findings,
        "screening_summary": counts,
        "notice": (
            "This screen compares only machine-readable properties with a dated "
            "profile. It cannot certify journal acceptance, font appearance, "
            "embedded-raster quality, accessibility, or scientific integrity."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Plan publication export from dated official-source snapshots and "
            "optionally screen a local file. No network access is used."
        )
    )
    parser.add_argument("--list", action="store_true", help="list profiles")
    parser.add_argument("--publisher", help="publisher/profile key")
    parser.add_argument(
        "--figure-type",
        default="combination",
        help="figure type in the selected profile (default: combination)",
    )
    parser.add_argument("--width", help="named final width from the profile")
    parser.add_argument(
        "--phase", help="your submission phase, for an explicit scope check"
    )
    parser.add_argument("--input", help="optional local file to screen")
    parser.add_argument(
        "--width-tolerance-mm",
        type=positive_float,
        default=1.0,
        help="vector/page width tolerance (default: 1.0)",
    )
    parser.add_argument("--output", help="optional JSON output path")
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        document = load_profiles()
        if args.list:
            emit_json(
                {
                    "schema_version": SCHEMA_VERSION,
                    "accessed": document["accessed"],
                    "profiles": {
                        name: {
                            "label": profile["label"],
                            "scope": profile["scope"],
                            "phase": profile["phase"],
                            "sources": profile["sources"],
                        }
                        for name, profile in sorted(document["profiles"].items())
                    },
                    "notice": document["notice"],
                },
                output=args.output,
                force=args.force,
            )
            return 0
        if not args.publisher:
            parser.error("--publisher is required unless --list is used")
        plan = build_plan(
            args.publisher,
            figure_type=args.figure_type,
            width=args.width,
            phase=args.phase,
        )
        result = (
            validate_against_plan(
                plan,
                args.input,
                width_tolerance_mm=args.width_tolerance_mm,
            )
            if args.input
            else plan
        )
        emit_json(result, output=args.output, force=args.force)
        if args.input:
            return 1 if result["screening_summary"]["fail"] else 0
        return 0
    except CliError as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    sys.exit(main())
