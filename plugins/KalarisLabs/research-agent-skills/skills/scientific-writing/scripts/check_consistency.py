"""Check numeric and methods-results consistency in a bounded JSON registry."""

from __future__ import annotations

import argparse
import math
import re
from typing import Any

from _common import (
    InputError,
    Issue,
    emit_report,
    is_nonempty_string,
    is_placeholder,
    issue,
    read_json,
    require_list,
    require_object,
    run,
)

TOOL = "check_consistency"
FACT_ID_RE = re.compile(r"^N\d{3,8}$")
METHOD_ID_RE = re.compile(r"^M\d{3,8}$")
RESULT_ID_RE = re.compile(r"^R\d{3,8}$")
OUTCOME_ID_RE = re.compile(r"^O\d{3,8}$")
EVIDENCE_ID_RE = re.compile(r"^E\d{3,8}$")
ANALYSIS_INTENT = {"confirmatory", "exploratory", "descriptive"}
PROTOCOL_STATUS = {
    "prespecified",
    "amended_before_analysis",
    "post_hoc",
    "not_applicable",
}
ROOT_FIELDS = {"schema_version", "numeric_facts", "methods", "results"}
FACT_FIELDS = {
    "fact_id",
    "concept",
    "section",
    "value",
    "unit",
    "numerator",
    "denominator",
    "sample_size",
    "analysis_set",
    "evidence_ids",
}
METHOD_FIELDS = {
    "method_id",
    "name",
    "analysis_intent",
    "protocol_status",
    "outcome_ids",
}
RESULT_FIELDS = {
    "result_id",
    "method_id",
    "outcome_id",
    "analysis_intent",
    "sample_size",
    "evidence_ids",
    "reported_sections",
}


def _is_number(value: Any) -> bool:
    """Return whether number."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _check_fields(
    value: dict[str, Any],
    expected: set[str],
    *,
    location: str,
    issues: list[Issue],
) -> None:
    """Check fields."""
    for key in sorted(set(value) - expected):
        issues.append(
            issue("error", "UNKNOWN_SCHEMA_FIELD", location=location, item_id=key)
        )
    for key in sorted(expected - set(value)):
        issues.append(
            issue("error", "MISSING_SCHEMA_FIELD", location=location, item_id=key)
        )


def _validate_ids(
    values: Any,
    *,
    pattern: re.Pattern[str],
    location: str,
    code: str,
    issues: list[Issue],
) -> list[str]:
    """Validate ids."""
    ids = require_list(values, location)
    valid: list[str] = []
    for raw_value in ids:
        if not isinstance(raw_value, str) or not pattern.fullmatch(raw_value):
            issues.append(issue("error", code, location=location))
        else:
            valid.append(raw_value)
    return valid


_FactSignature = tuple[float, str, str, int | None, float | None, float | None]


def _is_positive_int(value: Any) -> bool:
    """Return whether ``value`` is a positive integer that is not a bool."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _check_ratio(
    fact: dict[str, Any], unit: Any, value: Any, fact_id: str | None, issues: list[Issue]
) -> None:
    """Check a fact's numerator and denominator, including percent agreement."""
    numerator = fact.get("numerator")
    denominator = fact.get("denominator")
    if numerator is None and denominator is None:
        return
    if not _is_number(numerator) or not _is_number(denominator) or denominator <= 0:
        issues.append(issue("error", "INVALID_NUMERATOR_DENOMINATOR", item_id=fact_id))
    elif numerator > denominator:
        issues.append(issue("error", "NUMERATOR_EXCEEDS_DENOMINATOR", item_id=fact_id))
    elif unit == "percent" and _is_number(value):
        expected = 100.0 * float(numerator) / float(denominator)
        if not math.isclose(float(value), expected, rel_tol=0.0, abs_tol=0.05):
            issues.append(issue("error", "PERCENT_DENOMINATOR_MISMATCH", item_id=fact_id))


