#!/usr/bin/env python3
"""Executable Alignment Gate (Gate 1.5).

Deterministic implementation of shared/alignment_gate_protocol.md checks A1-D3
over a Course Passport. Read-only: reports findings, never edits the passport
(auditor discipline — see course-designer/agents/alignment_auditor_agent.md).

Usage:
  python3 scripts/check_alignment_gate.py path/to/course_passport.yaml [--json]

Exit codes: 0 = PASS / PASS-WITH-WARNINGS · 1 = FAIL (BLOCK findings) · 2 = error

Implementation notes:
- Run check_passport.py first; this gate assumes a structurally valid passport
  and reports referential breakage as NOT_EVALUABLE rather than duplicating it.
- A5 uses the lenient series rule: for an assessment due in several weeks (e.g.
  a weekly quiz series), the check fires only when the assessment's LAST due
  week still precedes an assessed outcome's first taught week. The strict
  per-occurrence rule would false-positive on every cumulative series.
- Due weeks come from schedule[].assessments_due (authoritative), not from the
  free-text assessment.week field.
- Previously dismissed findings (gates.alignment_gate.findings[] entries with a
  `dismissed` reason) are suppressed when check_id and affected_ids match, per
  protocol: a dismissed warning is never re-raised.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_passport import load_passport  # noqa: E402

BANNED_VERB_RE = re.compile(
    r"^(know|knows|understand|understands|appreciate|appreciates|learn|learns|"
    r"grasp|grasps|realize|realizes|believe|believes|cover|covers|"
    r"be\s+familiar|be\s+aware)\b|^demonstrate\s+(an?\s+)?understanding",
    re.IGNORECASE,
)
LOW_STAKES_MAX = 10     # weight <= this counts as low-stakes (C3)
HIGH_STAKES_MIN = 20    # weight >= this counts as high-stakes (C3)
MAJOR_WEIGHT = 15       # weight >= this counts as a major deliverable (D3)
SINGLE_WEIGHT_CAP = 40  # C2
WORKLOAD_TOLERANCE = 0.25  # D2


def week_num(week_id):
    m = re.match(r"^W(\d+)$", week_id or "")
    return int(m.group(1)) if m else None


def gate_findings(passport):
    """Return (findings, not_evaluable) lists of dicts shaped like passport gate findings."""
    findings, nev = [], []

    def block(check, detail, ids):
        findings.append({"check_id": check, "severity": "BLOCK", "detail": detail,
                         "affected_ids": sorted(set(ids))})

    def warn(check, detail, ids):
        findings.append({"check_id": check, "severity": "WARN", "detail": detail,
                         "affected_ids": sorted(set(ids))})

    def not_evaluable(check, detail):
        nev.append({"check_id": check, "severity": "NOT_EVALUABLE", "detail": detail,
                    "affected_ids": []})

    los = passport.get("learning_outcomes") or []
    plan = passport.get("assessment_plan") or []
    weeks = passport.get("schedule") or []
    a_by_id = {a.get("id"): a for a in plan}
    lo_by_id = {o.get("id"): o for o in los}

    # Due weeks per assessment, from the schedule (authoritative).
    due_weeks = {}
    for w in weeks:
        n = week_num(w.get("id"))
        for aid in w.get("assessments_due") or []:
            if n is not None:
                due_weeks.setdefault(aid, []).append(n)

    # --- A. Constructive alignment triangle ---
    for o in los:
        if not o.get("assessed_by"):
            block("A1", f"{o['id']} has empty assessed_by — outcome is never assessed", [o["id"]])
        if not o.get("taught_in"):
            block("A2", f"{o['id']} has empty taught_in — outcome is never taught", [o["id"]])
    for a in plan:
        if not a.get("outcomes_assessed"):
            block("A3", f"{a['id']} maps to no outcome", [a["id"]])
    for w in weeks:
        if not w.get("outcomes") and w.get("tag") != "logistics":
            warn("A4", f"{w['id']} maps to no outcome and is not tagged logistics", [w["id"]])
    # A5 (lenient series rule — see module docstring)
    for a in plan:
        dws = due_weeks.get(a.get("id"))
        if not dws:
            continue
        last_due = max(dws)
        for lo_id in a.get("outcomes_assessed") or []:
            lo = lo_by_id.get(lo_id)
            taught = [week_num(x) for x in (lo or {}).get("taught_in") or []]
            taught = [t for t in taught if t is not None]
            if lo and taught and last_due < min(taught):
                warn("A5", f"{a['id']} (last due W{last_due}) assesses {lo_id}, "
                           f"first taught W{min(taught)}", [a["id"], lo_id])

    # --- B. Outcome quality ---
    for o in los:
        stmt = (o.get("statement") or "").strip()
        if BANNED_VERB_RE.match(stmt):
            warn("B1", f"{o['id']} uses a non-measurable operative verb: \"{stmt[:60]}…\"", [o["id"]])
        if not o.get("bloom_level"):
            block("B2", f"{o['id']} has no bloom_level", [o["id"]])
    blooms = {o.get("bloom_level") for o in los if o.get("bloom_level")}
    if los and blooms <= {"remember", "understand"}:
        warn("B3", "no outcome above remember/understand — may be right for an intro "
                   "survey course; professor decides", [o["id"] for o in los])
    if los and not (3 <= len(los) <= 8):
        warn("B4", f"{len(los)} outcomes (3-8 typical"
                   f"{'; >12 usually means topics restated as outcomes' if len(los) > 12 else ''})",
             [o["id"] for o in los])

    # --- C. Assessment structure ---
    if plan:
        total = sum(a.get("weight") or 0 for a in plan)
        if abs(total - 100) > 0.01:
            block("C1", f"weights sum to {total}, expected 100", [a["id"] for a in plan])
        for a in plan:
            if (a.get("weight") or 0) > SINGLE_WEIGHT_CAP:
                warn("C2", f"{a['id']} carries {a['weight']}% (> {SINGLE_WEIGHT_CAP}%)", [a["id"]])
        # C3: a low-stakes assessment must be due strictly before the first high-stakes one
        high = [min(due_weeks[a["id"]]) for a in plan
                if (a.get("weight") or 0) >= HIGH_STAKES_MIN and due_weeks.get(a["id"])]
        low = [min(due_weeks[a["id"]]) for a in plan
               if (a.get("weight") or 0) <= LOW_STAKES_MAX and due_weeks.get(a["id"])]
        if high:
            if not due_weeks:
                not_evaluable("C3", "no assessments_due entries in the schedule")
            elif not low or min(low) >= min(high):
                warn("C3", f"first high-stakes assessment (W{min(high)}) is not preceded by "
                           "any low-stakes one — students get no calibration", [])
        # C4: evaluate/create outcomes assessed only by exam/quiz
        for o in los:
            if o.get("bloom_level") in ("evaluate", "create"):
                types = {a_by_id[aid].get("type") for aid in (o.get("assessed_by") or [])
                         if aid in a_by_id}
                if types and types <= {"exam", "quiz"}:
                    warn("C4", f"{o['id']} ({o['bloom_level']}) is assessed only by "
                               f"{sorted(types)} — artifact-level outcomes need "
                               "artifact-producing evidence", [o["id"]])

    # --- D. Workload ---
    wa = passport.get("workload_audit") or {}
    est, target = wa.get("estimated_hours_per_week"), wa.get("credit_hour_target")
    if est is None:
        block("D1", "workload_audit.estimated_hours_per_week not computed", [])
    elif target is None:
        not_evaluable("D2", "credit_hour_target not set — cannot judge range")
    elif target > 0 and abs(est - target) > WORKLOAD_TOLERANCE * target:
        warn("D2", f"estimated {est} h/wk vs target {target} h/wk "
                   f"(outside ±{int(WORKLOAD_TOLERANCE * 100)}%)", [])
    # D3: two major deliverables due the same week
    for w in weeks:
        majors = [aid for aid in (w.get("assessments_due") or [])
                  if aid in a_by_id and (a_by_id[aid].get("weight") or 0) >= MAJOR_WEIGHT]
        if len(majors) >= 2:
            warn("D3", f"{w['id']} has {len(majors)} major deliverables due "
                       f"({', '.join(sorted(majors))})", majors + [w["id"]])

    return findings, nev


def suppress_dismissed(findings, passport):
    """Drop findings whose (check_id, affected_ids) match a previously dismissed entry."""
    dismissed = {
        (f.get("check_id"), tuple(sorted(f.get("affected_ids") or [])))
        for f in ((passport.get("gates") or {}).get("alignment_gate") or {}).get("findings") or []
        if f.get("dismissed")
    }
    kept, suppressed = [], []
    for f in findings:
        key = (f["check_id"], tuple(sorted(f["affected_ids"])))
        (suppressed if key in dismissed else kept).append(f)
    return kept, suppressed


def run(path):
    passport = load_passport(path)
    findings, nev = gate_findings(passport)
    findings, suppressed = suppress_dismissed(findings, passport)
    blocks = [f for f in findings if f["severity"] == "BLOCK"]
    warns = [f for f in findings if f["severity"] == "WARN"]
    verdict = "FAIL" if blocks else ("PASS-WITH-WARNINGS" if warns else "PASS")
    return {"verdict": verdict, "findings": findings, "not_evaluable": nev,
            "suppressed_as_dismissed": suppressed}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("passport", help="path to course_passport.yaml")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        result = run(args.passport)
    except Exception as e:
        print(f"error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"] + result["not_evaluable"]:
            ids = ", ".join(f["affected_ids"])
            print(f"[{f['severity']}] {f['check_id']}: {f['detail']}" + (f" ({ids})" if ids else ""))
        for f in result["suppressed_as_dismissed"]:
            print(f"[dismissed earlier — not re-raised] {f['check_id']}: {f['detail']}")
        print(f"VERDICT: {result['verdict']}")
    return 1 if result["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
