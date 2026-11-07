"""Validate brainstorming idea and assumption registers structurally."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from _common import (
    MAX_ITEMS,
    CliError,
    emit_json,
    read_json,
    require_identifier,
    require_iso_date,
    require_text,
)

ORIGINS = {"human", "ai-assisted", "literature-inspired", "mixed", "other"}
RECORDED_STAGES = {"independent", "discussion", "post-check"}
EVIDENCE_STATUSES = {
    "not-checked",
    "search-incomplete",
    "support-located",
    "challenge-located",
    "mixed",
    "no-direct-evidence-located",
}
IDEA_STATUSES = {
    "candidate",
    "revised",
    "deferred",
    "paused",
    "stopped",
    "advanced-to-review",
}
ASSUMPTION_CATEGORIES = {
    "causal",
    "mechanistic",
    "measurement",
    "sampling",
    "operational",
    "statistical",
    "feasibility",
    "ethical",
    "value",
    "other",
}
ASSUMPTION_STATUSES = {
    "untested",
    "partially-supported",
    "challenged",
    "refuted",
    "not-applicable",
}
_AI_ORIGINS = {"ai-assisted", "mixed"}
_MSG_LIST = "must be a list"
_MSG_OBJECT = "must be an object"
_PATH_PARTICIPANTS = "$.session.participant_ids"
_PATH_ASSUMPTIONS = "$.assumptions"
_PATH_IDEAS = "$.ideas"


def _issue(path: str, message: str) -> dict[str, str]:
    """Build an issue record with a JSON path and message."""
    return {"path": path, "message": message}


def _normalized_statement(value: str) -> str:
    """Normalize only exact text features; this is not semantic matching."""

    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"\s+", " ", normalized).strip()


def _list_field(
    record: dict[str, Any],
    field: str,
    path: str,
    errors: list[dict[str, str]],
    *,
    required: bool = True,
) -> list[Any]:
    """Return a list-valued field, recording an error and truncating when invalid."""
    value = record.get(field)
    if value is None and not required:
        return []
    if not isinstance(value, list):
        errors.append(_issue(f"{path}.{field}", _MSG_LIST))
        return []
    if len(value) > MAX_ITEMS:
        errors.append(
            _issue(
                f"{path}.{field}",
                f"has {len(value)} items; limit is {MAX_ITEMS}",
            )
        )
        return value[:MAX_ITEMS]
    return value


def _check_text(
    value: Any,
    path: str,
    errors: list[dict[str, str]],
    *,
    maximum: int = 10_000,
    allow_empty: bool = False,
) -> str | None:
    """Validate a text value, recording an error and returning None when invalid."""
    try:
        return require_text(
            value,
            path,
            maximum=maximum,
            allow_empty=allow_empty,
        )
    except CliError as exc:
        errors.append(_issue(path, str(exc)))
        return None


def _check_id(
    value: Any,
    path: str,
    errors: list[dict[str, str]],
) -> str | None:
    """Validate an identifier, recording an error and returning None when invalid."""
    try:
        return require_identifier(value, path)
    except CliError as exc:
        errors.append(_issue(path, str(exc)))
        return None


def _check_string_list(
    values: list[Any],
    path: str,
    errors: list[dict[str, str]],
    *,
    identifiers: bool = False,
) -> list[str]:
    """Validate each list item as an identifier or short text and keep the valid ones."""
    result: list[str] = []
    for index, value in enumerate(values):
        item_path = f"{path}[{index}]"
        checked = (
            _check_id(value, item_path, errors)
            if identifiers
            else _check_text(value, item_path, errors, maximum=2_000)
        )
        if checked is not None:
            result.append(checked)
    return result


def _check_choice(
    value: Any, allowed: set[str], path: str, errors: list[dict[str, str]]
) -> None:
    """Record an error when a value is not one of the allowed choices."""
    if value not in allowed:
        errors.append(_issue(path, f"must be one of {sorted(allowed)}"))


def _check_optional_date(
    record: dict[str, Any], path: str, errors: list[dict[str, str]]
) -> None:
    """Validate the optional ``date`` field of a record as an ISO date."""
    if record.get("date") is None:
        return
    try:
        require_iso_date(record["date"], f"{path}.date")
    except CliError as exc:
        errors.append(_issue(f"{path}.date", str(exc)))


def _check_unique_id(
    identifier: str | None,
    path: str,
    seen: set[str],
    label: str,
    errors: list[dict[str, str]],
) -> None:
    """Record a duplicate-ID error and remember the identifier."""
    if identifier is None:
        return
    if identifier in seen:
        errors.append(_issue(path, f"duplicate {label} ID"))
    seen.add(identifier)


def _check_references(
    members: list[str],
    known: set[str],
    path: str,
    errors: list[dict[str, str]],
) -> None:
    """Record an error for every member that is not a known idea ID."""
    for member in members:
        if member not in known:
            errors.append(_issue(path, f"references missing idea ID {member!r}"))


def _bounded_required_list(
    document: dict[str, Any], key: str, path: str, errors: list[dict[str, str]]
) -> list[Any]:
    """Return a required top-level list, recording type/limit errors and truncating."""
    value = document.get(key)
    if not isinstance(value, list):
        errors.append(_issue(path, _MSG_LIST))
        return []
    if len(value) > MAX_ITEMS:
        errors.append(
            _issue(path, f"has {len(value)} items; limit is {MAX_ITEMS}")
        )
        return value[:MAX_ITEMS]
    return value


def _optional_list(
    document: dict[str, Any], key: str, errors: list[dict[str, str]]
) -> list[Any] | None:
    """Return an optional top-level list, or None after recording a type/limit error."""
    value = document.get(key, [])
    path = f"$.{key}"
    if not isinstance(value, list):
        errors.append(_issue(path, "must be a list when present"))
        return None
    if len(value) > MAX_ITEMS:
        errors.append(_issue(path, f"limit is {MAX_ITEMS}"))
        return None
    return value


def _validate_session(session: Any, errors: list[dict[str, str]]) -> set[str]:
    """Validate the session block and return its participant IDs."""
    if not isinstance(session, dict):
        errors.append(_issue("$.session", _MSG_OBJECT))
        return set()
    _check_id(session.get("id"), "$.session.id", errors)
    _check_text(session.get("title"), "$.session.title", errors, maximum=200)
    _check_text(
        session.get("question"),
        "$.session.question",
        errors,
        maximum=2_000,
    )
    raw_participants = _list_field(session, "participant_ids", "$.session", errors)
    participant_list = _check_string_list(
        raw_participants,
        _PATH_PARTICIPANTS,
        errors,
        identifiers=True,
    )
    if not participant_list:
        errors.append(
            _issue(_PATH_PARTICIPANTS, "must contain at least one participant ID")
        )
    if len(set(participant_list)) != len(participant_list):
        errors.append(_issue(_PATH_PARTICIPANTS, "participant IDs must be unique"))
    _check_optional_date(session, "$.session", errors)
    return set(participant_list)


def _validate_assumption(
    assumption: Any,
    path: str,
    participant_ids: set[str],
    assumption_ids: set[str],
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    """Validate one assumption record."""
    if not isinstance(assumption, dict):
        errors.append(_issue(path, _MSG_OBJECT))
        return
    assumption_id = _check_id(assumption.get("id"), f"{path}.id", errors)
    _check_unique_id(assumption_id, f"{path}.id", assumption_ids, "assumption", errors)
    _check_text(assumption.get("statement"), f"{path}.statement", errors)
    _check_choice(
        assumption.get("category"),
        ASSUMPTION_CATEGORIES,
        f"{path}.category",
        errors,
    )
    status = assumption.get("status")
    _check_choice(status, ASSUMPTION_STATUSES, f"{path}.status", errors)
    _check_text(
        assumption.get("test_or_check"),
        f"{path}.test_or_check",
        errors,
        maximum=2_000,
    )
    owner = _check_id(assumption.get("owner_id"), f"{path}.owner_id", errors)
    if owner is not None and participant_ids and owner not in participant_ids:
        errors.append(_issue(f"{path}.owner_id", "is not listed as a participant"))
    evidence_refs = _list_field(assumption, "evidence_refs", path, errors)
    clean_evidence_refs = _check_string_list(
        evidence_refs,
        f"{path}.evidence_refs",
        errors,
    )
    if status not in {None, "untested", "not-applicable"} and not clean_evidence_refs:
        warnings.append(
            _issue(
                f"{path}.evidence_refs",
                "non-untested status has no recorded evidence reference",
            )
        )


def _check_contributors(
    provenance: dict[str, Any],
    path: str,
    participant_ids: set[str],
    errors: list[dict[str, str]],
) -> None:
    """Validate contributor IDs: at least one, and each a known participant."""
    contributors = _check_string_list(
        _list_field(provenance, "contributor_ids", f"{path}.provenance", errors),
        f"{path}.provenance.contributor_ids",
        errors,
        identifiers=True,
    )
    if not contributors:
        errors.append(
            _issue(
                f"{path}.provenance.contributor_ids",
                "must contain at least one contributor ID",
            )
        )
    for contributor in contributors:
        if participant_ids and contributor not in participant_ids:
            errors.append(
                _issue(
                    f"{path}.provenance.contributor_ids",
                    f"{contributor!r} is not listed as a participant",
                )
            )


def _check_ai_tool_and_sources(
    provenance: dict[str, Any],
    path: str,
    origin: Any,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    """Validate source references and the AI-tool field against the recorded origin."""
    source_refs = _check_string_list(
        _list_field(provenance, "source_refs", f"{path}.provenance", errors),
        f"{path}.provenance.source_refs",
        errors,
    )
    ai_tool = provenance.get("ai_tool")
    if origin in _AI_ORIGINS:
        _check_text(ai_tool, f"{path}.provenance.ai_tool", errors, maximum=500)
    elif ai_tool is not None and ai_tool != "":
        warnings.append(
            _issue(
                f"{path}.provenance.ai_tool",
                "AI tool is recorded but origin is not AI-assisted or mixed",
            )
        )
    if origin == "literature-inspired" and not source_refs:
        errors.append(
            _issue(
                f"{path}.provenance.source_refs",
                "literature-inspired ideas require at least one source reference",
            )
        )


def _validate_provenance(
    idea: dict[str, Any],
    path: str,
    participant_ids: set[str],
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> bool:
    """Validate an idea's provenance block; return whether its origin involves AI."""
    provenance = idea.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(_issue(f"{path}.provenance", _MSG_OBJECT))
        provenance = {}
    origin = provenance.get("origin")
    _check_choice(origin, ORIGINS, f"{path}.provenance.origin", errors)
    _check_choice(
        provenance.get("recorded_stage"),
        RECORDED_STAGES,
        f"{path}.provenance.recorded_stage",
        errors,
    )
    _check_contributors(provenance, path, participant_ids, errors)
    _check_ai_tool_and_sources(provenance, path, origin, errors, warnings)
    return origin in _AI_ORIGINS


