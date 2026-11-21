#!/usr/bin/env python3
"""Check documentation gates without assessing clinical adequacy."""

from __future__ import annotations

import argparse
import sys

from _common import (
    Issue,
    ValidationError,
    error_report,
    load_package,
    print_report,
    report_payload,
    validate_package_structure,
)


_TRANSITION_DOC = "transition_reconciliation_record"
_HANDOFF_DOC = "intended_use_handoff_record"


def _required_text(value: object, path: str, issues: list[Issue]) -> None:
    """Handle required text."""
    if not isinstance(value, str) or not value.strip():
        issues.append(Issue("REQUIRED_VALUE_MISSING", path))


def _required_time(value: object, path: str, issues: list[Issue]) -> None:
    """Handle required time."""
    if value is None:
        issues.append(Issue("REQUIRED_TIME_MISSING", path))


def _flag(issues: list[Issue], condition: object, code: str, path: str) -> None:
    """Append an issue with ``code`` at ``path`` when ``condition`` is truthy."""
    if condition:
        issues.append(Issue(code, path))


def _require_texts(
    container: dict, fields: tuple[str, ...], base: str, issues: list[Issue]
) -> None:
    """Require each named field of ``container`` to be non-blank text, reporting under ``base``."""
    for field in fields:
        _required_text(container[field], f"{base}{field}", issues)


def _check_verification(
    verification: dict, base: str, pending_code: str, issues: list[Issue]
) -> None:
    """Check a verification block for verified status, verifier role and timestamp."""
    _flag(
        issues,
        verification["status"] != "verified",
        pending_code,
        f"{base}.verification.status",
    )
    _required_text(
        verification["verified_by_role"],
        f"{base}.verification.verified_by_role",
        issues,
    )
    _required_time(
        verification["verified_at"],
        f"{base}.verification.verified_at",
        issues,
    )


def _check_document_headers(documents: dict[str, dict], issues: list[Issue]) -> None:
    """Check every document for an unresolved template id and a creation time."""
    for document_type, document in documents.items():
        _flag(
            issues,
            "TEMPLATE" in document["document_id"],
            "TEMPLATE_DOCUMENT_ID_UNRESOLVED",
            f"{document_type}:$.document_id",
        )
        _required_time(
            document["created_at"], f"{document_type}:$.created_at", issues
        )


def _check_source_facts(facts: list[dict], issues: list[Issue]) -> None:
    """Check that source facts exist and each has been verified."""
    _flag(issues, not facts, "SOURCE_FACTS_REQUIRED", "source_fact_manifest:$.facts")
    for index, fact in enumerate(facts):
        _check_verification(
            fact["verification"],
            f"source_fact_manifest:$.facts[{index}]",
            "SOURCE_FACT_VERIFICATION_PENDING",
            issues,
        )


def _check_interventions(interventions: list[dict], issues: list[Issue]) -> None:
    """Check that clinician-authored interventions exist and are authorized and verified."""
    prefix = "clinician_authored_intervention_record:"
    _flag(
        issues,
        not interventions,
        "CLINICIAN_AUTHORED_INTERVENTION_REQUIRED",
        f"{prefix}$.interventions",
    )
    for index, intervention in enumerate(interventions):
        base = f"{prefix}$.interventions[{index}]"
        _flag(
            issues,
            intervention["clinical_decision_status"]
            != "supplied_and_verified_by_authorized_clinician",
            "INTERVENTION_AUTHORIZED_VERIFICATION_PENDING",
            f"{base}.clinical_decision_status",
        )
        _check_verification(
            intervention["verification"],
            base,
            "INTERVENTION_VERIFICATION_PENDING",
            issues,
        )


def _check_planning(planning: dict, issues: list[Issue]) -> None:
    """Check that goals, monitoring items and checkpoints are all recorded."""
    for field, code in (
        ("goals", "GOAL_RECORD_REQUIRED"),
        ("monitoring_items", "MONITORING_RECORD_REQUIRED"),
        ("checkpoints", "CHECKPOINT_RECORD_REQUIRED"),
    ):
        _flag(
            issues,
            not planning[field],
            code,
            f"goals_monitoring_checkpoint_record:$.{field}",
        )


