#!/usr/bin/env python3
"""Validate structured ICH E3, CONSORT 2025, or SPIRIT 2025 coverage."""

from __future__ import annotations

import argparse
import sys
from typing import Any

sys.dont_write_bytecode = True

from _common import (  # noqa: E402
    ValidationError,
    error_report,
    load_json_object,
    require_bool,
    require_data_class,
    require_exact_keys,
    require_identifier,
    require_string,
    write_json_report,
)

TOOL = "validate_trial_report"
ALLOWED_STATUSES = {
    "verified_present",
    "not_applicable_with_rationale",
    "missing",
    "conflict",
}
E3_SECTIONS = (
    "title_page",
    "synopsis",
    "table_of_contents",
    "abbreviations_and_definitions",
    "ethics",
    "investigators_and_administration",
    "introduction",
    "study_objectives",
    "investigational_plan",
    "study_patients",
    "efficacy_evaluation",
    "safety_evaluation",
    "discussion_and_conclusions",
    "tables_figures_graphs_not_in_text",
    "reference_list",
    "appendices",
)
COMMON_TOP_FIELDS = {
    "schema_version",
    "artifact_kind",
    "draft_status",
    "safety_notice",
    "data_classification",
    "authorized_purpose",
    "authorization_verified",
    "guidance",
    "provenance_manifest",
    "review",
}
ROUTES = {
    "clinical_study_report_draft": {
        "container": "sections",
        "keys": E3_SECTIONS,
        "guidance": "ICH E3 Step 4 1995-11-30 with Q&A R1 2012-07-06",
        "review_fields": (
            "medical_review",
            "statistical_review",
            "safety_review",
            "privacy_legal_review",
            "quality_review",
            "regulatory_review",
        ),
        "authorization_field": "submission_authorized",
        "draft_status": "BLOCKED_INCOMPLETE_DRAFT_NOT_FOR_FILING_OR_SUBMISSION",
        "top_fields": COMMON_TOP_FIELDS | {"study_metadata", "sections"},
        "metadata_name": "study_metadata",
        "item_fields": {"status", "source_fact_ids", "rationale"},
    },
    "randomized_trial_results_draft": {
        "container": "checklist_items",
        "keys": tuple(f"C{number:02d}" for number in range(1, 31)),
        "guidance": "CONSORT 2025",
        "review_fields": (
            "accountable_author_review",
            "methodologist_review",
            "statistical_review",
            "safety_review",
        ),
        "authorization_field": "publication_authorized",
        "draft_status": (
            "BLOCKED_INCOMPLETE_DRAFT_NOT_FOR_PUBLICATION_OR_SUBMISSION"
        ),
        "top_fields": COMMON_TOP_FIELDS
        | {
            "study_metadata",
            "checklist_items",
            "not_applicable_rationales",
            "participant_flow_source_fact_ids",
        },
        "metadata_name": "study_metadata",
        "item_fields": {"status", "source_fact_ids", "official_item_locator"},
    },
    "randomized_trial_protocol_reporting_manifest": {
        "container": "checklist_items",
        "keys": tuple(f"S{number:02d}" for number in range(1, 35)),
        "guidance": "SPIRIT 2025",
        "review_fields": (
            "investigator_sponsor_review",
            "methodologist_review",
            "statistical_review",
            "safety_review",
            "ethics_regulatory_review",
        ),
        "authorization_field": "protocol_approved",
        "draft_status": (
            "BLOCKED_INCOMPLETE_REPORTING_CHECKLIST_NOT_A_PROTOCOL_OR_ETHICS_APPROVAL"
        ),
        "top_fields": COMMON_TOP_FIELDS
        | {
            "protocol_metadata",
            "checklist_items",
            "not_applicable_rationales",
            "participant_timeline_source_fact_ids",
        },
        "metadata_name": "protocol_metadata",
        "item_fields": {"status", "source_fact_ids", "official_item_locator"},
    },
}


_CSR_GUIDANCE_KEYS = {
    "base",
    "base_version",
    "qa_version",
    "gcp_version_considered",
    "regional_adoption_verified",
}
_CHECKLIST_GUIDANCE_KEYS = {
    "base",
    "item_count",
    "statement_and_explanation_checked",
    "applicable_extensions",
    "applicable_extensions_reviewed",
    "extension_conflicts_resolved_by_methodologist",
}
_CHECKLIST_GUIDANCE_PROFILES = {
    "randomized_trial_results_draft": ("CONSORT 2025", 30, "results", "CONSORT"),
    "randomized_trial_protocol_reporting_manifest": ("SPIRIT 2025", 34, "protocol", "SPIRIT"),
}
_FACT_LIST_CHECKS = {
    "randomized_trial_results_draft": (
        "participant_flow_source_fact_ids",
        "participant flow requires verified source facts",
    ),
    "randomized_trial_protocol_reporting_manifest": (
        "participant_timeline_source_fact_ids",
        "participant timeline requires verified source facts",
    ),
}


