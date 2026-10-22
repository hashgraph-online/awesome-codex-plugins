# Lab {{lab_number}}: {{lab_title}}

**Course:** {{course_code}} · **Due:** {{due_date}} · **Weight:** {{weight}}% of final grade
**Assessment ID:** {{passport_assessment_id}} · **Work mode:** {{individual_or_team}}

## Purpose

{{TILT purpose: which learning outcomes this lab evidences (verbatim from the passport)
and why this skill matters in the discipline — 2–4 honest sentences, no marketing.}}

**Estimated time:** {{time_estimate}} hours
{{basis: pilot-solve time × novice multiplier — students deserve a real number}}

## Setup

{{tested cold-start instructions, verbatim from the starter README — clone/download,
environment build, "run the visible tests" smoke check. Every step here was executed in
a fresh environment on {{verification_date}}.}}

**Environment:** {{language_and_version}} · dependencies pinned in {{env_file_name}}
**Your dataset:** {{data_access_instructions — per-student labs: how each student gets
their own file; include the synthetic-data label here when realism requires it, e.g.
"This dataset is simulated, modeled on <kind of study>."}}

## Tasks

### Stage 1 — {{warmup_title}} (warm-up)

{{what to do; confirms environment + first contact with the data/API}}
**Deliverable:** {{stage_1_deliverable}}

### Stage 2 — {{core_title}} (core)

{{the outcome-bearing work; references stub contracts by name — the docstrings are the
specification}}
**Deliverable:** {{stage_2_deliverable}}

### Stage 3 — {{extension_title}} ({{optional_or_credit}})

{{stretch task, severable from the core}}
**Deliverable:** {{stage_3_deliverable}}

## What to submit

| File | Format | Contents |
|------|--------|----------|
{{submission contract rows — exact filenames, formats, constraints. This table is the
grading surface: files not listed here are not graded; files named differently may not
be found by the grader.}}

{{do-not-modify list: fixed infrastructure files, graded against the originals}}

## Grading

| Component | Points | How assessed |
|-----------|--------|--------------|
{{autograded rows: visible-test points (you can check these yourself before submitting)
+ hidden-test points (announced here: hidden tests exist and cover edge cases beyond
the visible ones)}}
{{judgment rows: rubric pointer → {{rubric_artifact_ref}}}}

Run the visible tests any time: `{{visible_test_command}}`. Passing them all does not
guarantee full marks — they cover the documented examples; hidden tests check the same
contracts on further cases.

## AI use on this lab: Tier {{ai_tier}} — {{tier_label}}

{{tier meaning + the one-line reason, per shared/ai_era_integrity.md — e.g. for D:
"AI assistance permitted; append a disclosure note: which tool, what you asked, what
you changed. Disclosure is never penalized." Your dataset is unique to you — answers
derived from someone else's data will not match yours.}}

## FAQ

{{seeded from the solution_verifier friction log — the questions the pilot solve
predicts, answered before office hours}}

**Questions:** {{where_questions_go}} · {{response_time_norm}}

---

<!-- ============================================================
INSTRUCTOR BLOCK — remove this section before distributing to students
============================================================ -->

## Instructor notes (do not distribute)

**Ground truth:** {{ground_truth_path}} — planted properties, seeds, seed↔student
mapping, generator code. Professor-only; nothing from it appears above this line.

**Time estimate evidence:** pilot solve {{pilot_solve_time}} on {{pilot_date}} ×
{{novice_multiplier}} = {{time_estimate}} h. {{workload_notes}}

**Common-struggle notes:** {{from solution_verifier grading notes — where students
will stall, misconception vs slip signals, acceptable alternative approaches}}

**Safety / equipment:** {{[NEEDS PROFESSOR INPUT: safety procedures and equipment
notes are institution- and lab-specific — supply or delete for non-physical labs]}}

**Verification record:** {{verification_record_path}} — what was executed, when, with
what result: scaffold cold-start, dataset recoverability runs, solution end-to-end,
grader vs solution (pass) and vs unmodified starter (~0). Items not executed in
session are listed there with [VERIFY] markers — check them before release.