def _check_shared_decisions(decisions: list[dict], issues: list[Issue]) -> None:
    """Check that shared-decision entries exist and are fully documented."""
    prefix = "informed_preference_shared_decision_record:"
    _flag(
        issues,
        not decisions,
        "SHARED_DECISION_RECORD_REQUIRED",
        f"{prefix}$.entries",
    )
    for index, decision in enumerate(decisions):
        base = f"{prefix}$.entries[{index}]"
        _flag(
            issues,
            decision["decision_status"] != "documented_by_authorized_clinician",
            "SHARED_DECISION_DOCUMENTATION_PENDING",
            f"{base}.decision_status",
        )
        _flag(
            issues,
            not decision["benefits_harms_uncertainty_documented"],
            "SHARED_DECISION_ELEMENTS_NOT_DOCUMENTED",
            f"{base}.benefits_harms_uncertainty_documented",
        )
        _require_texts(
            decision,
            ("preference_as_documented", "outcome_as_documented", "documented_by_role"),
            f"{base}.",
            issues,
        )
        _required_time(
            decision["documented_at"],
            f"{base}.documented_at",
            issues,
        )
        _flag(
            issues,
            decision["acknowledgment_status"] == "pending",
            "SHARED_DECISION_ACKNOWLEDGMENT_PENDING",
            f"{base}.acknowledgment_status",
        )


def _check_reconciliation(reconciliation: dict, issues: list[Issue]) -> None:
    """Check the medication reconciliation status and its completion details."""
    base = f"{_TRANSITION_DOC}:$.medication_reconciliation"
    status = reconciliation["status"]
    _flag(
        issues,
        status == "pending_authorized_review",
        "MEDICATION_RECONCILIATION_PENDING",
        f"{base}.status",
    )
    if status == "completed_by_authorized_clinician":
        _flag(
            issues,
            not reconciliation["source_list_fact_ids"],
            "RECONCILIATION_SOURCE_LIST_FACTS_REQUIRED",
            f"{base}.source_list_fact_ids",
        )
        _flag(
            issues,
            not reconciliation["destination_list_fact_ids"],
            "RECONCILIATION_DESTINATION_LIST_FACTS_REQUIRED",
            f"{base}.destination_list_fact_ids",
        )
        _flag(
            issues,
            reconciliation["discrepancy_status"] == "not_assessed",
            "RECONCILIATION_DISCREPANCY_STATUS_PENDING",
            f"{base}.discrepancy_status",
        )
    if status != "pending_authorized_review":
        _required_text(
            reconciliation["completed_by_role"],
            f"{base}.completed_by_role",
            issues,
        )
        _required_time(
            reconciliation["completed_at"],
            f"{base}.completed_at",
            issues,
        )


def _check_transition(transition_document: dict, issues: list[Issue]) -> None:
    """Check the transition record: settings, roles, reconciliation, handoff and unresolved items."""
    transition = transition_document["transition"]
    _require_texts(
        transition,
        (
            "from_setting_as_documented",
            "to_setting_as_documented",
            "responsible_sender_role",
            "responsible_receiver_role",
        ),
        f"{_TRANSITION_DOC}:$.transition.",
        issues,
    )
    _required_time(
        transition["handoff_date"],
        f"{_TRANSITION_DOC}:$.transition.handoff_date",
        issues,
    )
    _check_reconciliation(transition_document["medication_reconciliation"], issues)

    _flag(
        issues,
        not transition_document["handoff_items"],
        "HANDOFF_ITEM_REQUIRED",
        f"{_TRANSITION_DOC}:$.handoff_items",
    )
    for index, item in enumerate(transition_document["handoff_items"]):
        _flag(
            issues,
            item["acknowledgment_status"] == "pending",
            "HANDOFF_ITEM_ACKNOWLEDGMENT_PENDING",
            f"{_TRANSITION_DOC}:$.handoff_items[{index}].acknowledgment_status",
        )
    for index, item in enumerate(transition_document["unresolved_items"]):
        base = f"{_TRANSITION_DOC}:$.unresolved_items[{index}]"
        _flag(
            issues,
            item["status"] == "open_unrouted",
            "UNRESOLVED_ITEM_NOT_ROUTED",
            f"{base}.status",
        )
        if item["status"] != "resolved_by_authorized_professional":
            _required_text(
                item["routed_to_local_role"],
                f"{base}.routed_to_local_role",
                issues,
            )


