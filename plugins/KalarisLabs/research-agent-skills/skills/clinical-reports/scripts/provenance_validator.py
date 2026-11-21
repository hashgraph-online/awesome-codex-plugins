#!/usr/bin/env python3
"""Validate source-fact-to-claim traceability without opening source records."""

from __future__ import annotations

import argparse
import re
import sys
from typing import Any

sys.dont_write_bytecode = True

from _common import (  # noqa: E402
    SHA256_RE,
    ValidationError,
    error_report,
    load_json_object,
    parse_iso_date,
    require_bool,
    require_data_class,
    require_exact_keys,
    require_identifier,
    require_string,
    write_json_report,
)

TOOL = "provenance_validator"
LOCAL_LOCATOR_RE = re.compile(r"^local:[A-Za-z0-9_./:-]{1,280}$")
SOURCE_KINDS = {
    "synthetic_record",
    "deidentified_record",
    "aggregate_output",
    "protocol",
    "statistical_analysis_plan",
    "published_source",
    "authorized_system_record",
}
FACT_FIELDS = {
    "fact_id",
    "source_record_kind",
    "record_locator",
    "field_path",
    "value_hash_sha256",
    "verification_status",
    "verified_by_role",
    "verified_at",
    "source_version",
}
CLAIM_FIELDS = {
    "claim_id",
    "artifact_field_path",
    "fact_ids",
    "support_status",
}
TOP_LEVEL_FIELDS = {
    "schema_version",
    "artifact_kind",
    "manifest_status",
    "safety_notice",
    "data_classification",
    "authorized_purpose",
    "authorization_verified",
    "facts",
    "claims",
    "review",
}


_MAX_ITEMS = 10_000
_REVIEW_FIELDS = ("source_owner_review", "quality_review", "privacy_review")


def _check_header(data: dict[str, Any], errors: list[str]) -> None:
    """Validate the manifest envelope, classification, and authorization fields."""
    try:
        require_exact_keys(data, TOP_LEVEL_FIELDS, "manifest")
        if data.get("schema_version") != "2.0":
            raise ValidationError("schema_version must be 2.0")
        if data.get("manifest_status") != "BLOCKED_INCOMPLETE":
            raise ValidationError("manifest_status must remain BLOCKED_INCOMPLETE")
        require_string(data.get("safety_notice"), "safety_notice", max_length=1000)
    except ValidationError as exc:
        errors.append(str(exc))
    if data.get("artifact_kind") != "provenance_manifest":
        errors.append("artifact_kind must be provenance_manifest")
    try:
        require_data_class(data.get("data_classification"))
        require_string(data.get("authorized_purpose"), "authorized_purpose")
        if not require_bool(data.get("authorization_verified"), "authorization_verified"):
            errors.append("authorization_verified must be true")
    except ValidationError as exc:
        errors.append(str(exc))


def _bounded_array(data: dict[str, Any], name: str, errors: list[str]) -> list[Any]:
    """Return a non-empty list field, recording shape and size errors."""
    value = data.get(name)
    if not isinstance(value, list) or not value:
        errors.append(f"{name} must be a non-empty array")
        value = []
    return value


def _check_fact_fields(
    fact: dict[str, Any],
    label: str,
    fact_ids: set[str],
    errors: list[str],
) -> None:
    """Validate the value-level fields of one verified fact."""
    fact_id = require_identifier(fact.get("fact_id"), f"{label}.fact_id")
    if fact_id in fact_ids:
        errors.append(f"duplicate fact_id: {fact_id}")
    fact_ids.add(fact_id)
    if fact.get("source_record_kind") not in SOURCE_KINDS:
        errors.append(f"{label}.source_record_kind is invalid")
    locator = require_string(
        fact.get("record_locator"),
        f"{label}.record_locator",
        max_length=286,
    )
    if not LOCAL_LOCATOR_RE.fullmatch(locator):
        errors.append(f"{label}.record_locator must be a local: locator")
    require_string(fact.get("field_path"), f"{label}.field_path", max_length=300)
    value_hash = require_string(
        fact.get("value_hash_sha256"),
        f"{label}.value_hash_sha256",
        max_length=64,
    )
    if not SHA256_RE.fullmatch(value_hash):
        errors.append(f"{label}.value_hash_sha256 is invalid")
    if fact.get("verification_status") != "verified":
        errors.append(f"{label} is not verified")
    require_string(
        fact.get("verified_by_role"),
        f"{label}.verified_by_role",
        max_length=100,
    )
    parse_iso_date(fact.get("verified_at"), f"{label}.verified_at")
    require_string(fact.get("source_version"), f"{label}.source_version", max_length=100)


