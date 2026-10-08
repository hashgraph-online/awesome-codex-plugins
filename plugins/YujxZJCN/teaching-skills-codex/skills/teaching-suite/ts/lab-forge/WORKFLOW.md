---
name: lab-forge
description: "Executable teaching-artifact builder for STEM professors — pipeline Stage 2 extension. 5-agent team that builds lab and programming assignments as working packages: per-student synthetic datasets with planted, recoverable ground truth, starter-code scaffolds that run as shipped, autograders with visible/hidden test splits, and reference solutions produced by solving and verified by executing. Triggers on: lab assignment, programming assignment, problem set code, dataset for students, synthetic data, starter code, autograder, solution notebook, Jupyter, 实验作业, 编程作业, 数据集, 实验数据, 起始代码, 自动评分, 自动批改, 参考答案."
metadata:
  version: "1.0.0"
  last_updated: "2026-06-10"
  status: active
  pipeline_stage: 2
  related_skills:
    - assessment-architect
    - submission-auditor
    - lesson-builder
    - teaching-pipeline
---

# Lab Forge — Executable Teaching-Artifact Team

Builds the artifacts a STEM assignment is actually made of: the dataset students load,
the scaffold they fill in, the tests that grade them, the solution that proves the whole
thing is doable. Where `assessment-architect` writes the brief and the rubric, this skill
builds the *machinery* — and machinery is only real when it runs. Everything this skill
ships was executed in session; verification evidence travels with the package.

> **Prime rule:** executed, not assumed. A starter repo that doesn't compile, a dataset
> whose planted effect the intended analysis can't recover, an autograder the unmodified
> scaffold can pass — each is a defect, found by running, not by review. Verification is
> part of the build, never an optional final step.

## Quick Start

```
Build the Week 6 regression lab for STAT 210 — it's A3 in the passport
给我的机器学习课做一个编程作业：起始代码 + 自动评分
Generate a per-student dataset for the ANOVA lab — 45 students, same difficulty each
Write the autograder for this assignment spec; here's the starter repo
Make 4 variants of last year's pathfinding lab so sections can't share answers
我需要这次实验的参考答案和评分说明
```

## Modes

| Mode | Trigger intent | Output |
|------|---------------|--------|
| `lab` | "Build the lab / programming assignment for…" | Complete package: handout + starter + data + verified solution + grader + verification record |
| `dataset` | "Generate data for…" / per-student data requests | Synthetic dataset(s) with planted, recoverable properties; per-student/per-section variants; professor-only ground-truth doc |
| `starter-code` | "Starter code / scaffold / skeleton for…" | Scaffold repo: structure, stubs with full contracts, fixed vs student zones fenced, runs as shipped |
| `autograder` | "Autograder / tests to grade this" | Test-suite grader: visible tests for students + hidden tests for grading, partial-credit map, submission-auditor-consumable output |
| `solution` | "Reference solution / solution notebook for…" | Solution produced by solving from student-facing materials, verified by execution, + grading notes |
| `variant` | "Make N versions of this lab/dataset" | N difficulty-equivalent variants with the equivalence argument stated and spot-checked |

**Mode dispatch rule:** a request naming a passport assessment loads that entry; a
standalone request intakes context and offers passport write-back at exit (Passport Iron
Rule 5). `autograder` and `solution` without existing student-facing materials redirect
to `lab` — there is nothing honest to grade or solve against yet. Detect intent in any
language.

### Does NOT trigger

| Scenario | Use instead |
|----------|-------------|
| Writing the assignment brief, rubric, or grading criteria themselves | `assessment-architect` `project-brief` / `rubric` |
| Checking student submissions against a standard | `submission-auditor` |
| In-class ungraded exercises and activities | `lesson-builder` |
| Full design → materials → assessment run | `teaching-pipeline` |

## Agent Team (5)

| Agent | Role |
|-------|------|
| `lab_designer_agent` | Designs the lab arc against outcomes: staging, deliverables, submission contract, honest time estimates; safety notes flagged for physical labs |
| `dataset_smith_agent` | Generates synthetic data with planted properties verified recoverable; seeded per-student variation; professor-only ground-truth documentation |
| `starter_code_agent` | Builds scaffold repos that run as shipped: stubs with full contracts, fenced student-work zones, pinned dependencies, tested cold-start README |
| `autograder_agent` | Builds visible + hidden test suites with partial-credit mapping; validates against the verified solution AND the unmodified starter; output feeds submission-auditor |
| `solution_verifier_agent` | Solves the lab cold from student-facing materials only, executing everything; produces solution + grading notes; reports defects rather than patching around them |

## Workflow (`lab` mode)

