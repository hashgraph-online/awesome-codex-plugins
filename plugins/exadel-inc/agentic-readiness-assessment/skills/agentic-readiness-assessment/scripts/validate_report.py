from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SECTIONS = (
    "Verdict",
    "Run and Scope",
    "Glossary",
    "Readiness Scorecard",
    "Mandatory Gates",
    "What to Fix",
    "What Can Be Delegated Today",
    "What Is Already Good",
    "Surface Resolution",
    "Golden Path",
    "Probe",
    "Commands Executed",
    "Confidence and Limits",
)
RUN_KEYS = (
    "audited_by",
    "prompt_version",
    "started",
    "completed",
    "commit",
    "branch",
    "platform",
    "archetype",
    "scope",
    "baseline_worktree",
    "final_worktree",
    "clean_state_setup",
    "normalized_score",
    "raw_total",
    "applicable_maximum",
    "status",
    "confidence",
    "gates",
)
AREAS = (
    ("Agent guidance and navigation", 10),
    ("Reproducible environment and dependency setup", 10),
    ("Build, package, render, or deliverable validation", 10),
    ("Lint, format check, typecheck, static analysis, or policy validation", 10),
    ("Unit or component tests", 10),
    ("Integration, contract, or functional tests", 5),
    ("Runtime, API, CLI, or local-preview validation", 5),
    ("Browser or UI validation", 5),
    ("Coverage and feedback-loop quality", 5),
    ("CI enforcement and parity with local validation", 10),
    ("Safety, test isolation, artifacts, and cleanup", 5),
    ("Delivery workflow from task through review or PR", 5),
    ("Agent guardrails and permission scoping", 10),
    ("Context economy", 5),
)
FIX_RECORD_FIELDS = ("Problem", "Blocks", "Evidence", "Priority", "Owner", "Target", "Fix", "Verify", "Level")
AREA_STATUSES = ("Verified", "Partial", "Repository-blocked", "N/A")
INDEX_HEADER = "| ID | Priority / Owner | Problem and blocked capability | Fix and target | Verify |"
INDEX_SEPARATOR = "| --- | --- | --- | --- | --- |"
GLOSSARY_TABLE = """| Term | Meaning |
|---|---|
| Area | One of 14 scored readiness dimensions. Each has a weight shown as `Max`. |
| Gate | One of 4 mandatory checks. A gate's result **is** its anchor area's score, not a separate number. Gates 1–3 pass only at full points. |
| Probe | Gate 4. A deliberate small defect introduced and reverted, to test whether the repository's own verification catches a real break. |
| `F-nn` | A Fix Record: one stable ID per problem, holding the finding and its fix together. |
| Priority | P0 stops unattended work and needs a human. P1 lets the agent proceed incorrectly or unvalidated. P2 costs avoidable time or clarity. |
| Owner | Who fixes it: `repo`, `agent-environment` (the agent's image or toolchain), `platform` (org or infra config), or `external-service`. |
| Readiness status | Per area: Verified (full points), Partial (half, rounded down), Repository-blocked (0), or N/A (excluded from the maximum). |
| Verification state | How the evidence was obtained: Executed, Executed (unfrozen fallback), CI-proven, Environment-blocked, Not run: unsafe, or Not applicable. |
| Level | What a fix changes: `code`, `control`, `docs`, or `instructions`. |
| Normalized score | `points earned / applicable maximum * 100`. The applicable maximum is 105 minus the weight of every N/A area, so it is rarely 100. |
| Repository blocker | The repository itself is missing, wrong, unsafe, or contradictory. Counts against readiness. |
| Environment blocker | The repository documents enough, but this audit machine lacked a tool, service, or permission. Caps confidence; never a full zero. |
| Enforced control | Something that actually fails when violated. A rule that lives only in prose is documented guidance, not an enforced control. |
| Negative control | A safety defect such as a permission bypass, allow-all policy, unguarded secret file, or committed plaintext credential. Caps area 13 at 2. |
| Unfrozen fallback | The locked install failed, so a non-mutating unlocked install was used instead. Valid evidence, but caps the setup area at half. |"""