def _check_facts(facts: list[Any], errors: list[str]) -> set[str]:
    """Validate every fact and return the set of declared fact identifiers."""
    fact_ids: set[str] = set()
    for index, raw in enumerate(facts[:_MAX_ITEMS]):
        label = f"facts[{index}]"
        try:
            fact = require_exact_keys(raw, FACT_FIELDS, label)
        except ValidationError as exc:
            errors.append(str(exc))
            continue
        try:
            _check_fact_fields(fact, label, fact_ids, errors)
        except ValidationError as exc:
            errors.append(str(exc))
    return fact_ids


def _check_claim_fields(
    claim: dict[str, Any],
    label: str,
    claim_ids: set[str],
    fact_ids: set[str],
    referenced_facts: set[str],
    errors: list[str],
) -> None:
    """Validate one claim and the facts it links to."""
    claim_id = require_identifier(claim.get("claim_id"), f"{label}.claim_id")
    if claim_id in claim_ids:
        errors.append(f"duplicate claim_id: {claim_id}")
    claim_ids.add(claim_id)
    require_string(
        claim.get("artifact_field_path"),
        f"{label}.artifact_field_path",
        max_length=300,
    )
    links = claim.get("fact_ids")
    if not isinstance(links, list) or not links:
        errors.append(f"{label}.fact_ids must be a non-empty array")
        links = []
    for linked in links:
        linked_id = require_identifier(linked, f"{label}.fact_ids")
        referenced_facts.add(linked_id)
        if linked_id not in fact_ids:
            errors.append(f"{label} references unknown fact_id {linked_id}")
    if claim.get("support_status") != "supported_by_verified_facts":
        errors.append(f"{label} is not marked supported_by_verified_facts")


def _check_claims(claims: list[Any], fact_ids: set[str], errors: list[str]) -> set[str]:
    """Validate every claim and return the set of fact identifiers they reference."""
    claim_ids: set[str] = set()
    referenced_facts: set[str] = set()
    for index, raw in enumerate(claims[:_MAX_ITEMS]):
        label = f"claims[{index}]"
        try:
            claim = require_exact_keys(raw, CLAIM_FIELDS, label)
        except ValidationError as exc:
            errors.append(str(exc))
            continue
        try:
            _check_claim_fields(claim, label, claim_ids, fact_ids, referenced_facts, errors)
        except ValidationError as exc:
            errors.append(str(exc))
    return referenced_facts


def _check_review(data: dict[str, Any], errors: list[str], warnings: list[str]) -> None:
    """Check review completion and that release authorization remains false."""
    try:
        review = require_exact_keys(
            data.get("review"),
            {*_REVIEW_FIELDS, "release_authorized"},
            "review",
        )
        for field in _REVIEW_FIELDS:
            if review.get(field) != "completed":
                warnings.append(f"review.{field} remains required")
        if review.get("release_authorized") is not False:
            errors.append("review.release_authorized must remain false")
    except ValidationError as exc:
        errors.append(str(exc))


def validate_provenance(data: dict[str, Any]) -> dict[str, Any]:
    """Validate bounded metadata links while preserving source separation."""
    errors: list[str] = []
    warnings: list[str] = []
    _check_header(data, errors)

    facts = _bounded_array(data, "facts", errors)
    claims = _bounded_array(data, "claims", errors)
    if len(facts) > _MAX_ITEMS:
        errors.append("facts may contain at most 10,000 items")
    if len(claims) > _MAX_ITEMS:
        errors.append("claims may contain at most 10,000 items")

    fact_ids = _check_facts(facts, errors)
    referenced_facts = _check_claims(claims, fact_ids, errors)

    unused = sorted(fact_ids - referenced_facts)
    if unused:
        warnings.append(f"{len(unused)} verified facts are not linked to a claim")

    _check_review(data, errors, warnings)

    return {
        "tool": TOOL,
        "status": "BLOCKED" if errors else "TRACEABILITY_COMPLETE_REVIEW_REQUIRED",
        "fact_count": len(facts),
        "claim_count": len(claims),
        "linked_fact_count": len(referenced_facts),
        "errors": errors,
        "warnings": warnings,
        "limitations": [
            "Source records were not opened and hash values were not recomputed.",
            "Traceability metadata does not establish source truth or clinical correctness.",
        ],
        "review_required": True,
        "authorizes_clinical_use_or_submission": False,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Check bounded local source-fact traceability metadata. "
            "Does not open source records or copy clinical content."
        )
    )
    parser.add_argument("input_file", help="Local provenance manifest (.json)")
    parser.add_argument("-o", "--output", help="Optional local JSON report")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    args = build_parser().parse_args(argv)
    try:
        _, data = load_json_object(args.input_file)
        report = validate_provenance(data)
    except (OSError, ValidationError) as exc:
        report = error_report(TOOL, exc)
    try:
        write_json_report(report, args.output, overwrite=args.overwrite)
    except (OSError, ValidationError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0 if report["status"] == "TRACEABILITY_COMPLETE_REVIEW_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