@dataclass
class _IdeaTracker:
    """Cross-idea state gathered while validating the idea list."""

    idea_ids: set[str] = field(default_factory=set)
    statements: defaultdict[str, list[str]] = field(
        default_factory=lambda: defaultdict(list)
    )
    assumption_references: set[str] = field(default_factory=set)
    ai_assisted_count: int = 0


def _validate_idea_links(
    idea: dict[str, Any],
    path: str,
    tracker: _IdeaTracker,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    """Validate an idea's assumption links, predictions, uncertainties and statuses."""
    linked_assumptions = _check_string_list(
        _list_field(idea, "assumption_ids", path, errors),
        f"{path}.assumption_ids",
        errors,
        identifiers=True,
    )
    tracker.assumption_references.update(linked_assumptions)
    if not linked_assumptions:
        warnings.append(
            _issue(f"{path}.assumption_ids", "idea has no explicit linked assumptions")
        )

    _check_string_list(
        _list_field(idea, "predicted_observations", path, errors),
        f"{path}.predicted_observations",
        errors,
    )
    uncertainties = _check_string_list(
        _list_field(idea, "uncertainties", path, errors),
        f"{path}.uncertainties",
        errors,
    )
    if not uncertainties:
        warnings.append(
            _issue(f"{path}.uncertainties", "idea has no recorded uncertainty")
        )
    _check_choice(
        idea.get("evidence_status"), EVIDENCE_STATUSES, f"{path}.evidence_status", errors
    )
    _check_choice(idea.get("status"), IDEA_STATUSES, f"{path}.status", errors)


def _validate_idea(
    idea: Any,
    path: str,
    participant_ids: set[str],
    tracker: _IdeaTracker,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    """Validate one idea record and update the cross-idea tracker."""
    if not isinstance(idea, dict):
        errors.append(_issue(path, _MSG_OBJECT))
        return
    idea_id = _check_id(idea.get("id"), f"{path}.id", errors)
    _check_unique_id(idea_id, f"{path}.id", tracker.idea_ids, "idea", errors)
    statement = _check_text(idea.get("statement"), f"{path}.statement", errors)
    if statement is not None and idea_id is not None:
        tracker.statements[_normalized_statement(statement)].append(idea_id)

    if _validate_provenance(idea, path, participant_ids, errors, warnings):
        tracker.ai_assisted_count += 1
    _validate_idea_links(idea, path, tracker, errors, warnings)


def _check_cross_references(
    tracker: _IdeaTracker,
    assumption_ids: set[str],
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    """Warn on duplicate statements and cross-check idea/assumption links."""
    for normalized, duplicate_ids in sorted(tracker.statements.items()):
        if normalized and len(duplicate_ids) > 1:
            warnings.append(
                _issue(
                    _PATH_IDEAS,
                    "exact-after-case/whitespace/Unicode normalization duplicate "
                    f"text for IDs {sorted(duplicate_ids)}; this is not a claim "
                    "of semantic equivalence",
                )
            )

    for missing_id in sorted(tracker.assumption_references - assumption_ids):
        errors.append(
            _issue(
                "$.ideas[*].assumption_ids",
                f"references missing assumption ID {missing_id!r}",
            )
        )
    for unlinked_id in sorted(assumption_ids - tracker.assumption_references):
        warnings.append(
            _issue(
                _PATH_ASSUMPTIONS,
                f"assumption {unlinked_id!r} is not linked from any idea",
            )
        )


def _validate_clusters(
    clusters: list[Any], idea_ids: set[str], errors: list[dict[str, str]]
) -> None:
    """Validate the optional idea clusters."""
    cluster_ids: set[str] = set()
    for index, cluster in enumerate(clusters):
        path = f"$.clusters[{index}]"
        if not isinstance(cluster, dict):
            errors.append(_issue(path, _MSG_OBJECT))
            continue
        cluster_id = _check_id(cluster.get("id"), f"{path}.id", errors)
        _check_unique_id(cluster_id, f"{path}.id", cluster_ids, "cluster", errors)
        _check_text(cluster.get("relation"), f"{path}.relation", errors)
        members = _check_string_list(
            _list_field(cluster, "idea_ids", path, errors),
            f"{path}.idea_ids",
            errors,
            identifiers=True,
        )
        _check_references(members, idea_ids, f"{path}.idea_ids", errors)


def _validate_decisions(
    decisions: list[Any], idea_ids: set[str], errors: list[dict[str, str]]
) -> None:
    """Validate the optional decision log."""
    decision_ids: set[str] = set()
    for index, decision in enumerate(decisions):
        path = f"$.decision_log[{index}]"
        if not isinstance(decision, dict):
            errors.append(_issue(path, _MSG_OBJECT))
            continue
        decision_id = _check_id(
            decision.get("decision_id"), f"{path}.decision_id", errors
        )
        _check_unique_id(
            decision_id, f"{path}.decision_id", decision_ids, "decision", errors
        )
        _check_optional_date(decision, path, errors)
        candidates = _check_string_list(
            _list_field(decision, "candidate_ids", path, errors),
            f"{path}.candidate_ids",
            errors,
            identifiers=True,
        )
        _check_references(candidates, idea_ids, f"{path}.candidate_ids", errors)
        _check_text(decision.get("decision"), f"{path}.decision", errors)
        _check_text(decision.get("rationale"), f"{path}.rationale", errors)


def validate_register(document: Any) -> dict[str, Any]:
    """Return a deterministic structural validation report."""

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    if not isinstance(document, dict):
        return {
            "valid": False,
            "errors": [_issue("$", "top-level JSON value must be an object")],
            "warnings": [],
            "statistics": {},
            "limitations": [
                (
                    "Structural validation cannot establish truth, novelty, "
                    "feasibility, ethics approval, or scientific validity."
                )
            ],
        }

    if document.get("schema_version") != "1.1":
        warnings.append(
            _issue(
                "$.schema_version",
                "expected schema version '1.1'; unknown fields are not rejected",
            )
        )

    participant_ids = _validate_session(document.get("session"), errors)

    assumptions_raw = _bounded_required_list(
        document, "assumptions", _PATH_ASSUMPTIONS, errors
    )
    assumption_ids: set[str] = set()
    for index, assumption in enumerate(assumptions_raw):
        _validate_assumption(
            assumption,
            f"$.assumptions[{index}]",
            participant_ids,
            assumption_ids,
            errors,
            warnings,
        )

    ideas_raw = _bounded_required_list(document, "ideas", _PATH_IDEAS, errors)
    tracker = _IdeaTracker()
    for index, idea in enumerate(ideas_raw):
        _validate_idea(
            idea, f"$.ideas[{index}]", participant_ids, tracker, errors, warnings
        )
    _check_cross_references(tracker, assumption_ids, errors, warnings)

    clusters = _optional_list(document, "clusters", errors)
    if clusters is not None:
        _validate_clusters(clusters, tracker.idea_ids, errors)

    decisions = _optional_list(document, "decision_log", errors)
    if decisions is not None:
        _validate_decisions(decisions, tracker.idea_ids, errors)

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "statistics": {
            "participants": len(participant_ids),
            "ideas": len(ideas_raw),
            "assumptions": len(assumptions_raw),
            "ai_assisted_or_mixed_ideas": tracker.ai_assisted_count,
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "limitations": [
            (
                "Validation is structural and deterministic; it does not verify "
                "claims, citations, novelty, feasibility, or scientific validity."
            ),
            (
                "Exact normalized-text duplicate warnings do not assert semantic "
                "equivalence."
            ),
            (
                "A valid register is not ethics, biosafety, regulatory, clinical, "
                "or institutional approval."
            ),
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Validate the structure, provenance, links, and bounded fields in a "
            "brainstorming JSON register. No network or LLM calls are made."
        )
    )
    parser.add_argument("input", help="Session/register .json file")
    parser.add_argument(
        "--output",
        help="Optional validation-report .json file in an existing directory",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return exit status 1 for warnings as well as errors",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Explicitly replace an existing regular output file",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run register validation."""

    args = build_parser().parse_args(argv)
    try:
        _, document = read_json(args.input, label="register")
        report = validate_register(document)
        emit_json(report, args.output, force=args.force)
    except CliError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not report["valid"] or (args.strict and report["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
