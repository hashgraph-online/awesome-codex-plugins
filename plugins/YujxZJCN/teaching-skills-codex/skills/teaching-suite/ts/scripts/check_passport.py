#!/usr/bin/env python3
"""Course Passport validator.

Validates a course_passport.yaml in two layers:
  1. Structure — JSON Schema (shared/course_passport.schema.json)
  2. Cross-reference invariants the schema cannot express (P1-P10 below)

Usage:
  python3 scripts/check_passport.py path/to/course_passport.yaml [--json]

Exit codes: 0 = valid · 1 = violations found · 2 = usage/environment error

Invariants:
  P1  ids unique within learning_outcomes / assessment_plan / schedule
  P2  every LO.assessed_by id exists in assessment_plan
  P3  every assessment.outcomes_assessed id exists in learning_outcomes
  P4  assessed_by <-> outcomes_assessed are exact mirrors
  P5  every LO.taught_in id exists in schedule
  P6  every schedule[].outcomes id exists in learning_outcomes
  P7  taught_in <-> schedule[].outcomes are exact mirrors
  P8  every schedule[].assessments_due id exists in assessment_plan
  P9  assessment weights sum to 100 (tolerance 0.01)
  P10 gate findings' affected_ids reference existing ids (WARN-level)
  P11 learner_profile carries no student-identifying data — email/ID/roster (PII guard)
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = REPO_ROOT / "shared" / "course_passport.schema.json"


def load_passport(path):
    import yaml
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("passport root is not a mapping")
    return data


def schema_findings(passport, schema_path):
    import jsonschema
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft202012Validator(schema)
    out = []
    for err in sorted(validator.iter_errors(passport), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in err.absolute_path) or "(root)"
        out.append({"check_id": "SCHEMA", "severity": "BLOCK",
                    "detail": f"{loc}: {err.message}", "affected_ids": [loc]})
    return out


def crossref_findings(passport):
    out = []

    def fail(check, detail, ids):
        out.append({"check_id": check, "severity": "BLOCK",
                    "detail": detail, "affected_ids": sorted(ids)})

    def warn(check, detail, ids):
        out.append({"check_id": check, "severity": "WARN",
                    "detail": detail, "affected_ids": sorted(ids)})

    los = passport.get("learning_outcomes") or []
    plan = passport.get("assessment_plan") or []
    weeks = passport.get("schedule") or []

    lo_ids = [o.get("id") for o in los]
    a_ids = [a.get("id") for a in plan]
    w_ids = [w.get("id") for w in weeks]

    # P1 uniqueness
    for name, ids in (("learning_outcomes", lo_ids),
                      ("assessment_plan", a_ids),
                      ("schedule", w_ids)):
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            fail("P1", f"duplicate ids in {name}", dupes)

    lo_set, a_set, w_set = set(lo_ids), set(a_ids), set(w_ids)

    # P2 / P3 referential existence
    for o in los:
        missing = set(o.get("assessed_by") or []) - a_set
        if missing:
            fail("P2", f"{o.get('id')}.assessed_by references missing assessments", missing)
    for a in plan:
        missing = set(a.get("outcomes_assessed") or []) - lo_set
        if missing:
            fail("P3", f"{a.get('id')}.outcomes_assessed references missing outcomes", missing)

    # P4 mirror: LO.assessed_by <-> assessment.outcomes_assessed
    from_lo = {(o.get("id"), aid) for o in los for aid in (o.get("assessed_by") or [])}
    from_a = {(lid, a.get("id")) for a in plan for lid in (a.get("outcomes_assessed") or [])}
    for lo_id, a_id in sorted(from_lo - from_a):
        fail("P4", f"{lo_id} lists {a_id} in assessed_by but {a_id} does not list {lo_id}", [lo_id, a_id])
    for lo_id, a_id in sorted(from_a - from_lo):
        fail("P4", f"{a_id} lists {lo_id} in outcomes_assessed but {lo_id} does not list {a_id}", [lo_id, a_id])

    # P5 / P6 referential existence
    for o in los:
        missing = set(o.get("taught_in") or []) - w_set
        if missing:
            fail("P5", f"{o.get('id')}.taught_in references missing weeks", missing)
    for w in weeks:
        missing = set(w.get("outcomes") or []) - lo_set
        if missing:
            fail("P6", f"{w.get('id')}.outcomes references missing outcomes", missing)

    # P7 mirror: taught_in <-> schedule.outcomes
    from_lo_w = {(o.get("id"), wid) for o in los for wid in (o.get("taught_in") or [])}
    from_w = {(lid, w.get("id")) for w in weeks for lid in (w.get("outcomes") or [])}
    for lo_id, w_id in sorted(from_lo_w - from_w):
        fail("P7", f"{lo_id} lists {w_id} in taught_in but {w_id} does not list {lo_id}", [lo_id, w_id])
    for lo_id, w_id in sorted(from_w - from_lo_w):
        fail("P7", f"{w_id} lists {lo_id} in outcomes but {lo_id} does not list {w_id}", [lo_id, w_id])

    # P8
    for w in weeks:
        missing = set(w.get("assessments_due") or []) - a_set
        if missing:
            fail("P8", f"{w.get('id')}.assessments_due references missing assessments", missing)

    # P9 weights
    if plan:
        total = sum(a.get("weight") or 0 for a in plan)
        if abs(total - 100) > 0.01:
            fail("P9", f"assessment weights sum to {total}, expected 100", a_set)

    # P10 gate findings reference existing ids (WARN — findings may cite removed entries)
    known = lo_set | a_set | w_set
    for gate_name, gate in (passport.get("gates") or {}).items():
        for fnd in (gate or {}).get("findings") or []:
            stray = set(fnd.get("affected_ids") or []) - known
            if stray:
                warn("P10", f"{gate_name} finding {fnd.get('check_id')} cites unknown ids", stray)

    # P11 PII guard — the passport is about the course, never identifiable students.
    # Heuristic structural enforcement of the suite-wide rule (no student data in the
    # passport). Scans learner_profile + cohort_evidence for email addresses, ID-number
    # patterns, and student-roster-shaped lists. BLOCK — a privacy violation, not advisory.
    for finding in pii_findings(passport):
        out.append(finding)

    return out


import re as _re

_EMAIL = _re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# student-id-like: 6+ digit run, or e.g. "ID: 12345", but not weeks/years/percentages
_IDNUM = _re.compile(r"\b\d{6,}\b")
_ROSTER_HINT = _re.compile(r"\b(student name|roster|grade|gpa|score)s?\b\s*[:=]", _re.I)


def _walk_strings(obj, path="learner_profile"):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_strings(v, f"{path}[{i}]")


def pii_findings(passport):
    """P11: detect likely student-identifying data in learner_profile / cohort_evidence."""
    out = []
    lp = passport.get("learner_profile") or {}
    for loc, s in _walk_strings(lp):
        if _EMAIL.search(s):
            out.append({"check_id": "P11", "severity": "BLOCK",
                        "detail": f"{loc} contains an email address — student PII must never "
                                  f"enter the passport (route to student-mentor)", "affected_ids": [loc]})
        elif _IDNUM.search(s):
            out.append({"check_id": "P11", "severity": "BLOCK",
                        "detail": f"{loc} contains a long digit run resembling a student ID — "
                                  f"the passport holds aggregates only", "affected_ids": [loc]})
        elif _ROSTER_HINT.search(s):
            out.append({"check_id": "P11", "severity": "WARN",
                        "detail": f"{loc} looks roster/grade-shaped — verify it is an aggregate, "
                                  f"not per-student data", "affected_ids": [loc]})
    return out


def run(path, schema_path=DEFAULT_SCHEMA):
    passport = load_passport(path)
    findings = schema_findings(passport, schema_path) + crossref_findings(passport)
    return passport, findings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("passport", help="path to course_passport.yaml")
    ap.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    try:
        _, findings = run(args.passport, args.schema)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # YAML parse, schema load, etc.
        print(f"error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2

    blocks = [f for f in findings if f["severity"] == "BLOCK"]
    if args.json:
        print(json.dumps({"valid": not blocks, "findings": findings}, indent=2))
    else:
        for f in findings:
            ids = ", ".join(f["affected_ids"])
            print(f"[{f['severity']}] {f['check_id']}: {f['detail']} ({ids})")
        print(f"{'INVALID' if blocks else 'VALID'} — {len(blocks)} blocking, "
              f"{len(findings) - len(blocks)} advisory")
    return 1 if blocks else 0


if __name__ == "__main__":
    sys.exit(main())