def _fact_signature(
    fact: dict[str, Any], value: Any
) -> tuple[tuple[str, str], _FactSignature] | None:
    """Return the concept key and comparable signature of a fact, or None if incomplete."""
    concept = fact.get("concept")
    analysis_set = fact.get("analysis_set")
    unit = fact.get("unit")
    section = fact.get("section")
    if not (
        is_nonempty_string(concept)
        and is_nonempty_string(analysis_set)
        and is_nonempty_string(unit)
        and _is_number(value)
        and is_nonempty_string(section)
    ):
        return None
    sample_size = fact.get("sample_size")
    numerator = fact.get("numerator")
    denominator = fact.get("denominator")
    current = (
        float(value),
        str(unit),
        str(section),
        sample_size if _is_positive_int(sample_size) else None,
        float(numerator) if _is_number(numerator) else None,
        float(denominator) if _is_number(denominator) else None,
    )
    return (str(concept), str(analysis_set)), current


def _compare_to_prior(
    prior: _FactSignature, current: _FactSignature, fact_id: str | None, issues: list[Issue]
) -> None:
    """Report cross-section disagreements between two facts about the same concept."""
    if prior[1] != current[1]:
        issues.append(issue("error", "UNIT_MISMATCH", item_id=fact_id))
    elif not math.isclose(prior[0], current[0], rel_tol=0.0, abs_tol=1e-12):
        issues.append(issue("error", "CROSS_SECTION_VALUE_MISMATCH", item_id=fact_id))
    if prior[3] != current[3]:
        issues.append(
            issue("error", "CROSS_SECTION_SAMPLE_SIZE_MISMATCH", item_id=fact_id)
        )
    if prior[4:] != current[4:]:
        issues.append(
            issue("error", "CROSS_SECTION_DENOMINATOR_MISMATCH", item_id=fact_id)
        )


def _check_fact(
    index: int,
    raw_fact: Any,
    seen_ids: set[str],
    by_concept: dict[tuple[str, str], _FactSignature],
    issues: list[Issue],
) -> None:
    """Validate one numeric fact and compare it with earlier facts on the same concept."""
    fact = require_object(raw_fact, f"numeric_facts[{index}]")
    location = f"numeric_facts[{index}]"
    _check_fields(fact, FACT_FIELDS, location=location, issues=issues)
    fact_id = fact.get("fact_id")
    if not isinstance(fact_id, str) or not FACT_ID_RE.fullmatch(fact_id):
        issues.append(issue("error", "INVALID_FACT_ID", location=location))
        fact_id = None
    elif fact_id in seen_ids:
        issues.append(issue("error", "DUPLICATE_FACT_ID", item_id=fact_id))
    else:
        seen_ids.add(fact_id)

    unit = fact.get("unit")
    for key, text in {
        "concept": fact.get("concept"),
        "section": fact.get("section"),
        "unit": unit,
        "analysis_set": fact.get("analysis_set"),
    }.items():
        if not is_nonempty_string(text) or is_placeholder(text):
            issues.append(
                issue("error", "MISSING_FACT_FIELD", location=key, item_id=fact_id)
            )

    value = fact.get("value")
    if not _is_number(value):
        issues.append(issue("error", "INVALID_FACT_VALUE", item_id=fact_id))
    sample_size = fact.get("sample_size")
    if sample_size is not None and not _is_positive_int(sample_size):
        issues.append(issue("error", "INVALID_FACT_SAMPLE_SIZE", item_id=fact_id))

    _check_ratio(fact, unit, value, fact_id, issues)

    evidence_ids = _validate_ids(
        fact.get("evidence_ids"),
        pattern=EVIDENCE_ID_RE,
        location=f"{location}.evidence_ids",
        code="INVALID_FACT_EVIDENCE_ID",
        issues=issues,
    )
    if not evidence_ids:
        issues.append(issue("error", "FACT_WITHOUT_EVIDENCE", item_id=fact_id))

    signature = _fact_signature(fact, value)
    if signature is None:
        return
    key, current = signature
    prior = by_concept.get(key)
    if prior is None:
        by_concept[key] = current
    else:
        _compare_to_prior(prior, current, fact_id, issues)