def section(content: str, heading: str) -> str | None:
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", content, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else None


def yaml_block(content: str) -> str | None:
    run_scope = section(content, "Run and Scope")
    if run_scope is None:
        return None
    match = re.search(r"^```yaml\n(.*?)^```$", run_scope, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else None


def integer(yaml: str, key: str, errors: list[str]) -> int | None:
    match = re.search(rf"^{re.escape(key)}:\s*(\d+)\s*$", yaml, re.MULTILINE)
    if not match:
        errors.append(f"invalid Run and Scope integer: {key}")
        return None
    return int(match.group(1))


def allowed_value(yaml: str, key: str, values: tuple[str, ...], errors: list[str]) -> None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", yaml, re.MULTILINE)
    if match and match.group(1) not in values:
        errors.append(f"invalid Run and Scope {key}: {match.group(1)}")


def validate_scorecard(content: str, errors: list[str]) -> tuple[dict[int, int], dict[int, str], dict[int, int], int, int, bool]:
    scorecard = section(content, "Readiness Scorecard")
    scores: dict[int, int] = {}
    statuses: dict[int, str] = {}
    maximums: dict[int, int] = {}
    total = 0
    applicable_maximum = 0
    if scorecard is None:
        return scores, statuses, maximums, total, applicable_maximum, False

    for number, (name, maximum) in enumerate(AREAS, start=1):
        match = re.search(
            rf"^\| {re.escape(name)} \| [^|]* \| ([^|]*) \| ([^|]*) \|",
            scorecard,
            re.MULTILINE,
        )
        if not match:
            errors.append(f"missing scorecard row: {name}")
            continue
        status = match.group(1).strip()
        score = match.group(2).strip()
        statuses[number] = status
        maximums[number] = maximum
        if status not in AREA_STATUSES:
            errors.append(f"invalid status for {name}: {status}")
        expected = {
            "Verified": maximum,
            "Partial": maximum // 2,
            "Repository-blocked": 0,
        }.get(status)
        if status == "N/A":
            if score != "N/A":
                errors.append(f"invalid score for {name}: {score}")
            continue
        applicable_maximum += maximum
        if expected is None or score != f"{expected}/{maximum}":
            errors.append(f"invalid score for {name}: {score}")
            continue
        scores[number] = expected
        total += expected
    negative_controls = re.search(r"^Negative controls:\s*(.+?)\s*$", scorecard, re.MULTILINE)
    if negative_controls is None:
        errors.append("missing negative controls declaration")
        has_negative_control = False
    elif negative_controls.group(1) == "none":
        has_negative_control = False
    elif re.fullmatch(r"F-\d\d(?:, F-\d\d)*", negative_controls.group(1)):
        has_negative_control = True
    else:
        errors.append("invalid negative controls declaration")
        has_negative_control = False
    return scores, statuses, maximums, total, applicable_maximum, has_negative_control


def validate_gates(yaml: str, scores: dict[int, int], errors: list[str]) -> tuple[dict[str, int], str | None]:
    expected = {
        "setup": (2,),
        "deliverable": (3,),
        "verification": (4, 5, 6),
    }
    gate_anchors: dict[str, int] = {}
    for gate, anchors in expected.items():
        match = re.search(
            rf"^  {gate}:\n    anchor:\s*(\d+)\n    score:\s*(\d+)\s*$",
            yaml,
            re.MULTILINE,
        )
        if not match:
            errors.append(f"missing gate entry: {gate}")
            continue
        anchor, score = (int(value) for value in match.groups())
        if anchor not in anchors:
            errors.append(f"invalid gate anchor: {gate}")
            continue
        gate_anchors[gate] = anchor
        if scores.get(anchor) != score:
            errors.append(f"gate {gate} score does not match anchor area {anchor}")

    probe = re.search(r"^  probe:\n    result:\s*(pass|fail|not attempted)\s*$", yaml, re.MULTILINE)
    if not probe:
        errors.append("missing gate entry: probe")
    return gate_anchors, probe.group(1) if probe else None


def validate_overall_status(yaml: str, normalized_score: int | None, scores: dict[int, int], statuses: dict[int, str], maximums: dict[int, int], gate_anchors: dict[str, int], probe: str | None, has_p0: bool, has_negative_control: bool, errors: list[str]) -> None:
    status = re.search(r"^status:\s*(.+?)\s*$", yaml, re.MULTILINE)
    confidence = re.search(r"^confidence:\s*(.+?)\s*$", yaml, re.MULTILINE)
    if not status:
        return
    gates_pass = all(
        statuses.get(anchor) == "Verified" and scores.get(anchor) == maximums.get(anchor)
        for anchor in gate_anchors.values()
    ) and len(gate_anchors) == 3
    gate_blocked = any(statuses.get(anchor) == "Repository-blocked" for anchor in gate_anchors.values())
    ready = normalized_score is not None and normalized_score >= 80 and confidence is not None and confidence.group(1) in ("High", "Medium") and probe == "pass" and gates_pass and not has_p0 and not has_negative_control
    not_ready = normalized_score is not None and (normalized_score < 50 or gate_blocked or probe == "fail" or has_p0)

    if status.group(1) == "Ready" and not ready:
        errors.append("Ready status is not supported by parsed report fields")
    elif status.group(1) == "Partially ready" and (ready or not_ready):
        errors.append("Partially ready status is not supported by parsed report fields")
    elif status.group(1) == "Not ready" and not not_ready:
        errors.append("Not ready status is not supported by parsed report fields")


def split_table_row(row: str) -> list[str]:
    return re.split(r"(?<!\\)\|", row)


def validate_fix_records(content: str, errors: list[str]) -> bool:
    fixes = section(content, "What to Fix")
    if fixes is None:
        return False

    normalized_fixes = fixes.strip()
    if not normalized_fixes.startswith(INDEX_HEADER):
        errors.append("missing What to Fix compact index")
        index_rows: list[str] = []
    else:
        after_header = normalized_fixes[len(INDEX_HEADER):]
        if not after_header.startswith(f"\n{INDEX_SEPARATOR}"):
            errors.append("malformed What to Fix compact index separator")
            index_rows = []
        else:
            index_rows = []
            for line in after_header[len(INDEX_SEPARATOR) + 2:].splitlines():
                if not line:
                    break
                if not line.startswith("|"):
                    break
                index_rows.append(line)

    index_ids: list[str] = []
    for row in index_rows:
        cells = split_table_row(row)
        if len(cells) != 7 or not row.endswith("|"):
            errors.append("malformed What to Fix compact index row")
            continue
        value = cells[1].strip()
        if not re.fullmatch(r"F-\d\d", value):
            errors.append(f"malformed Fix Record index ID: {value}")
        else:
            index_ids.append(value)
    for identifier in set(index_ids):
        if index_ids.count(identifier) != 1:
            errors.append(f"duplicate Fix Record index ID: {identifier}")

    records: list[tuple[str, str]] = []
    declarations = list(re.finditer(r"^### (F-.*)$", fixes, re.MULTILINE))
    for position, declaration in enumerate(declarations):
        identifier = declaration.group(1)
        if not re.fullmatch(r"F-\d\d", identifier):
            errors.append(f"malformed Fix Record declaration: {identifier}")
            continue
        end = declarations[position + 1].start() if position + 1 < len(declarations) else len(fixes)
        records.append((identifier, fixes[declaration.end():end]))

    record_ids = [identifier for identifier, _ in records]
    for identifier in set(index_ids):
        if record_ids.count(identifier) != 1:
            errors.append(f"index Fix Record {identifier} does not have exactly one matching record")
    for identifier in set(record_ids):
        if identifier not in index_ids:
            errors.append(f"Fix Record {identifier} is not declared in the index")

    for identifier, record in records:
        for field in FIX_RECORD_FIELDS:
            if not re.search(rf"^\*\*{re.escape(field)}:\*\*\s+\S", record, re.MULTILINE):
                errors.append(f"{identifier} is missing Fix Record field: {field}")
    return any(re.search(r"^\| F-\d\d \| P0 /", row) for row in index_rows)


def validate(path: Path) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return [f"cannot read report: {path}"]

    errors: list[str] = []
    if not re.search(r"^# Agentic Readiness — .+", content, re.MULTILINE):
        errors.append("missing report title")

    headings = re.findall(r"^## (.+)$", content, re.MULTILINE)
    missing = [heading for heading in SECTIONS if heading not in headings]
    errors.extend(f"missing section: {heading}" for heading in missing)
    if not missing and tuple(headings) != SECTIONS:
        errors.append("sections are not in the required order")

    glossary = section(content, "Glossary")
    normalized_glossary = glossary.strip() if glossary is not None else ""
    anchor_sentence = r"Gate 3 anchor: Area ([456]) — [^\n]+\."
    glossary_anchor: int | None = None
    if glossary is None or not re.search(r"^\| Term \| Meaning \|$", normalized_glossary, re.MULTILINE):
        errors.append("missing glossary table header")
    elif not normalized_glossary.startswith(GLOSSARY_TABLE):
        errors.append("glossary does not match the fixed table")
    elif not normalized_glossary[len(GLOSSARY_TABLE):].strip():
        errors.append("missing Gate 3 anchor sentence")
    else:
        anchor = re.fullmatch(rf"{re.escape(GLOSSARY_TABLE)}\n\n{anchor_sentence}", normalized_glossary)
        if not anchor:
            errors.append("glossary does not match the fixed contract")
        else:
            glossary_anchor = int(anchor.group(1))

    yaml = yaml_block(content)
    if yaml is None:
        errors.append("missing Run and Scope YAML block")
    else:
        top_level_keys = tuple(re.findall(r"^([a-z_]+):", yaml, re.MULTILINE))
        for key in RUN_KEYS:
            if not re.search(rf"^{re.escape(key)}:\s", yaml, re.MULTILINE):
                errors.append(f"missing Run and Scope key: {key}")
        if top_level_keys != RUN_KEYS:
            errors.append("Run and Scope keys are not in the required order")
        allowed_value(yaml, "status", ("Ready", "Partially ready", "Not ready"), errors)
        allowed_value(yaml, "confidence", ("High", "Medium", "Low"), errors)
        scores, area_statuses, area_maximums, scorecard_total, scorecard_maximum, has_negative_control = validate_scorecard(content, errors)
        raw_total = integer(yaml, "raw_total", errors)
        applicable_maximum = integer(yaml, "applicable_maximum", errors)
        normalized_score = integer(yaml, "normalized_score", errors)
        if raw_total is not None and raw_total != scorecard_total:
            errors.append("raw_total does not equal scorecard total")
        if applicable_maximum is not None and applicable_maximum != scorecard_maximum:
            errors.append("applicable_maximum does not equal scorecard maximum")
        if raw_total is not None and applicable_maximum not in (None, 0) and normalized_score is not None:
            if normalized_score != round(raw_total / applicable_maximum * 100):
                errors.append("normalized_score does not match raw_total and applicable_maximum")
        gate_anchors, probe = validate_gates(yaml, scores, errors)
        if glossary_anchor is not None and gate_anchors.get("verification") != glossary_anchor:
            errors.append("Glossary Gate 3 anchor does not match gates.verification.anchor")
        has_p0 = validate_fix_records(content, errors)
        validate_overall_status(yaml, normalized_score, scores, area_statuses, area_maximums, gate_anchors, probe, has_p0, has_negative_control, errors)
        return errors

    validate_fix_records(content, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an agentic-readiness report contract.")
    parser.add_argument("report", type=Path)
    args = parser.parse_args(argv)

    errors = validate(args.report)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
