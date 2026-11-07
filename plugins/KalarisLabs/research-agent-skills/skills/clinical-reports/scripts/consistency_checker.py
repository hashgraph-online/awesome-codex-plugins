#!/usr/bin/env python3
"""Check structured dates, units, denominators, percentages, and totals."""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

sys.dont_write_bytecode = True

from _common import (  # noqa: E402
    ValidationError,
    error_report,
    load_json_object,
    parse_iso_date,
    require_bool,
    require_data_class,
    require_exact_keys,
    require_identifier,
    require_nonnegative_int,
    require_string,
    write_json_report,
)

TOOL = "consistency_checker"
TOP_LEVEL_FIELDS = {
    "schema_version",
    "artifact_kind",
    "manifest_status",
    "safety_notice",
    "data_classification",
    "authorized_purpose",
    "authorization_verified",
    "provenance_manifest",
    "dates",
    "date_ranges",
    "quantities",
    "proportions",
    "totals",
}


def _array(data: dict[str, Any], field: str, errors: list[str]) -> list[Any]:
    """Handle array."""
    value = data.get(field, [])
    if not isinstance(value, list):
        errors.append(f"{field} must be an array")
        return []
    if len(value) > 10_000:
        errors.append(f"{field} may contain at most 10,000 items")
        return value[:10_000]
    return value


def _finite_number(value: Any, field: str) -> float:
    """Handle finite number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise ValidationError(f"{field} must be finite")
    return number


def _track_id(
    value: Any,
    field: str,
    seen: set[str],
    errors: list[str],
) -> str | None:
    """Handle track id."""
    try:
        identifier = require_identifier(value, field)
    except ValidationError as exc:
        errors.append(str(exc))
        return None
    if identifier in seen:
        errors.append(f"duplicate check id: {identifier}")
    seen.add(identifier)
    return identifier


_STATUS_INVALID = "BLOCKED_INVALID_SCHEMA"
_STATUS_DISCREPANT = "DISCREPANCIES_REQUIRE_RESOLUTION"
_STATUS_CONSISTENT = "CONSISTENT_WITHIN_DECLARED_TOLERANCES_REVIEW_REQUIRED"

_DATE_KEYS = {"id", "date", "source_fact_id"}
_RANGE_KEYS = {"id", "start", "end", "source_fact_id"}
_QUANTITY_KEYS = {
    "id",
    "series_id",
    "value",
    "unit",
    "expected_unit",
    "source_fact_id",
}
_PROPORTION_KEYS = {
    "id",
    "numerator",
    "denominator",
    "reported_percent",
    "tolerance_percentage_points",
    "source_fact_id",
}
_TOTAL_KEYS = {"id", "components", "reported_total", "source_fact_ids"}


@dataclass
class _Run:
    """Mutable accumulator shared by the per-section checks."""

    errors: list[str] = field(default_factory=list)
    discrepancies: list[str] = field(default_factory=list)
    seen_ids: set[str] = field(default_factory=set)
    series_units: dict[str, str] = field(default_factory=dict)
    checked: int = 0


def _check_header(data: dict[str, Any], errors: list[str]) -> None:
    """Validate the manifest envelope fields and append any errors."""
    try:
        require_exact_keys(data, TOP_LEVEL_FIELDS, "manifest")
        if data.get("schema_version") != "2.0":
            raise ValidationError("schema_version must be 2.0")
        if data.get("manifest_status") != "BLOCKED_INCOMPLETE":
            raise ValidationError("manifest_status must remain BLOCKED_INCOMPLETE")
        require_string(data.get("safety_notice"), "safety_notice", max_length=1000)
        require_string(data.get("authorized_purpose"), "authorized_purpose")
        if not require_bool(data.get("authorization_verified"), "authorization_verified"):
            raise ValidationError("authorization_verified must be true")
        require_string(data.get("provenance_manifest"), "provenance_manifest")
    except ValidationError as exc:
        errors.append(str(exc))
    if data.get("artifact_kind") != "consistency_manifest":
        errors.append("artifact_kind must be consistency_manifest")
    try:
        require_data_class(data.get("data_classification"))
    except ValidationError as exc:
        errors.append(str(exc))


def _open_item(
    run: _Run,
    raw: Any,
    section: str,
    index: int,
    keys: set[str],
) -> tuple[dict[str, Any], str | None] | None:
    """Validate an item's keys and register its id, or record the error."""
    try:
        item = require_exact_keys(raw, keys, f"{section}[{index}]")
    except ValidationError as exc:
        run.errors.append(str(exc))
        return None
    check_id = _track_id(item.get("id"), f"{section}[{index}].id", run.seen_ids, run.errors)
    return item, check_id


