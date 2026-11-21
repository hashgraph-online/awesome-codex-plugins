#!/usr/bin/env python3
"""Check cross-record consistency without clinical interpretation."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import Any

from _common import (
    Issue,
    ValidationError,
    load_package,
    parse_iso_datetime,
    print_report,
    record_ids,
    report_payload,
    validate_package_structure,
    error_report,
)


def _collect_ids(documents: dict[str, dict]) -> list[tuple[str, str]]:
    """Collect ids."""
    values: list[tuple[str, str]] = []

    def collect(records: list, field: str, path: str) -> None:
        """Collect."""
        for index, record in enumerate(records):
            if isinstance(record, dict) and isinstance(record.get(field), str):
                values.append((f"{path}[{index}].{field}", record[field]))

    facts = documents["source_fact_manifest"]["facts"]
    collect(facts, "fact_id", "source_fact_manifest:$.facts")

    interventions = documents[
        "clinician_authored_intervention_record"
    ]["interventions"]
    collect(
        interventions,
        "intervention_id",
        "clinician_authored_intervention_record:$.interventions",
    )
    for index, record in enumerate(interventions):
        collect(
            record["parameters_as_supplied"],
            "parameter_id",
            (
                "clinician_authored_intervention_record:"
                f"$.interventions[{index}].parameters_as_supplied"
            ),
        )

    planning = documents["goals_monitoring_checkpoint_record"]
    collect(
        planning["goals"],
        "goal_id",
        "goals_monitoring_checkpoint_record:$.goals",
    )
    collect(
        planning["monitoring_items"],
        "monitoring_id",
        "goals_monitoring_checkpoint_record:$.monitoring_items",
    )
    collect(
        planning["checkpoints"],
        "checkpoint_id",
        "goals_monitoring_checkpoint_record:$.checkpoints",
    )

    entries = documents[
        "informed_preference_shared_decision_record"
    ]["entries"]
    collect(
        entries,
        "decision_id",
        "informed_preference_shared_decision_record:$.entries",
    )
    for index, record in enumerate(entries):
        collect(
            record["options_as_documented"],
            "option_id",
            (
                "informed_preference_shared_decision_record:"
                f"$.entries[{index}].options_as_documented"
            ),
        )

    transition = documents["transition_reconciliation_record"]
    collect(
        transition["handoff_items"],
        "item_id",
        "transition_reconciliation_record:$.handoff_items",
    )
    collect(
        transition["unresolved_items"],
        "item_id",
        "transition_reconciliation_record:$.unresolved_items",
    )
    return values


def _duplicate_reference_issues(
    value: Any, path: str = "$"
) -> list[Issue]:
    """Handle duplicate reference issues."""
    issues: list[Issue] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            nested_path = f"{path}.{key}"
            if (
                key.endswith("_ids")
                and isinstance(nested, list)
                and len(nested) != len(set(nested))
            ):
                issues.append(Issue("DUPLICATE_REFERENCE_IN_LIST", nested_path))
            issues.extend(_duplicate_reference_issues(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(
                _duplicate_reference_issues(nested, f"{path}[{index}]")
            )
    return issues


_TRANSITION_PREFIX = "transition_reconciliation_record:"
_HANDOFF_PREFIX = "intended_use_handoff_record:"
_RECONCILIATION_PATH = f"{_TRANSITION_PREFIX}$.medication_reconciliation"


def _flag(issues: list[Issue], condition: object, code: str, path: str) -> None:
    """Append an issue with ``code`` at ``path`` when ``condition`` is truthy."""
    if condition:
        issues.append(Issue(code, path))


def _check_document_consistency(
    documents: dict[str, dict],
    subject_ref: object,
    classification: object,
    issues: list[Issue],
) -> None:
    """Check each document's subject, classification and duplicate list references."""
    for document_type, document in documents.items():
        _flag(
            issues,
            document["subject_ref"] != subject_ref,
            "SUBJECT_REFERENCE_MISMATCH",
            f"{document_type}:$.subject_ref",
        )
        _flag(
            issues,
            document["data_classification"] != classification,
            "DATA_CLASSIFICATION_MISMATCH",
            f"{document_type}:$.data_classification",
        )
        issues.extend(
            Issue(issue.code, f"{document_type}:{issue.path}", issue.level)
            for issue in _duplicate_reference_issues(document)
        )


