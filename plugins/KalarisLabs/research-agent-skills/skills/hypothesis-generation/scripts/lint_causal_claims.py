#!/usr/bin/env python3
"""Lexically lint causal versus associational claims in bounded Markdown."""

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
    read_markdown,
    write_json_report,
)

TAG_RE = re.compile(
    r"\[(claim|estimand|identification|confounding|selection|collider|"
    r"reverse-causation):([A-Za-z0-9_.:-]+)\]",
    re.IGNORECASE,
)
CAUSAL_RE = re.compile(
    r"\b(?:causes?|caused|causal\s+(?:effect|impact)|effect\s+of|"
    r"leads?\s+to|results?\s+in|increases?|reduces?|prevents?|improves?|"
    r"worsens?|drives?|mediates?|produces?)\b",
    re.IGNORECASE,
)
ASSOCIATION_RE = re.compile(
    r"\b(?:associated\s+with|association|correlates?\s+with|correlation|"
    r"co-var(?:y|ies|ied)\s+with|predicts?|linked\s+to)\b",
    re.IGNORECASE,
)
CLAIM_TYPES = {"causal", "associational", "descriptive", "predictive", "mechanistic"}
IDENTIFICATION_TYPES = {
    "randomized",
    "quasi_experimental",
    "observational_assumption_dependent",
    "mechanistic_experiment",
    "other_assumption_dependent",
}
RISK_STATES = {"assessed", "unresolved", "not_applicable"}
REQUIRED_CAUSAL_TAGS = (
    "estimand",
    "identification",
    "confounding",
    "selection",
    "collider",
    "reverse-causation",
)


def _finding(code: str, line_number: int) -> dict[str, Any]:
    """Handle finding."""
    return {"code": code, "line": line_number}


_RISK_TAGS = ("confounding", "selection", "collider", "reverse-causation")


@dataclass
class _LintState:
    """Mutable findings and counters accumulated while linting a document."""

    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    claim_counts: Counter[str] = field(default_factory=Counter)
    causal_trigger_lines: int = 0
    association_trigger_lines: int = 0


def _check_claim_type(state: _LintState, claim_type: str, line_number: int) -> None:
    """Validate and count the declared claim type."""
    if not claim_type:
        return
    if claim_type not in CLAIM_TYPES:
        state.errors.append(_finding("INVALID_CLAIM_TYPE", line_number))
    else:
        state.claim_counts[claim_type] += 1


def _check_causal_language(state: _LintState, claim_type: str, line_number: int) -> None:
    """Flag causal wording that is unmarked or attached to a non-causal claim."""
    state.causal_trigger_lines += 1
    if not claim_type:
        state.errors.append(_finding("UNMARKED_CAUSAL_LANGUAGE", line_number))
    elif claim_type not in {"causal", "mechanistic"}:
        state.errors.append(_finding("CAUSAL_LANGUAGE_IN_NONCAUSAL_CLAIM", line_number))


def _check_association_language(
    state: _LintState,
    claim_type: str,
    has_causal_language: bool,
    line_number: int,
) -> None:
    """Warn about unmarked associational wording or an association-only causal tag."""
    state.association_trigger_lines += 1
    if not claim_type:
        state.warnings.append(_finding("UNMARKED_ASSOCIATIONAL_LANGUAGE", line_number))
    elif claim_type == "causal" and not has_causal_language:
        state.warnings.append(
            _finding("CAUSAL_TAG_WITH_ASSOCIATION_ONLY_LANGUAGE", line_number)
        )


def _check_causal_tags(state: _LintState, tags: dict[str, str], line_number: int) -> None:
    """Check the required companion tags of a causal claim."""
    for required_tag in REQUIRED_CAUSAL_TAGS:
        if required_tag not in tags:
            code_tag = required_tag.replace("-", "_").upper()
            state.errors.append(
                _finding(f"CAUSAL_CLAIM_MISSING_{code_tag}_TAG", line_number)
            )
    identification = tags.get("identification", "").casefold()
    if identification and identification not in IDENTIFICATION_TYPES:
        state.errors.append(_finding("INVALID_IDENTIFICATION_TAG", line_number))
    for risk_tag in _RISK_TAGS:
        risk_state = tags.get(risk_tag, "").casefold()
        code_tag = risk_tag.replace("-", "_").upper()
        if risk_state and risk_state not in RISK_STATES:
            state.errors.append(_finding(f"INVALID_{code_tag}_STATE", line_number))
        if risk_state == "unresolved":
            state.warnings.append(_finding(f"UNRESOLVED_{code_tag}_RISK", line_number))


def _lint_line(state: _LintState, stripped: str, line_number: int) -> None:
    """Lint one non-blank, non-heading line outside code fences."""
    matches = [(key.casefold(), value) for key, value in TAG_RE.findall(stripped)]
    key_counts = Counter(key for key, _ in matches)
    for key, count in key_counts.items():
        if count > 1:
            state.errors.append(_finding(f"DUPLICATE_{key.upper()}_TAG", line_number))
    tags = dict(matches)
    claim_type = tags.get("claim", "").casefold()
    has_causal_language = CAUSAL_RE.search(stripped) is not None
    has_association_language = ASSOCIATION_RE.search(stripped) is not None

    _check_claim_type(state, claim_type, line_number)
    if has_causal_language:
        _check_causal_language(state, claim_type, line_number)
    if has_association_language:
        _check_association_language(state, claim_type, has_causal_language, line_number)

    if claim_type == "causal":
        _check_causal_tags(state, tags, line_number)
    elif claim_type and "estimand" in tags:
        state.warnings.append(_finding("ESTIMAND_TAG_ON_NONCAUSAL_CLAIM", line_number))


def lint(markdown: str) -> dict[str, Any]:
    """Lint Markdown for causal and associational claim annotations."""
    state = _LintState()
    in_fence = False

    for line_number, raw_line in enumerate(markdown.splitlines(), start=1):
        stripped = raw_line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped or stripped.startswith("#"):
            continue
        _lint_line(state, stripped, line_number)

    if in_fence:
        state.errors.append(issue("UNCLOSED_MARKDOWN_FENCE", "document"))

    return {
        "schema_version": "2.0",
        "valid": not state.errors,
        "status": "INVALID_CLAIM_MARKUP" if state.errors else "VALID_LEXICAL_LINT",
        "errors": state.errors,
        "warnings": state.warnings,
        "claim_type_counts": dict(sorted(state.claim_counts.items())),
        "causal_trigger_line_count": state.causal_trigger_lines,
        "associational_trigger_line_count": state.association_trigger_lines,
        "notice": (
            "This deterministic lexical lint does not determine whether language "
            "is scientifically causal, whether an estimand is well defined, or "
            "whether identification assumptions hold. Review every flagged and "
            "unflagged claim manually."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Lint bounded local Markdown for causal/associational claim annotations "
            "and emit only rule codes and line numbers."
        )
    )
    parser.add_argument("document", help="Local Markdown document")
    parser.add_argument("-o", "--output", help="Optional local JSON report")
    parser.add_argument(
        "--force", action="store_true", help="Replace an existing output file"
    )
    return parser


def main() -> int:
    """Run the command-line interface."""
    args = build_parser().parse_args()
    try:
        report = lint(read_markdown(args.document))
        write_json_report(report, args.output, force=args.force)
        return 0 if report["valid"] else 1
    except ValidationError as exc:
        return error_exit(exc)


if __name__ == "__main__":
    raise SystemExit(main())