def validate_numeric_facts(data: dict[str, Any]) -> tuple[list[Issue], int]:
    """Validate numeric facts."""
    issues: list[Issue] = []
    facts = require_list(data.get("numeric_facts"), "numeric_facts")
    seen_ids: set[str] = set()
    by_concept: dict[tuple[str, str], _FactSignature] = {}
    for index, raw_fact in enumerate(facts):
        _check_fact(index, raw_fact, seen_ids, by_concept, issues)
    return issues, len(facts)


def _check_method(
    index: int,
    raw_method: Any,
    methods: dict[str, dict[str, Any]],
    expected_outcomes: dict[str, set[str]],
    issues: list[Issue],
) -> None:
    """Validate one declared method and register it with its expected outcomes."""
    method = require_object(raw_method, f"methods[{index}]")
    _check_fields(
        method,
        METHOD_FIELDS,
        location=f"methods[{index}]",
        issues=issues,
    )
    method_id = method.get("method_id")
    if not isinstance(method_id, str) or not METHOD_ID_RE.fullmatch(method_id):
        issues.append(issue("error", "INVALID_METHOD_ID", location=f"methods[{index}]"))
        return
    if method_id in methods:
        issues.append(issue("error", "DUPLICATE_METHOD_ID", item_id=method_id))
        return
    methods[method_id] = method
    if not is_nonempty_string(method.get("name")) or is_placeholder(method.get("name")):
        issues.append(issue("error", "MISSING_METHOD_NAME", item_id=method_id))
    if method.get("analysis_intent") not in ANALYSIS_INTENT:
        issues.append(
            issue("error", "INVALID_METHOD_ANALYSIS_INTENT", item_id=method_id)
        )
    if method.get("protocol_status") not in PROTOCOL_STATUS:
        issues.append(issue("error", "INVALID_PROTOCOL_STATUS", item_id=method_id))
    outcomes = set(
        _validate_ids(
            method.get("outcome_ids"),
            pattern=OUTCOME_ID_RE,
            location=f"methods[{index}].outcome_ids",
            code="INVALID_METHOD_OUTCOME_ID",
            issues=issues,
        )
    )
    if not outcomes:
        issues.append(issue("error", "METHOD_WITHOUT_OUTCOME", item_id=method_id))
    expected_outcomes[method_id] = outcomes


def _check_result_method(
    result: dict[str, Any],
    result_id: str | None,
    methods: dict[str, dict[str, Any]],
    expected_outcomes: dict[str, set[str]],
    observed_outcomes: dict[str, set[str]],
    issues: list[Issue],
) -> None:
    """Check a result's method link, outcome id and analysis intent."""
    method_id = result.get("method_id")
    outcome_id = result.get("outcome_id")
    if method_id not in methods:
        issues.append(issue("error", "RESULT_WITHOUT_DECLARED_METHOD", item_id=result_id))
        return
    if not isinstance(outcome_id, str) or not OUTCOME_ID_RE.fullmatch(outcome_id):
        issues.append(issue("error", "INVALID_RESULT_OUTCOME_ID", item_id=result_id))
    else:
        observed_outcomes[method_id].add(outcome_id)
        if outcome_id not in expected_outcomes[method_id]:
            issues.append(issue("error", "UNDECLARED_RESULT_OUTCOME", item_id=result_id))
    if result.get("analysis_intent") != methods[method_id].get("analysis_intent"):
        issues.append(issue("error", "ANALYSIS_INTENT_MISMATCH", item_id=result_id))