def _check_intervention_dates(interventions: list[dict], issues: list[Issue]) -> None:
    """Flag interventions whose explicit start date falls after their end date."""
    for index, record in enumerate(interventions):
        start = record["start_date"]
        end = record["end_date"]
        _flag(
            issues,
            start is not None
            and end is not None
            and date.fromisoformat(start) > date.fromisoformat(end),
            "INTERVENTION_DATE_ORDER_INVALID",
            f"clinician_authored_intervention_record:$.interventions[{index}]",
        )


def _check_checkpoint_links(
    planning: dict,
    goal_ids: set[str],
    intervention_ids: set[str],
    issues: list[Issue],
) -> None:
    """Flag checkpoints that link to unknown goals or interventions."""
    for index, checkpoint in enumerate(planning["checkpoints"]):
        base = f"goals_monitoring_checkpoint_record:$.checkpoints[{index}]"
        for reference_index, goal_id in enumerate(checkpoint["linked_goal_ids"]):
            _flag(
                issues,
                goal_id not in goal_ids,
                "CHECKPOINT_UNKNOWN_GOAL",
                f"{base}.linked_goal_ids[{reference_index}]",
            )
        for reference_index, intervention_id in enumerate(
            checkpoint["linked_intervention_ids"]
        ):
            _flag(
                issues,
                intervention_id not in intervention_ids,
                "CHECKPOINT_UNKNOWN_INTERVENTION",
                f"{base}.linked_intervention_ids[{reference_index}]",
            )


def _check_reconciliation_consistency(
    reconciliation: dict, issues: list[Issue]
) -> None:
    """Check that the medication reconciliation fields agree with its status."""
    status = reconciliation["status"]
    if status == "pending_authorized_review":
        _flag(
            issues,
            reconciliation["completed_by_role"]
            or reconciliation["completed_at"] is not None,
            "PENDING_RECONCILIATION_HAS_COMPLETION_DATA",
            _RECONCILIATION_PATH,
        )
    elif status == "not_applicable_by_authorized_clinician":
        _flag(
            issues,
            reconciliation["source_list_fact_ids"]
            or reconciliation["destination_list_fact_ids"],
            "NOT_APPLICABLE_RECONCILIATION_HAS_LIST_REFERENCES",
            _RECONCILIATION_PATH,
        )
    elif status == "completed_by_authorized_clinician":
        _flag(
            issues,
            not reconciliation["completed_by_role"]
            or reconciliation["completed_at"] is None,
            "COMPLETED_RECONCILIATION_MISSING_REVIEW",
            _RECONCILIATION_PATH,
        )


def _check_release_consistency(
    handoff_document: dict, classification: object, issues: list[Issue]
) -> None:
    """Check privacy classification and the release gate against sign-off and handoff state."""
    _flag(
        issues,
        handoff_document["privacy_process"]["data_classification"] != classification,
        "PRIVACY_CLASSIFICATION_MISMATCH",
        f"{_HANDOFF_PREFIX}$.privacy_process.data_classification",
    )
    release = handoff_document["release_gate"]
    if release["status"] != "released_for_authorized_documentation_handoff":
        return
    _flag(
        issues,
        handoff_document["clinician_signoff"]["status"] != "signed",
        "RELEASE_WITHOUT_CLINICIAN_SIGNOFF",
        f"{_HANDOFF_PREFIX}$.release_gate.status",
    )
    _flag(
        issues,
        release["blocker_codes"],
        "RELEASE_WITH_BLOCKERS",
        f"{_HANDOFF_PREFIX}$.release_gate.blocker_codes",
    )
    _flag(
        issues,
        handoff_document["handoff"]["acknowledgment_status"] != "acknowledged",
        "RELEASE_WITHOUT_HANDOFF_ACKNOWLEDGMENT",
        f"{_HANDOFF_PREFIX}$.handoff.acknowledgment_status",
    )