def _check_privacy_process(
    privacy: dict, data_classification: object, issues: list[Issue]
) -> None:
    """Check privacy attestations, qualified review status and data disposition."""
    base = f"{_HANDOFF_DOC}:$.privacy_process"
    for field in (
        "local_authorization_confirmed",
        "minimum_necessary_confirmed",
        "no_external_tools_confirmed",
        "no_prompt_log_example_copy_confirmed",
    ):
        _flag(
            issues,
            not privacy[field],
            "PRIVACY_PROCESS_ATTESTATION_PENDING",
            f"{base}.{field}",
        )
    _require_texts(
        privacy,
        ("authorized_environment_reference", "retention_policy_reference"),
        f"{base}.",
        issues,
    )
    if data_classification == "synthetic":
        expected_review = {"not_applicable_synthetic", "completed_by_qualified_reviewer"}
    else:
        expected_review = {"completed_by_qualified_reviewer"}
    _flag(
        issues,
        privacy["privacy_review_status"] not in expected_review,
        "QUALIFIED_PRIVACY_REVIEW_PENDING",
        f"{base}.privacy_review_status",
    )
    if privacy["privacy_review_status"] == "completed_by_qualified_reviewer":
        _required_text(
            privacy["privacy_reviewer_role"],
            f"{base}.privacy_reviewer_role",
            issues,
        )
        _required_time(privacy["reviewed_at"], f"{base}.reviewed_at", issues)
    _flag(
        issues,
        privacy["data_disposition_status"] == "pending",
        "DATA_DISPOSITION_PENDING",
        f"{base}.data_disposition_status",
    )


def _check_governance_and_routing(handoff_document: dict, issues: list[Issue]) -> None:
    """Check local governance, emergency routing and reporting-route declarations."""
    governance = handoff_document["local_governance"]
    _require_texts(
        governance,
        (
            "institution_or_organization_reference",
            "clinical_owner_role",
            "records_owner_role",
            "change_control_owner_role",
        ),
        f"{_HANDOFF_DOC}:$.local_governance.",
        issues,
    )
    _flag(
        issues,
        not governance["policy_references"],
        "LOCAL_POLICY_REFERENCE_REQUIRED",
        f"{_HANDOFF_DOC}:$.local_governance.policy_references",
    )
    _require_texts(
        handoff_document["emergency_routing"],
        ("local_process_reference", "verified_by_role"),
        f"{_HANDOFF_DOC}:$.emergency_routing.",
        issues,
    )
    _require_texts(
        handoff_document["reporting_routes"],
        (
            "local_patient_safety_route",
            "product_event_route",
            "privacy_incident_route",
            "responsible_role",
        ),
        f"{_HANDOFF_DOC}:$.reporting_routes.",
        issues,
    )


def _check_package_handoff(
    handoff_document: dict, has_unresolved_items: bool, issues: list[Issue]
) -> None:
    """Check the package handoff, clinician sign-off and release gate."""
    handoff = handoff_document["handoff"]
    _require_texts(
        handoff,
        ("sender_role", "recipient_role"),
        f"{_HANDOFF_DOC}:$.handoff.",
        issues,
    )
    _required_time(
        handoff["sent_at"],
        f"{_HANDOFF_DOC}:$.handoff.sent_at",
        issues,
    )
    _flag(
        issues,
        handoff["acknowledgment_status"] != "acknowledged",
        "PACKAGE_HANDOFF_ACKNOWLEDGMENT_PENDING",
        f"{_HANDOFF_DOC}:$.handoff.acknowledgment_status",
    )
    _flag(
        issues,
        has_unresolved_items and not handoff["unresolved_items_routed"],
        "UNRESOLVED_ITEM_ROUTING_ATTESTATION_PENDING",
        f"{_HANDOFF_DOC}:$.handoff.unresolved_items_routed",
    )

    signoff = handoff_document["clinician_signoff"]
    _flag(
        issues,
        signoff["status"] != "signed",
        "CLINICIAN_SIGNOFF_PENDING",
        f"{_HANDOFF_DOC}:$.clinician_signoff.status",
    )
    _require_texts(
        signoff,
        ("signer_role", "credential_authority_reference"),
        f"{_HANDOFF_DOC}:$.clinician_signoff.",
        issues,
    )
    _required_time(
        signoff["signed_at"],
        f"{_HANDOFF_DOC}:$.clinician_signoff.signed_at",
        issues,
    )

    release = handoff_document["release_gate"]
    _flag(
        issues,
        release["status"] != "released_for_authorized_documentation_handoff",
        "DOCUMENTATION_HANDOFF_RELEASE_BLOCKED",
        f"{_HANDOFF_DOC}:$.release_gate.status",
    )
    _required_text(
        release["released_by_role"],
        f"{_HANDOFF_DOC}:$.release_gate.released_by_role",
        issues,
    )
    _required_time(
        release["released_at"],
        f"{_HANDOFF_DOC}:$.release_gate.released_at",
        issues,
    )
    _flag(
        issues,
        release["blocker_codes"],
        "RELEASE_BLOCKER_CODES_REMAIN",
        f"{_HANDOFF_DOC}:$.release_gate.blocker_codes",
    )


