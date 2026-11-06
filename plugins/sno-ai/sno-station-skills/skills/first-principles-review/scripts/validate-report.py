#!/usr/bin/env python3
"""Validate a first-principles review report and its PRD handoff."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
from typing import Any


_extractor_path = Path(__file__).with_name("extract-prd-handoff.py")
_extractor_spec = importlib.util.spec_from_file_location("extract_prd_handoff", _extractor_path)
if _extractor_spec is None or _extractor_spec.loader is None:
    raise RuntimeError(f"cannot load extractor: {_extractor_path}")
_extractor_module = importlib.util.module_from_spec(_extractor_spec)
_extractor_spec.loader.exec_module(_extractor_module)
extract = _extractor_module.extract


SECTIONS = (
    "Scope and Boundary",
    "Research Receipt",
    "True Outcome",
    "Constraint and Assumption Analysis",
    "Premise Ledger",
    "Alternatives",
    "Primary Recommendation",
    "Falsifiers",
    "Owner Decisions",
    "PRD Handoff",
)
DISPOSITIONS = {"PROCEED", "REFRAME", "SIMPLIFY", "REPLACE", "SPLIT", "TEST-FIRST", "STOP"}
CONSTRAINT_CLASSES = {"hard constraint", "owner preference", "inherited assumption"}
PREMISE_STATES = {"evidence-backed", "unproven", "inherited", "falsified"}
RESEARCH_STATES = {"verified", "inference", "unknown"}


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty_string(item) for item in value)


def section_content(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    return match.group(1).strip() if match else ""


def validate_handoff(handoff: dict[str, Any], errors: list[str]) -> None:
    required = {
        "true_problem",
        "constraints",
        "premises",
        "selected_direction",
        "rejected_alternatives",
        "experiments",
        "acceptance_implications",
        "open_owner_decisions",
        "research_receipt",
        "calibration",
    }
    require(required <= handoff.keys(), f"handoff missing fields: {sorted(required - handoff.keys())}", errors)
    require(nonempty_string(handoff.get("true_problem")), "true_problem must be non-empty", errors)

    constraints = handoff.get("constraints")
    require(isinstance(constraints, list), "constraints must be a list", errors)
    if isinstance(constraints, list):
        for index, item in enumerate(constraints):
            require(isinstance(item, dict), f"constraint {index} must be an object", errors)
            if not isinstance(item, dict):
                continue
            require(nonempty_string(item.get("claim")), f"constraint {index} claim is empty", errors)
            require(item.get("classification") in CONSTRAINT_CLASSES, f"constraint {index} classification is invalid", errors)
            require(nonempty_string(item.get("evidence")), f"constraint {index} evidence is empty", errors)
            require(item.get("state") in PREMISE_STATES, f"constraint {index} state is invalid", errors)

    premises = handoff.get("premises")
    require(isinstance(premises, list) and bool(premises), "premises must be non-empty", errors)
    if isinstance(premises, list):
        for index, item in enumerate(premises):
            require(isinstance(item, dict), f"premise {index} must be an object", errors)
            if not isinstance(item, dict):
                continue
            require(nonempty_string(item.get("claim")), f"premise {index} claim is empty", errors)
            require(item.get("state") in PREMISE_STATES, f"premise {index} state is invalid", errors)
            require(nonempty_string(item.get("challenge")), f"premise {index} challenge is empty", errors)
            require(nonempty_string(item.get("result")), f"premise {index} result is empty", errors)

    selected = handoff.get("selected_direction")
    require(isinstance(selected, dict), "selected_direction must be an object", errors)
    if isinstance(selected, dict):
        require(selected.get("disposition") in DISPOSITIONS, "selected disposition is invalid", errors)
        require(nonempty_string(selected.get("recommendation")), "selected recommendation is empty", errors)
        require(nonempty_strings(selected.get("falsifiers")), "selected falsifiers must be non-empty", errors)
        split_outcomes = selected.get("split_outcomes")
        require(
            isinstance(split_outcomes, list) and all(nonempty_string(item) for item in split_outcomes),
            "selected split_outcomes must be a string list",
            errors,
        )
        if selected.get("disposition") == "SPLIT":
            require(len(split_outcomes) >= 2 if isinstance(split_outcomes, list) else False, "SPLIT requires at least two split outcomes", errors)
        else:
            require(split_outcomes == [], "split_outcomes must be empty unless disposition is SPLIT", errors)

    alternatives = handoff.get("rejected_alternatives")
    require(isinstance(alternatives, list), "rejected_alternatives must be a list", errors)
    if isinstance(alternatives, list):
        for index, item in enumerate(alternatives):
            require(
                isinstance(item, dict)
                and nonempty_string(item.get("name"))
                and nonempty_string(item.get("reason")),
                f"rejected alternative {index} is incomplete",
                errors,
            )

    require(nonempty_strings(handoff.get("experiments")), "experiments must be non-empty", errors)
    require(nonempty_strings(handoff.get("acceptance_implications")), "acceptance_implications must be non-empty", errors)
    owner_decisions = handoff.get("open_owner_decisions")
    require(isinstance(owner_decisions, list) and all(nonempty_string(item) for item in owner_decisions), "open_owner_decisions must be a string list", errors)

    receipt = handoff.get("research_receipt")
    require(isinstance(receipt, list) and bool(receipt), "research_receipt must be non-empty", errors)
    if isinstance(receipt, list):
        for index, item in enumerate(receipt):
            require(isinstance(item, dict), f"research item {index} must be an object", errors)
            if not isinstance(item, dict):
                continue
            require(nonempty_string(item.get("source")), f"research item {index} source is empty", errors)
            require(nonempty_string(item.get("finding")), f"research item {index} finding is empty", errors)
            require(item.get("status") in RESEARCH_STATES, f"research item {index} status is invalid", errors)

    calibration = handoff.get("calibration")
    require(isinstance(calibration, dict), "calibration must be an object", errors)
    if isinstance(calibration, dict):
        for key in ("verified_facts", "inferences", "unknowns"):
            value = calibration.get(key)
            require(isinstance(value, list) and all(nonempty_string(item) for item in value), f"calibration.{key} must be a string list", errors)
        require(
            any(calibration.get(key) for key in ("verified_facts", "inferences", "unknowns")),
            "calibration must contain at least one claim",
            errors,
        )


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return [str(error)]

    positions: list[int] = []
    for heading in SECTIONS:
        marker = f"## {heading}"
        count = text.count(marker)
        require(count == 1, f"expected one {marker} section, found {count}", errors)
        positions.append(text.find(marker))
        require(bool(section_content(text, heading)), f"{marker} must not be empty", errors)
    require(positions == sorted(positions) and all(position >= 0 for position in positions), "required sections are out of order", errors)
    require("?" not in re.sub(r"https?://\S+", "", text), "report must not contain questions", errors)
    require("bounded" in section_content(text, "Scope and Boundary").lower(), "scope must say the review is bounded", errors)

    research = section_content(text, "Research Receipt").lower()
    premise = section_content(text, "Premise Ledger").lower()
    require("no research was performed" not in research, "research receipt records zero work", errors)
    require("no premises were challenged" not in premise, "premise ledger records zero work", errors)

    disposition_match = re.search(r"\*\*Disposition:\*\*\s*([A-Z-]+)", section_content(text, "Primary Recommendation"))
    require(bool(disposition_match), "primary recommendation lacks a disposition", errors)
    human_disposition = disposition_match.group(1) if disposition_match else None
    require(human_disposition in DISPOSITIONS, "primary recommendation disposition is invalid", errors)

    try:
        handoff = extract(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        errors.append(str(error))
        return errors
    validate_handoff(handoff, errors)
    selected = handoff.get("selected_direction")
    if isinstance(selected, dict):
        require(selected.get("disposition") == human_disposition, "human and handoff dispositions differ", errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    errors = validate(args.report)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"valid: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