def _optional_datetime(value: str | None):
    """Parse an ISO datetime, passing None through unchanged."""
    return parse_iso_datetime(value) if value is not None else None


def _check_timestamp_order(handoff_document: dict, issues: list[Issue]) -> None:
    """Check that sign-off, privacy review, release and handoff timestamps are ordered."""
    signed_at = _optional_datetime(handoff_document["clinician_signoff"]["signed_at"])
    released_at = _optional_datetime(handoff_document["release_gate"]["released_at"])
    sent_at = _optional_datetime(handoff_document["handoff"]["sent_at"])
    reviewed_at = _optional_datetime(handoff_document["privacy_process"]["reviewed_at"])
    _flag(
        issues,
        signed_at and released_at and signed_at > released_at,
        "SIGNOFF_AFTER_RELEASE",
        f"{_HANDOFF_PREFIX}$.release_gate.released_at",
    )
    _flag(
        issues,
        released_at and sent_at and released_at > sent_at,
        "RELEASE_AFTER_HANDOFF_SENT",
        f"{_HANDOFF_PREFIX}$.handoff.sent_at",
    )
    _flag(
        issues,
        reviewed_at and released_at and reviewed_at > released_at,
        "PRIVACY_REVIEW_AFTER_RELEASE",
        f"{_HANDOFF_PREFIX}$.privacy_process.reviewed_at",
    )


def check_consistency(documents: dict[str, dict]) -> dict:
    """Check identifiers, links, classifications, status coherence and explicit date order."""
    issues = validate_package_structure(documents)
    if issues:
        return report_payload(
            "cross_record_consistency",
            issues,
            counts={"structural_issues": len(issues)},
        )

    handoff_document = documents["intended_use_handoff_record"]
    classification = handoff_document["data_classification"]
    _check_document_consistency(
        documents, handoff_document["subject_ref"], classification, issues
    )

    seen: set[str] = set()
    for path, identifier in _collect_ids(documents):
        _flag(issues, identifier in seen, "GLOBAL_RECORD_ID_COLLISION", path)
        seen.add(identifier)

    interventions = documents[
        "clinician_authored_intervention_record"
    ]["interventions"]
    _check_intervention_dates(interventions, issues)

    planning = documents["goals_monitoring_checkpoint_record"]
    goal_ids = record_ids(planning, "goals", "goal_id")
    intervention_ids = record_ids(
        documents["clinician_authored_intervention_record"],
        "interventions",
        "intervention_id",
    )
    _check_checkpoint_links(planning, goal_ids, intervention_ids, issues)
    _check_reconciliation_consistency(
        documents["transition_reconciliation_record"]["medication_reconciliation"],
        issues,
    )
    _check_release_consistency(handoff_document, classification, issues)
    _check_timestamp_order(handoff_document, issues)

    issues.sort(key=lambda item: (item.path, item.code))
    return report_payload(
        "cross_record_consistency",
        issues,
        counts={
            "global_record_ids": len(seen),
            "checkpoints": len(planning["checkpoints"]),
            "interventions": len(interventions),
        },
        extra={
            "clinical_semantics_compared": False,
            "date_intervals_inferred": False,
        },
    )


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Check identifiers, links, classifications, status coherence, and "
            "explicit date order. Clinical text is not compared or interpreted."
        )
    )
    parser.add_argument("package", help="Complete local package directory")
    return parser


def main() -> int:
    """Run the command-line interface."""
    args = build_parser().parse_args()
    try:
        documents, _ = load_package(args.package)
        report = check_consistency(documents)
    except ValidationError as exc:
        report = error_report("cross_record_consistency", exc)
    print_report(report)
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