def _run_section(
    run: _Run,
    data: dict[str, Any],
    section: str,
    keys: set[str],
    body: Callable[[_Run, dict[str, Any], str, str | None], None],
) -> None:
    """Apply a per-item check to every item of one manifest section."""
    for index, raw in enumerate(_array(data, section, run.errors)):
        opened = _open_item(run, raw, section, index, keys)
        if opened is None:
            continue
        item, check_id = opened
        try:
            body(run, item, f"{section}[{index}]", check_id)
        except ValidationError as exc:
            run.errors.append(str(exc))


def _date_body(run: _Run, item: dict[str, Any], prefix: str, check_id: str | None) -> None:
    """Check a single dated fact."""
    parse_iso_date(item.get("date"), f"{prefix}.date")
    require_identifier(item.get("source_fact_id"), f"{prefix}.source_fact_id")
    run.checked += 1


def _range_body(run: _Run, item: dict[str, Any], prefix: str, check_id: str | None) -> None:
    """Check that a date range does not start after it ends."""
    start = parse_iso_date(item.get("start"), f"{prefix}.start")
    end = parse_iso_date(item.get("end"), f"{prefix}.end")
    require_identifier(item.get("source_fact_id"), f"{prefix}.source_fact_id")
    run.checked += 1
    if start > end and check_id:
        run.discrepancies.append(f"{check_id}: start date is after end date")


def _quantity_body(run: _Run, item: dict[str, Any], prefix: str, check_id: str | None) -> None:
    """Check a quantity's unit against its series and its expected unit."""
    series_id = require_identifier(item.get("series_id"), f"{prefix}.series_id")
    _finite_number(item.get("value"), f"{prefix}.value")
    unit = require_string(item.get("unit"), f"{prefix}.unit", max_length=80)
    require_identifier(item.get("source_fact_id"), f"{prefix}.source_fact_id")
    run.checked += 1
    prior = run.series_units.get(series_id)
    if prior is not None and prior != unit and check_id:
        run.discrepancies.append(
            f"{check_id}: unit {unit!r} differs from prior series unit {prior!r}"
        )
    else:
        run.series_units[series_id] = unit
    expected = item.get("expected_unit")
    if expected is None:
        return
    expected_unit = require_string(expected, f"{prefix}.expected_unit", max_length=80)
    if expected_unit != unit and check_id:
        run.discrepancies.append(f"{check_id}: unit does not match expected_unit")


def _proportion_body(
    run: _Run,
    item: dict[str, Any],
    prefix: str,
    check_id: str | None,
) -> None:
    """Check an n/N proportion against its reported percentage."""
    numerator = require_nonnegative_int(item.get("numerator"), f"{prefix}.numerator")
    denominator = require_nonnegative_int(item.get("denominator"), f"{prefix}.denominator")
    reported = _finite_number(item.get("reported_percent"), f"{prefix}.reported_percent")
    tolerance = _finite_number(
        item.get("tolerance_percentage_points", 0.05),
        f"{prefix}.tolerance_percentage_points",
    )
    require_identifier(item.get("source_fact_id"), f"{prefix}.source_fact_id")
    run.checked += 1
    if denominator == 0:
        run.errors.append(f"{prefix}.denominator must be greater than zero")
    elif numerator > denominator and check_id:
        run.discrepancies.append(f"{check_id}: numerator exceeds denominator")
    elif not 0 <= reported <= 100 and check_id:
        run.discrepancies.append(f"{check_id}: reported_percent is outside 0-100")
    elif tolerance < 0:
        run.errors.append(f"{prefix}.tolerance_percentage_points must be non-negative")
    elif abs(numerator / denominator * 100 - reported) > tolerance and check_id:
        run.discrepancies.append(
            f"{check_id}: reported_percent differs from n/N beyond tolerance"
        )


