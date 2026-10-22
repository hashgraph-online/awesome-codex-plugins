#!/usr/bin/env python3
"""Executable Quality & Integrity Gate (Gate 3.5).

Deterministic implementation of the machine-checkable subset of
shared/quality_gate_protocol.md over a Course Passport + its produced artifacts.
Read-only: reports findings, writes nothing (the gate_runner agent persists the verdict).

The Quality Gate is harder to fully automate than the Alignment Gate — several checks
(UDL nuance, inclusion/tone, whether a brief's Criteria are *good*) need human/model
judgment. This script executes the parts a machine can decide and marks the rest
NOT_EVALUABLE, honestly, so the model+professor handle those rather than the gate
pretending to. Closes the gap where Gate 3.5's blocking core (Q1/Q2) was prose-only
while Gate 1.5 was fully executable.

Executable here:
  Q1  policies.ai_use_policy non-empty + names tiers (permitted/disclosed/prohibited)   BLOCK
  Q2  every assessment has ai_resilience in {reviewed, redesigned}                       BLOCK
  Q4  no assessment artifact relies on AI-detection tools (grep)                         WARN
  T1  every project/paper brief artifact has Purpose / Task / Criteria                   BLOCK
  T2  every assessment >=10% weight has a rubric/brief artifact_ref that exists          WARN
  T4  no student-facing artifact has unresolved [NEEDS PROFESSOR INPUT]/[VERIFY]         WARN
  W1  workload_audit present (re-audit hook; reuses Alignment D1)                        WARN
Not script-evaluable (reported NOT_EVALUABLE — handled by gate_runner + professor):
  Q3 resilience adequacy · T3 syllabus-content nuance · U1-U3 UDL · I1-I2 inclusion/tone

Usage: python3 scripts/check_quality_gate.py <passport.yaml> [--json]
Exit: 0 = PASS / PASS-WITH-WARNINGS · 1 = FAIL (BLOCK) · 2 = error
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_passport import load_passport  # noqa: E402
from check_content_markers import artifact_paths, scan  # noqa: E402

TIER_WORDS = re.compile(r"permit|disclos|prohibit|allowed|not allowed|tier", re.I)
DETECTION = re.compile(r"\b(turnitin|gptzero|ai[ -]?detector|detection tool|originality\.ai)\b", re.I)
T2_WEIGHT = 10


def gate_findings(passport, passport_path):
    findings, nev = [], []
    base = Path(passport_path).parent

    def block(c, d, ids=None): findings.append({"check_id": c, "severity": "BLOCK", "detail": d, "affected_ids": ids or []})
    def warn(c, d, ids=None): findings.append({"check_id": c, "severity": "WARN", "detail": d, "affected_ids": ids or []})
    def nevf(c, d): nev.append({"check_id": c, "severity": "NOT_EVALUABLE", "detail": d, "affected_ids": []})

    plan = passport.get("assessment_plan") or []
    pol = passport.get("policies") or {}

    # Q1
    aiu = (pol.get("ai_use_policy") or "").strip()
    if not aiu:
        block("Q1", "policies.ai_use_policy is empty — every course needs a stated AI-use policy")
    elif not TIER_WORDS.search(aiu):
        warn("Q1", "ai_use_policy is present but does not name per-assignment tiers "
                   "(permitted / disclosed / prohibited) — students need the rule and the reason")

    # Q2
    for a in plan:
        if a.get("ai_resilience") not in ("reviewed", "redesigned"):
            block("Q2", f"{a.get('id')} ai_resilience is '{a.get('ai_resilience')}' — the integrity "
                        f"audit has not run on it", [a.get("id")])

    # T2 + Q4 + T1 (artifact-aware)
    for a in plan:
        if (a.get("weight") or 0) >= T2_WEIGHT:
            ref = a.get("artifact_ref")
            if not ref:
                warn("T2", f"{a.get('id')} ({a.get('weight')}%) has no rubric/brief artifact_ref", [a.get("id")])
            elif not (base / ref).exists():
                warn("T2", f"{a.get('id')} artifact_ref '{ref}' is missing on disk", [a.get("id")])
        ref = a.get("artifact_ref")
        if ref and (base / ref).exists():
            text = (base / ref).read_text(encoding="utf-8", errors="ignore")
            if DETECTION.search(text):
                warn("Q4", f"{a.get('id')} artifact mentions an AI-detection tool as an integrity "
                           f"mechanism — the suite does not rely on detection", [a.get("id")])
            if a.get("type") in ("project", "paper") or "brief" in (ref.lower()):
                missing = [s for s in ("purpose", "task", "criteria") if s not in text.lower()]
                if missing:
                    block("T1", f"{a.get('id')} brief ({ref}) is missing TILT section(s): "
                                f"{', '.join(missing)}", [a.get("id")])

    # T4 — unresolved markers in student-facing artifacts
    marks = scan(artifact_paths(passport_path))
    if marks:
        warn("T4", f"{len(marks)} unresolved [NEEDS PROFESSOR INPUT]/[VERIFY] marker(s) across "
                   f"artifacts — fine for drafts, must be 0 at Stage 5 finalize "
                   f"(run check_content_markers.py --strict)")

    # W1 — workload re-audit hook
    if (passport.get("workload_audit") or {}).get("estimated_hours_per_week") is None:
        warn("W1", "workload_audit not populated — re-run the workload estimate against built artifacts")

    # honest NOT_EVALUABLE for the judgment-heavy checks
    nevf("Q3", "resilience adequacy of each ≥20% assessment — gate_runner + professor judge against ai_era_integrity.md")
    nevf("T3", "syllabus help/late/grading nuance — content judgment")
    nevf("U1-U3/I1-I2", "UDL accessibility + inclusion/tone — advisory, content judgment (never block per protocol)")

    return findings, nev


def suppress_dismissed(findings, passport):
    dismissed = {(f.get("check_id"), tuple(sorted(f.get("affected_ids") or [])))
                 for f in ((passport.get("gates") or {}).get("quality_gate") or {}).get("findings") or []
                 if f.get("dismissed")}
    kept, sup = [], []
    for f in findings:
        key = (f["check_id"], tuple(sorted(f["affected_ids"])))
        (sup if key in dismissed else kept).append(f)
    return kept, sup


def run(path):
    passport = load_passport(path)
    findings, nev = gate_findings(passport, path)
    findings, sup = suppress_dismissed(findings, passport)
    blocks = [f for f in findings if f["severity"] == "BLOCK"]
    warns = [f for f in findings if f["severity"] == "WARN"]
    verdict = "FAIL" if blocks else ("PASS-WITH-WARNINGS" if warns else "PASS")
    return {"verdict": verdict, "findings": findings, "not_evaluable": nev, "suppressed_as_dismissed": sup}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("passport")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = run(args.passport)
    except Exception as ex:
        print(f"error: {type(ex).__name__}: {ex}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"] + result["not_evaluable"]:
            ids = ", ".join(f["affected_ids"])
            print(f"[{f['severity']}] {f['check_id']}: {f['detail']}" + (f" ({ids})" if ids else ""))
        print(f"VERDICT: {result['verdict']}")
    return 1 if result["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