def _check_intended_use_handoff(
    handoff_document: dict, has_unresolved_items: bool, issues: list[Issue]
) -> None:
    """Check every section of the intended-use handoff record."""
    intended = handoff_document["intended_use"]
    _flag(
        issues,
        not intended["intended_users"],
        "INTENDED_USER_REQUIRED",
        f"{_HANDOFF_DOC}:$.intended_use.intended_users",
    )
    _required_text(
        intended["intended_setting"],
        f"{_HANDOFF_DOC}:$.intended_use.intended_setting",
        issues,
    )
    _check_privacy_process(
        handoff_document["privacy_process"],
        handoff_document["data_classification"],
        issues,
    )
    _check_governance_and_routing(handoff_document, issues)
    _check_package_handoff(handoff_document, has_unresolved_items, issues)


def check_completeness(documents: dict[str, dict]) -> dict:
    """Check that every documentation gate in the package is declared and resolved."""
    issues = validate_package_structure(documents)
    if issues:
        return report_payload(
            "documentation_completeness",
            issues,
            counts={"structural_issues": len(issues)},
        )

    _check_document_headers(documents, issues)
    facts = documents["source_fact_manifest"]["facts"]
    _check_source_facts(facts, issues)
    interventions = documents[
        "clinician_authored_intervention_record"
    ]["interventions"]
    _check_interventions(interventions, issues)
    planning = documents["goals_monitoring_checkpoint_record"]
    _check_planning(planning, issues)
    decisions = documents[
        "informed_preference_shared_decision_record"
    ]["entries"]
    _check_shared_decisions(decisions, issues)
    transition_document = documents[_TRANSITION_DOC]
    _check_transition(transition_document, issues)
    _check_intended_use_handoff(
        documents[_HANDOFF_DOC],
        bool(transition_document["unresolved_items"]),
        issues,
    )

    issues.sort(key=lambda item: (item.path, item.code))
    return report_payload(
        "documentation_completeness",
        issues,
        counts={
            "source_facts": len(facts),
            "interventions": len(interventions),
            "goals": len(planning["goals"]),
            "monitoring_items": len(planning["monitoring_items"]),
            "checkpoints": len(planning["checkpoints"]),
            "shared_decision_entries": len(decisions),
            "handoff_items": len(transition_document["handoff_items"]),
            "unresolved_items": len(
                transition_document["unresolved_items"]
            ),
        },
        extra={
            "ready_for_authorized_documentation_handoff": not issues,
            "clinical_completeness_determined": False,
        },
    )


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Check required documentation, review, routing, sign-off, and "
            "handoff declarations. No clinical adequacy is assessed."
        )
    )
    parser.add_argument("package", help="Complete local package directory")
    return parser


def main() -> int:
    """Run the command-line interface."""
    args = build_parser().parse_args()
    try:
        documents, _ = load_package(args.package)
        report = check_completeness(documents)
    except ValidationError as exc:
        report = error_report("documentation_completeness", exc)
    print_report(report)
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