def _validate_csr_guidance(guidance: dict[str, Any], errors: list[str]) -> None:
    """Check the ICH E3 guidance block of a clinical study report draft."""
    try:
        guidance = require_exact_keys(guidance, _CSR_GUIDANCE_KEYS, "guidance")
    except ValidationError as exc:
        errors.append(str(exc))
        return
    if guidance.get("base") != "ICH E3":
        errors.append("CSR guidance.base must be ICH E3")
    if guidance.get("base_version") != "Step 4 1995-11-30":
        errors.append("CSR base_version is not the supported ICH E3 version")
    if guidance.get("qa_version") != "R1 2012-07-06":
        errors.append("CSR qa_version is not the supported E3 Q&A version")
    if guidance.get("gcp_version_considered") != "ICH E6(R3) consolidated 2026-06-16":
        errors.append("CSR must record consideration of current ICH E6(R3)")
    if guidance.get("regional_adoption_verified") is not True:
        errors.append("CSR regional adoption/version review is required")


def _validate_checklist_guidance(
    guidance: dict[str, Any],
    errors: list[str],
    profile: tuple[str, int, str, str],
) -> None:
    """Check a CONSORT or SPIRIT guidance block against its expected profile."""
    base, item_count, manifest_label, name = profile
    try:
        guidance = require_exact_keys(guidance, _CHECKLIST_GUIDANCE_KEYS, "guidance")
    except ValidationError as exc:
        errors.append(str(exc))
        return
    if guidance.get("base") != base or guidance.get("item_count") != item_count:
        errors.append(
            f"{manifest_label} manifest must declare {base} with {item_count} items"
        )
    if guidance.get("statement_and_explanation_checked") is not True:
        errors.append(f"{name} statement and explanation must be checked")
    if guidance.get("applicable_extensions_reviewed") is not True:
        errors.append(f"applicable {name} extensions must be reviewed")
    extensions = guidance.get("applicable_extensions")
    if not isinstance(extensions, list):
        errors.append("guidance.applicable_extensions must be an array")
    else:
        for index, extension in enumerate(extensions):
            try:
                require_string(
                    extension,
                    f"guidance.applicable_extensions[{index}]",
                    max_length=200,
                )
            except ValidationError as exc:
                errors.append(str(exc))
    try:
        conflicts_resolved = require_bool(
            guidance.get("extension_conflicts_resolved_by_methodologist"),
            "guidance.extension_conflicts_resolved_by_methodologist",
        )
        if extensions and not conflicts_resolved:
            errors.append("extension conflicts require methodologist resolution")
    except ValidationError as exc:
        errors.append(str(exc))


def _validate_guidance(
    artifact_kind: str,
    guidance: Any,
    errors: list[str],
) -> None:
    """Dispatch guidance validation by artifact kind."""
    if not isinstance(guidance, dict):
        errors.append("guidance must be an object")
        return
    if artifact_kind == "clinical_study_report_draft":
        _validate_csr_guidance(guidance, errors)
    elif artifact_kind in _CHECKLIST_GUIDANCE_PROFILES:
        _validate_checklist_guidance(
            guidance,
            errors,
            _CHECKLIST_GUIDANCE_PROFILES[artifact_kind],
        )


def _validate_csr_metadata(value: Any, errors: list[str]) -> None:
    """Check the study metadata of a clinical study report draft."""
    fields = {
        "protocol_reference",
        "sap_reference",
        "data_cut_reference",
        "analysis_output_reference",
        "coding_dictionary_versions",
    }
    try:
        metadata = require_exact_keys(value, fields, "study_metadata")
        for field in fields - {"coding_dictionary_versions"}:
            require_string(metadata.get(field), f"study_metadata.{field}")
        versions = metadata.get("coding_dictionary_versions")
        if not isinstance(versions, list) or not versions:
            raise ValidationError("study_metadata.coding_dictionary_versions must be non-empty")
        for index, version in enumerate(versions):
            require_string(
                version,
                f"study_metadata.coding_dictionary_versions[{index}]",
                max_length=100,
            )
    except ValidationError as exc:
        errors.append(str(exc))


def _validate_results_metadata(value: Any, errors: list[str]) -> None:
    """Check the study metadata of a randomized trial results draft."""
    fields = {
        "protocol_reference",
        "sap_reference",
        "registry_reference",
        "data_cut_reference",
        "analysis_output_reference",
    }
    try:
        metadata = require_exact_keys(value, fields, "study_metadata")
        for field in fields:
            require_string(metadata.get(field), f"study_metadata.{field}")
    except ValidationError as exc:
        errors.append(str(exc))