def _non_empty_list(value: Any, field_name: str) -> list[Any]:
    """Return a non-empty list or raise a ValidationError."""
    if not isinstance(value, list) or not value:
        raise ValidationError(f"{field_name} must be non-empty")
    return value


def _total_body(run: _Run, item: dict[str, Any], prefix: str, check_id: str | None) -> None:
    """Check that components sum to the reported total."""
    components = _non_empty_list(item.get("components"), f"{prefix}.components")
    parsed_components = [
        require_nonnegative_int(value, f"{prefix}.components") for value in components
    ]
    reported_total = require_nonnegative_int(
        item.get("reported_total"),
        f"{prefix}.reported_total",
    )
    source_fact_ids = _non_empty_list(item.get("source_fact_ids"), f"{prefix}.source_fact_ids")
    for fact_id in source_fact_ids:
        require_identifier(fact_id, f"{prefix}.source_fact_ids")
    run.checked += 1
    if sum(parsed_components) != reported_total and check_id:
        run.discrepancies.append(f"{check_id}: components do not equal reported_total")


_SECTIONS = (
    ("dates", _DATE_KEYS, _date_body),
    ("date_ranges", _RANGE_KEYS, _range_body),
    ("quantities", _QUANTITY_KEYS, _quantity_body),
    ("proportions", _PROPORTION_KEYS, _proportion_body),
    ("totals", _TOTAL_KEYS, _total_body),
)


def validate_consistency(data: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic discrepancies without changing any values."""
    run = _Run()
    warnings: list[str] = []
    _check_header(data, run.errors)
    for section, keys, body in _SECTIONS:
        _run_section(run, data, section, keys, body)

    if run.checked == 0:
        run.errors.append("manifest contains no valid checks")
    if not run.discrepancies and not run.errors:
        warnings.append("No discrepancy was found within the declared checks and tolerances.")

    if run.errors:
        status = _STATUS_INVALID
    elif run.discrepancies:
        status = _STATUS_DISCREPANT
    else:
        status = _STATUS_CONSISTENT
    return {
        "tool": TOOL,
        "status": status,
        "checks_completed": run.checked,
        "errors": run.errors,
        "discrepancies": run.discrepancies,
        "warnings": warnings,
        "limitations": [
            "No source was chosen as authoritative and no value was changed.",
            "Arithmetic and format checks do not validate clinical or statistical meaning.",
        ],
        "review_required": True,
        "authorizes_clinical_use_or_submission": False,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Check bounded structured dates, units, n/N percentages, and totals. "
            "Does not infer, convert, reconcile, or alter values."
        )
    )
    parser.add_argument("input_file", help="Local consistency manifest (.json)")
    parser.add_argument("-o", "--output", help="Optional local JSON report")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    args = build_parser().parse_args(argv)
    try:
        _, data = load_json_object(args.input_file)
        report = validate_consistency(data)
    except (OSError, ValidationError) as exc:
        report = error_report(TOOL, exc)
    try:
        write_json_report(report, args.output, overwrite=args.overwrite)
    except (OSError, ValidationError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return (
        0
        if report["status"]
        == "CONSISTENT_WITHIN_DECLARED_TOLERANCES_REVIEW_REQUIRED"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
