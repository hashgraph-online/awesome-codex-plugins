# Course Passport (Schema 1)

> **Machine-checkable since v1.1.0:** `ts/shared/course_passport.schema.json` (structure)
> + `ts/scripts/check_passport.py` (P1–P10 cross-reference invariants: id mirrors, weight
> sums, referential integrity) + `ts/scripts/check_alignment_gate.py` (executable Gate
> 1.5). This prose document remains the authoritative contract for meaning; the JSON
> Schema and validators enforce the parts a machine can check, in CI and at runtime.

The Course Passport is the single source of truth that travels through the entire teaching
pipeline. Every skill reads it; every stage appends to it; no skill silently mutates what
another stage wrote. It is the teaching-side analog of a research project's data ledger:
if a claim about the course isn't in the passport, downstream skills must not assume it.

Stored as `course_passport.yaml` in the working directory (or a path the professor chooses
at Stage 0). All skills in this suite check for its presence at startup; when present, they
auto-load it instead of re-asking the professor for context.

## Top-level structure

```yaml
passport_version: "1.0"
course:
  code: "CS 201"                    # institutional course code
  title: "Data Structures"
  discipline: "Computer Science"
  level: "undergraduate-2nd-year"   # free text: year/graduate/professional
  credits: 3
  modality: "in-person"             # in-person | online-sync | online-async | hybrid | flipped
  class_size: 80
  contact_hours_per_week: 3
  weeks: 16
  language_of_instruction: "English"
  prerequisites: ["CS 101"]
  institution_constraints: []       # accreditation requirements, mandated topics, grade policies

term_calendar:                      # the stored academic calendar — ask once, store here; never invent
  start_date: null                  # ISO date of week 1; "what week is it?" computes from this
  end_date: null
  holidays: []                      # [{date|range, name}] — weeks with no class
  exam_weeks: []                    # week ids that are exam/logistics weeks
  add_drop_deadline: null           # ISO date (institutional fact; [NEEDS PROFESSOR INPUT] if unknown)
  withdrawal_deadline: null

learner_profile:                    # who the students actually are — drives every design choice
  prior_knowledge: ""
  motivation_context: ""            # required course vs elective; career goals
  known_difficulties: []            # common misconceptions, struggle points from past iterations
  accessibility_needs: "unknown"    # what accommodations are anticipated
  cohort_evidence: null             # AGGREGATES ONLY from cohort-analyst — never individual rows.
                                    # { instrument, date, n, response_rate, readiness: {concept: dist},
                                    #   misconceptions: {name: prevalence}, source_note }
                                    # Iron rule: no student-identifying data ever (see PII lint, check_passport.py P11)

learning_outcomes:                  # the spine of constructive alignment
  - id: LO1
    statement: "Analyze the time and space complexity of fundamental data structures"
    bloom_level: analyze            # remember | understand | apply | analyze | evaluate | create
    assessed_by: [A1, A3]           # assessment IDs — MUST be non-empty after Alignment Gate
    taught_in: [W2, W3, W4]         # week IDs — MUST be non-empty after Alignment Gate

assessment_plan:
  - id: A1
    type: exam                      # exam | quiz | project | paper | presentation | participation | portfolio | homework
    title: "Midterm Exam"
    weight: 25                      # percent of final grade; all weights sum to 100
    outcomes_assessed: [LO1, LO2]
    week: W8
    ai_resilience: not_reviewed     # not_reviewed | reviewed | redesigned — set by integrity audit
    artifact_ref: null              # path to the produced exam/rubric/brief, once built

schedule:
  - id: W1
    topic: "Course introduction; abstract data types"
    outcomes: [LO1]
    activities: []                  # filled by lesson-builder
    assessments_due: []
    artifact_refs: []               # lesson plans, slides outlines, activity sheets

policies:
  grading_scheme: ""
  late_policy: ""
  ai_use_policy: ""                 # REQUIRED before syllabus finalization — see ai_era_integrity.md
  integrity_policy: ""
  attendance_policy: ""

workload_audit:                     # computed by course-designer schedule_planner at the schedule
                                    # checkpoint; audited by the Alignment Gate (read-only — the gate
                                    # never writes this field, it reads and judges it via check D1/D2)
  estimated_hours_per_week: null
  credit_hour_target: null
  status: not_audited               # not_audited | within_range | overloaded | underloaded
  constants_used: ""                # the estimation constants, shown so the professor can adjust them

gates:
  alignment_gate:                   # Gate 1.5 — see alignment_gate_protocol.md
    status: not_run                 # not_run | pass | fail
    last_run: null
    findings: []
  quality_gate:                     # Gate 3.5 — see quality_gate_protocol.md
    status: not_run
    last_run: null
    findings: []

artifacts:                          # ledger of everything the pipeline produced
  - path: "syllabus.md"
    type: syllabus
    produced_by: course-designer
    stage: 1
    confirmed_by_professor: true    # checkpoint record — nothing advances unconfirmed

iteration_history:                  # cross-semester improvement loop (Stage 6).
                                    # SINGLE WRITER: only iteration_coach (teaching-pipeline
                                    # Stage 6) appends a consolidated entry. Other skills that
                                    # produce evidence (eval-analysis, item-analysis, cohort,
                                    # submission patterns) hand it to iteration_coach rather than
                                    # writing here directly — keeps the ledger one-voiced.
  - term: "2025 Fall"
    changes: []                     # [{change, source_skill, evidence_ref}]
    evidence: ""                    # what evaluation/observation data motivated each change
                                    # (AGGREGATE only — never individual student data)
```

## Iron rules

1. **Append, don't overwrite.** A skill updating the passport adds or amends its own
   stage's fields; it never deletes another stage's entries. Corrections are made by the
   professor at a checkpoint, not silently by an agent.
2. **No invented context.** If a field a skill needs is empty (e.g., `learner_profile`),
   the skill asks the professor — it does not fabricate plausible values. Unknown is a
   legitimate value; a guess recorded as fact is not.
3. **Outcomes are the spine.** Every assessment lists `outcomes_assessed`; every schedule
   week lists `outcomes`. An artifact that maps to no outcome is flagged at the Alignment
   Gate, not quietly accepted.
4. **Checkpoint provenance.** `confirmed_by_professor` is set only when the professor has
   actually confirmed at a checkpoint. Agents never set it preemptively.
5. **Graceful absence.** All skills work standalone without a passport — they simply ask
   for the context they need and offer to create a passport at the end.
