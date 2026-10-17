# Alignment Gate Protocol (Gate 1.5)

The first of two blocking gates in the teaching pipeline. Runs after Stage 1 (DESIGN) and
before Stage 2 (BUILD). Purpose: catch structural defects in the course design while they
are still cheap to fix — before lessons and assessments are built on top of them.

The gate is a deterministic checklist over the Course Passport, followed by a professor
acknowledgment checkpoint. It is **not skippable** inside the pipeline. Individual skills
invoked standalone may offer it as `align-check` mode.

## Checks

### A. Constructive alignment triangle (Pedagogy Foundations §2)

| # | Check | Severity |
|---|-------|----------|
| A1 | Every learning outcome has at least one entry in `assessed_by` | BLOCK |
| A2 | Every learning outcome has at least one entry in `taught_in` | BLOCK |
| A3 | Every assessment's `outcomes_assessed` is non-empty and references existing LO ids | BLOCK |
| A4 | Every schedule week maps to ≥1 outcome (or is explicitly tagged `logistics`, e.g. exam week, review week) | WARN |
| A5 | No outcome is assessed *before* the week it is first taught | WARN |

### B. Outcome quality (Pedagogy Foundations §3)

| # | Check | Severity |
|---|-------|----------|
| B1 | Outcome statements use measurable verbs (no "know", "understand", "appreciate", "be familiar with" as the operative verb) | WARN |
| B2 | `bloom_level` is declared for every outcome | BLOCK |
| B3 | Bloom distribution sanity: a course with zero outcomes above "understand" is flagged for review (may be legitimate in intro survey courses — professor decides) | WARN |
| B4 | Outcome count is reviewable (3–8 typical per course; >12 flagged) | WARN |

### C. Assessment structure (Pedagogy Foundations §5, §10)

| # | Check | Severity |
|---|-------|----------|
| C1 | Assessment weights sum to 100% | BLOCK |
| C2 | No single assessment exceeds 40% of the grade (professor may override with reason, logged) | WARN |
| C3 | At least one low-stakes assessment exists before the first high-stakes one | WARN |
| C4 | Cognitive level of assessment types plausibly covers outcome levels (a "create"-level outcome assessed only by multiple-choice exam → flag) | WARN |

### D. Workload audit (see workload notes below)

| # | Check | Severity |
|---|-------|----------|
| D1 | `workload_audit.estimated_hours_per_week` is present (computed upstream by course-designer `schedule_planner` and persisted at the schedule checkpoint; the gate verifies presence, it does not compute it) | BLOCK (must be present, not that it must be in range) |
| D2 | Estimate within ±25% of the credit-hour convention (≈2 out-of-class hours per contact hour, adjusted for institution norms in `institution_constraints`) | WARN |
| D3 | No week with two major deliverables due simultaneously without professor sign-off | WARN |

**Workload estimation heuristics** (adapted from the Rice University course-workload
estimator approach): reading ≈ 67–500 words/min depending on density and purpose;
problem sets ≈ professor's estimate × 3 for novices; writing ≈ 0.5–5 hrs/page by genre.
When in doubt, present the calculation and let the professor adjust the constants —
`schedule_planner` records the constants used in `workload_audit.constants_used` (the
gate only reads them). Canonical constants live in `ts/shared/workload_constants.md` so the
script, the protocol, and the blueprint template share one source.

## Gate behavior

1. Run all checks. Write findings to `gates.alignment_gate.findings[]` as
   `{check_id, severity, detail, affected_ids}`.
2. **Any BLOCK finding → status `fail`.** The pipeline returns to Stage 1 with the
   findings list. Max 3 fix-and-rerun rounds before escalating the disagreement to the
   professor as a design decision rather than a defect.
3. WARN findings never block. They are presented at the checkpoint with a one-line
   rationale and the Pedagogy Foundations citation; the professor may dismiss each with
   a reason, which is logged in the finding (`dismissed: <reason>`). Dismissed warnings
   are not re-raised in later runs.
4. Professor acknowledgment closes the gate: status `pass`, `last_run` stamped.

## Honesty rules

- Findings cite specific passport entries by id. "Some outcomes may be unassessed" is
  not a finding; "LO4 has empty assessed_by" is.
- The gate checks structure, not merit. It must not editorialize about topic choices,
  discipline conventions, or teaching style.
- If the passport lacks the data to run a check (e.g., no weights yet), report the check
  as NOT_EVALUABLE rather than passing it silently.