def _check_result(
    index: int,
    raw_result: Any,
    seen_result_ids: set[str],
    methods: dict[str, dict[str, Any]],
    expected_outcomes: dict[str, set[str]],
    observed_outcomes: dict[str, set[str]],
    issues: list[Issue],
) -> None:
    """Validate one reported result against the declared methods."""
    result = require_object(raw_result, f"results[{index}]")
    _check_fields(
        result,
        RESULT_FIELDS,
        location=f"results[{index}]",
        issues=issues,
    )
    result_id = result.get("result_id")
    if not isinstance(result_id, str) or not RESULT_ID_RE.fullmatch(result_id):
        issues.append(issue("error", "INVALID_RESULT_ID", location=f"results[{index}]"))
        result_id = None
    elif result_id in seen_result_ids:
        issues.append(issue("error", "DUPLICATE_RESULT_ID", item_id=result_id))
    else:
        seen_result_ids.add(result_id)

    _check_result_method(
        result, result_id, methods, expected_outcomes, observed_outcomes, issues
    )

    if not _is_positive_int(result.get("sample_size")):
        issues.append(issue("error", "INVALID_RESULT_SAMPLE_SIZE", item_id=result_id))
    evidence_ids = _validate_ids(
        result.get("evidence_ids"),
        pattern=EVIDENCE_ID_RE,
        location=f"results[{index}].evidence_ids",
        code="INVALID_RESULT_EVIDENCE_ID",
        issues=issues,
    )
    if not evidence_ids:
        issues.append(issue("error", "RESULT_WITHOUT_EVIDENCE", item_id=result_id))
    sections = result.get("reported_sections")
    if (
        not isinstance(sections, list)
        or not sections
        or not all(is_nonempty_string(value) for value in sections)
    ):
        issues.append(
            issue("error", "RESULT_WITHOUT_REPORTED_SECTION", item_id=result_id)
        )


def validate_methods_results(data: dict[str, Any]) -> tuple[list[Issue], int, int]:
    """Validate methods results."""
    issues: list[Issue] = []
    methods: dict[str, dict[str, Any]] = {}
    expected_outcomes: dict[str, set[str]] = {}
    for index, raw_method in enumerate(require_list(data.get("methods"), "methods")):
        _check_method(index, raw_method, methods, expected_outcomes, issues)

    results = require_list(data.get("results"), "results")
    seen_result_ids: set[str] = set()
    observed_outcomes: dict[str, set[str]] = {method_id: set() for method_id in methods}
    for index, raw_result in enumerate(results):
        _check_result(
            index, raw_result, seen_result_ids, methods, expected_outcomes,
            observed_outcomes, issues,
        )

    for method_id, outcomes in expected_outcomes.items():
        for outcome_id in sorted(outcomes - observed_outcomes.get(method_id, set())):
            issues.append(
                issue(
                    "error",
                    "METHOD_OUTCOME_WITHOUT_RESULT",
                    location=method_id,
                    item_id=outcome_id,
                )
            )
    return issues, len(methods), len(results)


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Check a local JSON registry for repeated numeric values, units, "
            "denominators, sample sizes, and declared methods-results mappings."
        )
    )
    parser.add_argument("registry", help="UTF-8 JSON consistency registry")
    return parser


def cli() -> int:
    """Handle cli."""
    args = build_parser().parse_args()
    data = require_object(read_json(args.registry), "consistency_registry")
    root_issues: list[Issue] = []
    _check_fields(data, ROOT_FIELDS, location="root", issues=root_issues)
    if data.get("schema_version") != "1.0":
        raise InputError("unsupported consistency registry version")
    issues, fact_count = validate_numeric_facts(data)
    issues.extend(root_issues)
    method_issues, method_count, result_count = validate_methods_results(data)
    issues.extend(method_issues)
    return emit_report(
        TOOL,
        issues,
        summary={
            "numeric_facts": fact_count,
            "methods": method_count,
            "results": result_count,
        },
    )


if __name__ == "__main__":
    run(TOOL, cli)
