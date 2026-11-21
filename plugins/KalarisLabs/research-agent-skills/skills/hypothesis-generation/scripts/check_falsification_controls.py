#!/usr/bin/env python3
"""Audit falsifiers, discriminating tests, nulls, and controls without scoring."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from _common import (
    ValidationError,
    error_exit,
    issue,
    read_json,
    require_enum,
    require_exact_keys,
    require_identifier,
    require_list,
    require_object,
    require_text,
    require_text_list,
    require_unique,
    write_json_report,
)
from validate_hypothesis_schema import load_hypothesis_record, validate_record

CONTROL_TYPES = {
    "negative_exposure",
    "negative_outcome",
    "procedural_negative",
    "positive_control",
    "vehicle_or_sham",
    "other",
}
NEGATIVE_TYPES = {"negative_exposure", "negative_outcome", "procedural_negative"}


def _parse_falsifier(raw: Any, context: str) -> dict[str, Any]:
    """Parse falsifier."""
    value = require_object(raw, context)
    require_exact_keys(
        value,
        required={
            "prediction_id",
            "conditions",
            "observable",
            "incompatible_result",
            "assumption_failure_checks",
        },
        context=context,
    )
    return {
        "prediction_id": require_identifier(
            value["prediction_id"], f"{context}.prediction_id"
        ),
        "conditions": require_text(
            value["conditions"], f"{context}.conditions", minimum=10
        ),
        "observable": require_text(
            value["observable"], f"{context}.observable", minimum=5
        ),
        "incompatible_result": require_text(
            value["incompatible_result"],
            f"{context}.incompatible_result",
            minimum=10,
        ),
        "assumption_failure_checks": require_text_list(
            value["assumption_failure_checks"],
            f"{context}.assumption_failure_checks",
            minimum=1,
        ),
    }


def _parse_discriminating_tests(raw: Any, context: str) -> list[dict[str, str]]:
    """Parse discriminating tests."""
    values = require_list(raw, context, minimum=1, maximum=100)
    parsed: list[dict[str, str]] = []
    identifiers: list[str] = []
    fields = {
        "test_id",
        "rival_hypothesis_id",
        "focal_expected",
        "rival_expected",
        "indeterminate_result",
    }
    for index, raw_value in enumerate(values):
        item_context = f"{context}[{index}]"
        value = require_object(raw_value, item_context)
        require_exact_keys(value, required=fields, context=item_context)
        test_id = require_identifier(value["test_id"], f"{item_context}.test_id")
        identifiers.append(test_id)
        parsed.append(
            {
                "test_id": test_id,
                "rival_hypothesis_id": require_identifier(
                    value["rival_hypothesis_id"],
                    f"{item_context}.rival_hypothesis_id",
                ),
                "focal_expected": require_text(
                    value["focal_expected"],
                    f"{item_context}.focal_expected",
                    minimum=10,
                ),
                "rival_expected": require_text(
                    value["rival_expected"],
                    f"{item_context}.rival_expected",
                    minimum=10,
                ),
                "indeterminate_result": require_text(
                    value["indeterminate_result"],
                    f"{item_context}.indeterminate_result",
                    minimum=10,
                ),
            }
        )
    require_unique(identifiers, context)
    return parsed


def _parse_nulls(raw: Any, context: str) -> list[dict[str, str]]:
    """Parse nulls."""
    values = require_list(raw, context, minimum=1, maximum=100)
    parsed: list[dict[str, str]] = []
    identifiers: list[str] = []
    fields = {"null_id", "statement", "analysis_id", "interpretation_limit"}
    for index, raw_value in enumerate(values):
        item_context = f"{context}[{index}]"
        value = require_object(raw_value, item_context)
        require_exact_keys(value, required=fields, context=item_context)
        null_id = require_identifier(value["null_id"], f"{item_context}.null_id")
        identifiers.append(null_id)
        parsed.append(
            {
                "null_id": null_id,
                "statement": require_text(
                    value["statement"], f"{item_context}.statement", minimum=10
                ),
                "analysis_id": require_identifier(
                    value["analysis_id"], f"{item_context}.analysis_id"
                ),
                "interpretation_limit": require_text(
                    value["interpretation_limit"],
                    f"{item_context}.interpretation_limit",
                    minimum=10,
                ),
            }
        )
    require_unique(identifiers, context)
    return parsed


def _parse_controls(raw: Any, context: str) -> list[dict[str, str]]:
    """Parse controls."""
    values = require_list(raw, context, minimum=1, maximum=100)
    parsed: list[dict[str, str]] = []
    identifiers: list[str] = []
    fields = {
        "control_id",
        "control_type",
        "rationale",
        "expected_result",
        "failure_implication",
    }
    for index, raw_value in enumerate(values):
        item_context = f"{context}[{index}]"
        value = require_object(raw_value, item_context)
        require_exact_keys(value, required=fields, context=item_context)
        control_id = require_identifier(
            value["control_id"], f"{item_context}.control_id"
        )
        identifiers.append(control_id)
        parsed.append(
            {
                "control_id": control_id,
                "control_type": require_enum(
                    value["control_type"],
                    CONTROL_TYPES,
                    f"{item_context}.control_type",
                ),
                "rationale": require_text(
                    value["rationale"], f"{item_context}.rationale", minimum=10
                ),
                "expected_result": require_text(
                    value["expected_result"],
                    f"{item_context}.expected_result",
                    minimum=5,
                ),
                "failure_implication": require_text(
                    value["failure_implication"],
                    f"{item_context}.failure_implication",
                    minimum=10,
                ),
            }
        )
    require_unique(identifiers, context)
    return parsed


def _parse_outcome_interpretation(raw: Any, context: str) -> dict[str, str]:
    """Parse outcome interpretation."""
    value = require_object(raw, context)
    fields = {
        "consistent_with_candidate",
        "challenges_candidate",
        "supports_neither_or_mixed",
    }
    require_exact_keys(value, required=fields, context=context)
    return {
        field: require_text(value[field], f"{context}.{field}", minimum=10)
        for field in fields
    }


def load_checklist(payload: Any) -> dict[str, Any]:
    """Load checklist."""
    root = require_object(payload, "checklist")
    require_exact_keys(
        root,
        required={"schema_version", "checklist_id", "record_id", "hypotheses"},
        context="checklist",
    )
    raw_hypotheses = require_list(
        root["hypotheses"], "checklist.hypotheses", minimum=1, maximum=50
    )
    parsed_hypotheses: list[dict[str, Any]] = []
    hypothesis_ids: list[str] = []
    fields = {
        "hypothesis_id",
        "candidate_status",
        "assumptions",
        "boundary_conditions",
        "falsifier",
        "discriminating_tests",
        "nulls",
        "controls",
        "outcome_interpretation",
        "human_review_status",
    }
    for index, raw_hypothesis in enumerate(raw_hypotheses):
        context = f"checklist.hypotheses[{index}]"
        hypothesis = require_object(raw_hypothesis, context)
        require_exact_keys(hypothesis, required=fields, context=context)
        hypothesis_id = require_identifier(
            hypothesis["hypothesis_id"], f"{context}.hypothesis_id"
        )
        hypothesis_ids.append(hypothesis_id)
        parsed_hypotheses.append(
            {
                "hypothesis_id": hypothesis_id,
                "candidate_status": require_enum(
                    hypothesis["candidate_status"],
                    {"candidate"},
                    f"{context}.candidate_status",
                ),
                "assumptions": require_text_list(
                    hypothesis["assumptions"],
                    f"{context}.assumptions",
                    minimum=1,
                ),
                "boundary_conditions": require_text_list(
                    hypothesis["boundary_conditions"],
                    f"{context}.boundary_conditions",
                    minimum=1,
                ),
                "falsifier": _parse_falsifier(
                    hypothesis["falsifier"], f"{context}.falsifier"
                ),
                "discriminating_tests": _parse_discriminating_tests(
                    hypothesis["discriminating_tests"],
                    f"{context}.discriminating_tests",
                ),
                "nulls": _parse_nulls(
                    hypothesis["nulls"], f"{context}.nulls"
                ),
                "controls": _parse_controls(
                    hypothesis["controls"], f"{context}.controls"
                ),
                "outcome_interpretation": _parse_outcome_interpretation(
                    hypothesis["outcome_interpretation"],
                    f"{context}.outcome_interpretation",
                ),
                "human_review_status": require_enum(
                    hypothesis["human_review_status"],
                    {"pending", "complete", "specialist_required"},
                    f"{context}.human_review_status",
                ),
            }
        )
    require_unique(hypothesis_ids, "checklist.hypotheses")
    return {
        "schema_version": require_enum(
            root["schema_version"], {"2.0"}, "checklist.schema_version"
        ),
        "checklist_id": require_identifier(
            root["checklist_id"], "checklist.checklist_id"
        ),
        "record_id": require_identifier(root["record_id"], "checklist.record_id"),
        "hypotheses": parsed_hypotheses,
    }


def _normalize(value: str) -> str:
    """Normalize."""
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


@dataclass
class _AuditState:
    """Mutable findings shared by the per-hypothesis audit steps."""

    record_ids: dict[str, set[str]] | None
    errors: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)
    review_counts: Counter[str] = field(default_factory=Counter)
    test_ids: list[str] = field(default_factory=list)
    null_ids: list[str] = field(default_factory=list)

    def check_known(self, group: str, value: str, code: str, subject: str) -> None:
        """Record an error when a record cross-check is active and value is unknown."""
        if self.record_ids is not None and value not in self.record_ids[group]:
            self.errors.append(issue(code, subject))


def _record_id_sets(record: dict[str, Any] | None) -> dict[str, set[str]] | None:
    """Return identifier sets from a validated hypothesis record, if one was given."""
    if record is None:
        return None
    record_report = validate_record(record)
    if not record_report["valid"]:
        raise ValidationError(
            "optional hypothesis record must pass schema validation first"
        )
    return {
        "hypotheses": {item["hypothesis_id"] for item in record["hypotheses"]},
        "predictions": {item["prediction_id"] for item in record["predictions"]},
        "analyses": {
            item["analysis_id"] for item in record["analysis_plan"]["analyses"]
        },
        "controls": {item["control_id"] for item in record["negative_controls"]},
        "nulls": {item["null_id"] for item in record["null_hypotheses"]},
    }


def _audit_tests(state: _AuditState, hypothesis: dict[str, Any]) -> None:
    """Audit discriminating tests for rival identity, contrast, and record links."""
    hypothesis_id = hypothesis["hypothesis_id"]
    for test in hypothesis["discriminating_tests"]:
        state.test_ids.append(test["test_id"])
        if test["rival_hypothesis_id"] == hypothesis_id:
            state.errors.append(issue("FOCAL_HYPOTHESIS_LISTED_AS_RIVAL", test["test_id"]))
        if _normalize(test["focal_expected"]) == _normalize(test["rival_expected"]):
            state.errors.append(
                issue("FOCAL_AND_RIVAL_EXPECTATIONS_IDENTICAL", test["test_id"])
            )
        state.check_known(
            "hypotheses",
            test["rival_hypothesis_id"],
            "UNKNOWN_RIVAL_HYPOTHESIS_ID",
            test["test_id"],
        )


def _audit_nulls(state: _AuditState, hypothesis: dict[str, Any]) -> None:
    """Audit null hypotheses against the optional record."""
    for null in hypothesis["nulls"]:
        state.null_ids.append(null["null_id"])
        state.check_known("nulls", null["null_id"], "UNKNOWN_NULL_ID", null["null_id"])
        state.check_known(
            "analyses", null["analysis_id"], "UNKNOWN_ANALYSIS_ID", null["analysis_id"]
        )


def _audit_controls(state: _AuditState, hypothesis: dict[str, Any]) -> None:
    """Require a negative control and check negative controls against the record."""
    negative_controls = [
        control
        for control in hypothesis["controls"]
        if control["control_type"] in NEGATIVE_TYPES
    ]
    if not negative_controls:
        state.errors.append(issue("NEGATIVE_CONTROL_REQUIRED", hypothesis["hypothesis_id"]))
    for control in negative_controls:
        state.check_known(
            "controls",
            control["control_id"],
            "UNKNOWN_NEGATIVE_CONTROL_ID",
            control["control_id"],
        )


def _audit_hypothesis(state: _AuditState, hypothesis: dict[str, Any]) -> None:
    """Run every audit step for one checklist hypothesis."""
    hypothesis_id = hypothesis["hypothesis_id"]
    state.review_counts[hypothesis["human_review_status"]] += 1
    if hypothesis["human_review_status"] != "complete":
        state.warnings.append(issue("HUMAN_REVIEW_INCOMPLETE", hypothesis_id))

    if state.record_ids is not None:
        prediction_id = hypothesis["falsifier"]["prediction_id"]
        state.check_known("hypotheses", hypothesis_id, "UNKNOWN_HYPOTHESIS_ID", hypothesis_id)
        state.check_known("predictions", prediction_id, "UNKNOWN_PREDICTION_ID", prediction_id)
    _audit_tests(state, hypothesis)
    _audit_nulls(state, hypothesis)
    _audit_controls(state, hypothesis)


def _checklist_status(errors: list[dict[str, str]], hypotheses: list[dict[str, Any]]) -> str:
    """Summarize validity and human-review declarations as a status string."""
    if errors:
        return "INVALID_CHECKLIST"
    if any(item["human_review_status"] != "complete" for item in hypotheses):
        return "VALID_PENDING_HUMAN_REVIEW"
    return "VALID_HUMAN_REVIEW_DECLARED_COMPLETE"


def audit(
    checklist: dict[str, Any], record: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Audit a parsed checklist, optionally cross-checking a validated record."""
    state = _AuditState(record_ids=_record_id_sets(record))
    for hypothesis in checklist["hypotheses"]:
        _audit_hypothesis(state, hypothesis)

    require_unique(state.test_ids, "checklist.discriminating_tests")
    require_unique(state.null_ids, "checklist.nulls")

    return {
        "schema_version": "2.0",
        "checklist_id": checklist["checklist_id"],
        "record_id": checklist["record_id"],
        "valid": not state.errors,
        "status": _checklist_status(state.errors, checklist["hypotheses"]),
        "errors": state.errors,
        "warnings": state.warnings,
        "hypothesis_ids": sorted(
            item["hypothesis_id"] for item in checklist["hypotheses"]
        ),
        "discriminating_test_ids": sorted(state.test_ids),
        "null_ids": sorted(state.null_ids),
        "human_review_status_counts": dict(sorted(state.review_counts.items())),
        "record_cross_check_performed": record is not None,
        "notice": (
            "This audit checks declared falsifiers, rival contrasts, nulls, "
            "controls, and links. It does not prove falsifiability, validate "
            "control assumptions, interpret results, or select a hypothesis."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Audit a bounded local falsification/control JSON checklist without "
            "scientific scoring or candidate selection."
        )
    )
    parser.add_argument("checklist", help="Local falsification/control checklist JSON")
    parser.add_argument(
        "--record", help="Optional local hypothesis record JSON for cross-checks"
    )
    parser.add_argument("-o", "--output", help="Optional local JSON report")
    parser.add_argument(
        "--force", action="store_true", help="Replace an existing output file"
    )
    return parser


def main() -> int:
    """Run the command-line interface."""
    args = build_parser().parse_args()
    try:
        record = (
            load_hypothesis_record(read_json(args.record)) if args.record else None
        )
        report = audit(load_checklist(read_json(args.checklist)), record)
        write_json_report(report, args.output, force=args.force)
        return 0 if report["valid"] else 1
    except ValidationError as exc:
        return error_exit(exc)


if __name__ == "__main__":
    raise SystemExit(main())