def _validate_protocol_metadata(value: Any, errors: list[str], warnings: list[str]) -> None:
    """Check the protocol metadata of a protocol reporting manifest."""
    fields = {
        "authorized_protocol_reference",
        "protocol_version",
        "registry_reference",
        "ethics_record_reference",
    }
    try:
        metadata = require_exact_keys(value, fields, "protocol_metadata")
        for field in fields - {"ethics_record_reference"}:
            require_string(metadata.get(field), f"protocol_metadata.{field}")
        if metadata.get("ethics_record_reference") is None:
            warnings.append("protocol_metadata.ethics_record_reference remains pending")
        else:
            require_string(
                metadata.get("ethics_record_reference"),
                "protocol_metadata.ethics_record_reference",
            )
    except ValidationError as exc:
        errors.append(str(exc))


def _validate_metadata(
    artifact_kind: str,
    value: Any,
    errors: list[str],
    warnings: list[str],
) -> None:
    """Dispatch metadata validation by artifact kind."""
    if artifact_kind == "clinical_study_report_draft":
        _validate_csr_metadata(value, errors)
    elif artifact_kind == "randomized_trial_results_draft":
        _validate_results_metadata(value, errors)
    else:
        _validate_protocol_metadata(value, errors, warnings)


def _validated_fact_ids(value: Any, field: str) -> list[str]:
    """Return validated identifiers from an array or raise a ValidationError."""
    if not isinstance(value, list):
        raise ValidationError(f"{field} must be an array")
    return [require_identifier(item, field) for item in value]


def _validate_envelope(data: dict[str, Any], route: dict[str, Any], errors: list[str]) -> None:
    """Check the top-level keys, fixed status, and authorization fields."""
    try:
        require_exact_keys(data, route["top_fields"], "manifest")
        if data.get("schema_version") != "2.0":
            raise ValidationError("schema_version must be 2.0")
        if data.get("draft_status") != route["draft_status"]:
            raise ValidationError(
                "draft_status must preserve the blocked non-use/non-submission warning"
            )
        require_string(data.get("safety_notice"), "safety_notice", max_length=1000)
        require_data_class(data.get("data_classification"))
        require_string(data.get("authorized_purpose"), "authorized_purpose")
        if not require_bool(data.get("authorization_verified"), "authorization_verified"):
            errors.append("authorization_verified must be true")
        require_string(data.get("provenance_manifest"), "provenance_manifest")
    except ValidationError as exc:
        errors.append(str(exc))