```
Phase 0  INTAKE      — load the passport assessment entry (outcomes_assessed, weight,
                       week, ai_tier) or intake standalone: outcomes, topics taught,
                       student environment (language, tools, compute), class size.
                       Missing context = ask, don't guess (Passport Iron Rule 2).
Phase 1  DESIGN      — lab_designer drafts the lab arc: what students do, in what
                       order, what they submit (the submission contract), time
                       estimate with evidence
         🧑 checkpoint: arc confirmed — staging, deliverables, and per-student
            variation plan decided here, before anything is built
Phase 2  BUILD       — parallel: dataset_smith (data + ground_truth.md) and
                       starter_code (scaffold + env). Both execute their artifacts
                       before handing off.
Phase 3  SOLVE       — solution_verifier solves the lab from the STUDENT artifacts
                       only — handout, starter, data — executing every step. A lab
                       that can't be completed from its own materials is reported
                       as defective, not quietly repaired (iron rule 2).
Phase 4  GRADE       — autograder built against the verified solution; run against
                       both solution (must pass) and unmodified starter (must score
                       ~0); partial-credit map drawn from the rubric if one exists
Phase 5  PACKAGE     — handout from templates/lab_handout_template.md + run-it-cold
                       test: the README's fresh-environment instructions are
                       actually followed start to finish in a clean environment
         🧑 checkpoint: package confirmed, presented WITH the verification record
            (what ran, when, results) → passport artifact_ref + artifacts[] updated
```

`dataset`, `starter-code`, `autograder`, and `solution` run their agent plus the
verification steps that agent owns, ending in a checkpoint with evidence. `variant` runs
dataset_smith and/or starter_code in variation mode, then solution_verifier spot-solves
a sample of variants before the equivalence argument is presented.

## Iron rules

1. **Executed, not assumed.** Every artifact in the package was run in session — the
   scaffold imported, the data generated and analyzed, the solution executed end to end,
   the grader run against both solution and starter. The verification record (commands,
   outputs, dates) ships with the package. Anything that could not be executed carries
   `[VERIFY: <what to run and expect>]`, never silent confidence.
2. **Solution independence.** The solver works from student-facing materials only —
   never the design notes, never the ground-truth doc. A mismatch between what the
   solver could do and what the design intended is the finding; it goes to the
   checkpoint as a lab defect, and is never patched by quietly editing the solution.
3. **Ground-truth isolation.** Planted effects, generation seeds, seed↔student mappings,
   and expected answer values live in a professor-only `ground_truth.md`. They appear in
   no student-facing artifact — including autograder feedback strings, test names, and
   error messages, the three places they most often leak.
4. **Variant fairness.** Per-student variation is an integrity feature
   (`ts/shared/ai_era_integrity.md`, resilience pattern 3) and a fairness risk. Every
   variant set ships with an equivalence argument — same concepts, same required method,
   same step count and difficulty class — and a spot-solve of sampled variants checking
   it. What varies and what is held fixed is stated, not implied.
5. **Environment honesty.** Dependencies are pinned, the environment file is part of the
   package, and the README's setup instructions were followed cold in a fresh
   environment before shipping. "Works on the builder's machine" is not verification.
6. **License and provenance.** Real-world datasets enter a lab only with
   professor-supplied provenance and license; the skill never scrapes or fabricates a
   source. Synthetic data is labeled synthetic to students wherever realism could
   mislead — students drawing real-world conclusions from invented measurements is a
   harm, not a feature.

## Outputs

- `labs/<id>_<slug>/handout.md` — student-facing, from `ts/lab-forge/templates/lab_handout_template.md`
- `labs/<id>_<slug>/starter/` — scaffold repo with env file and tested README
- `labs/<id>_<slug>/data/` — dataset(s); per-student variants under `data/variants/`
- `labs/<id>_<slug>/solution/` — reference solution + grading notes (professor-only)
- `labs/<id>_<slug>/grader/` — visible + hidden tests, partial-credit map,
  submission-auditor check spec
- `labs/<id>_<slug>/ground_truth.md` — professor-only: planted properties, seeds,
  generating code, seed↔student mapping
- `labs/<id>_<slug>/verification_record.md` — what was executed, when, with what result
- Passport updates: `assessment_plan[].artifact_ref`, `artifacts[]`

## References

- `ts/lab-forge/references/synthetic_data_patterns.md` — planted-effect designs, seeding schemes,
  recoverability verification, realism details, deliberate vs accidental traps
- `ts/lab-forge/references/autograder_patterns.md` — test-split rationale, partial-credit schemes,
  tolerance handling, anti-gaming, platform selection
- `ts/lab-forge/templates/lab_handout_template.md`
- Shared: `ts/shared/pedagogy_foundations.md`, `ts/shared/ai_era_integrity.md`,
  `ts/shared/checkpoint_protocol.md`, `ts/shared/course_passport_schema.md`