def _validate_container(
    data: dict[str, Any],
    route: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    """Return the item container after reporting missing or unexpected keys."""
    container_name = str(route["container"])
    expected_keys = tuple(route["keys"])
    container = data.get(container_name)
    if not isinstance(container, dict):
        errors.append(f"{container_name} must be an object")
        container = {}
    missing_keys = sorted(set(expected_keys) - set(container))
    extra_keys = sorted(set(container) - set(expected_keys))
    if missing_keys:
        errors.append(f"missing {container_name} keys: {missing_keys}")
    if extra_keys:
        errors.append(f"unexpected {container_name} keys: {extra_keys}")
    return container


def _check_verified_item(
    container_name: str,
    label: str,
    item: dict[str, Any],
    facts: list[str],
    errors: list[str],
) -> None:
    """Require source facts, and a locator for checklist items, on verified items."""
    if not facts:
        errors.append(f"{label} requires a verified source fact")
    if container_name != "checklist_items":
        return
    try:
        require_string(item.get("official_item_locator"), f"{label}.official_item_locator")
    except ValidationError as exc:
        errors.append(str(exc))


def _check_not_applicable_item(
    container_name: str,
    key: str,
    item: dict[str, Any],
    rationale_map: Any,
    errors: list[str],
) -> None:
    """Require a bounded rationale for an item marked not applicable."""
    label = f"{container_name}.{key}"
    try:
        if container_name == "sections":
            value, field = item.get("rationale"), f"{label}.rationale"
        else:
            value, field = rationale_map.get(key), f"not_applicable_rationales.{key}"
        require_string(value, field, max_length=500)
    except ValidationError as exc:
        errors.append(str(exc))


def _check_item(
    container_name: str,
    key: str,
    raw_item: Any,
    route: dict[str, Any],
    rationale_map: Any,
    errors: list[str],
    coverage: dict[str, str],
) -> None:
    """Validate one section or checklist item and record its coverage status."""
    label = f"{container_name}.{key}"
    if not isinstance(raw_item, dict):
        errors.append(f"{label} must be an object")
        return
    try:
        item = require_exact_keys(raw_item, route["item_fields"], label)
    except ValidationError as exc:
        errors.append(str(exc))
        return
    status = item.get("status")
    coverage[key] = str(status)
    if status not in ALLOWED_STATUSES:
        errors.append(f"{label}.status is invalid")
        return
    try:
        facts = _validated_fact_ids(item.get("source_fact_ids"), f"{label}.source_fact_ids")
    except ValidationError as exc:
        errors.append(str(exc))
        facts = []
    if status == "verified_present":
        _check_verified_item(container_name, label, item, facts, errors)
    elif status == "not_applicable_with_rationale":
        _check_not_applicable_item(container_name, key, item, rationale_map, errors)
    else:
        errors.append(f"{label} is {status}")


def _check_items(
    data: dict[str, Any],
    route: dict[str, Any],
    container: dict[str, Any],
    errors: list[str],
) -> dict[str, str]:
    """Validate every expected item and return the per-item coverage map."""
    container_name = str(route["container"])
    coverage: dict[str, str] = {}
    rationale_map = data.get("not_applicable_rationales", {})
    if container_name == "checklist_items" and not isinstance(rationale_map, dict):
        errors.append("not_applicable_rationales must be an object")
        rationale_map = {}
    for key in route["keys"]:
        _check_item(
            container_name,
            key,
            container.get(key),
            route,
            rationale_map,
            errors,
            coverage,
        )
    return coverage


def _check_source_fact_list(artifact_kind: Any, data: dict[str, Any], errors: list[str]) -> None:
    """Require verified source facts for the participant flow or timeline."""
    check = _FACT_LIST_CHECKS.get(artifact_kind)
    if check is None:
        return
    field, message = check
    try:
        if not _validated_fact_ids(data.get(field), field):
            errors.append(message)
    except ValidationError as exc:
        errors.append(str(exc))


def _check_review(
    data: dict[str, Any],
    route: dict[str, Any],
    errors: list[str],
    warnings: list[str],
) -> None:
    """Check review completion and that authorization remains false."""
    try:
        review = require_exact_keys(
            data.get("review"),
            {*route["review_fields"], route["authorization_field"]},
            "review",
        )
        for field in route["review_fields"]:
            if review.get(field) != "completed":
                warnings.append(f"review.{field} remains required")
        authorization_field = str(route["authorization_field"])
        if review.get(authorization_field) is not False:
            errors.append(f"review.{authorization_field} must remain false")
    except ValidationError as exc:
        errors.append(str(exc))


def validate_trial_manifest(data: dict[str, Any]) -> dict[str, Any]:
    """Return structural findings without evaluating trial content."""
    errors: list[str] = []
    warnings: list[str] = []
    artifact_kind = data.get("artifact_kind")
    route = ROUTES.get(artifact_kind)
    if route is None:
        return {
            "tool": TOOL,
            "status": "BLOCKED",
            "errors": [f"unsupported artifact_kind: {artifact_kind!r}"],
            "warnings": [],
            "review_required": True,
            "authorizes_clinical_use_or_submission": False,
        }

    _validate_envelope(data, route, errors)
    _validate_guidance(str(artifact_kind), data.get("guidance"), errors)
    _validate_metadata(
        str(artifact_kind),
        data.get(route["metadata_name"]),
        errors,
        warnings,
    )
    container = _validate_container(data, route, errors)
    coverage = _check_items(data, route, container, errors)
    _check_source_fact_list(artifact_kind, data, errors)
    _check_review(data, route, errors, warnings)

    return {
        "tool": TOOL,
        "artifact_kind": artifact_kind,
        "guidance": route["guidance"],
        "status": "BLOCKED" if errors else "STRUCTURE_COMPLETE_REVIEW_REQUIRED",
        "coverage": coverage,
        "errors": errors,
        "warnings": warnings,
        "limitations": [
            "Checks item keys, statuses, and provenance references only.",
            "Does not validate conduct, analyses, clinical content, compliance, or submission format.",
        ],
        "review_required": True,
        "authorizes_clinical_use_or_submission": False,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Check a bounded JSON ICH E3, CONSORT 2025, or SPIRIT 2025 "
            "coverage manifest; never claims compliance."
        )
    )
    parser.add_argument("input_file", help="Local trial-report manifest (.json)")
    parser.add_argument("-o", "--output", help="Optional local JSON report path")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface."""
    args = build_parser().parse_args(argv)
    try:
        _, data = load_json_object(args.input_file)
        report = validate_trial_manifest(data)
    except (OSError, ValidationError) as exc:
        report = error_report(TOOL, exc)
    try:
        write_json_report(report, args.output, overwrite=args.overwrite)
    except (OSError, ValidationError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0 if report["status"] == "STRUCTURE_COMPLETE_REVIEW_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
