# Rubric Patterns

Working reference for `rubric_designer_agent` and professors reviewing its drafts.
A rubric serves three audiences at once: students aiming before submission (Pedagogy
Foundations §6), graders scoring consistently, and the professor defending a grade
months later. A rubric failing any audience is a defect.

## Choosing the rubric type

| Type | Shape | Use when | Trade-off |
|------|-------|----------|-----------|
| **Analytic** | criteria × levels grid, points per cell | Multi-dimensional work; multiple graders; weight ≥10% (Quality Gate T2); diagnostic feedback wanted | Slowest to apply; risk of criterion bloat |
| **Holistic** | one scale of integrated level descriptors | Short one-construct responses; single grader; speed matters | Little diagnostic feedback; drifts across graders — avoid with TA teams |
| **Single-point** | one proficiency descriptor, open margins for "exceeds"/"falls short" notes | Formative drafts; feedback-rich low-stakes work; milestone check-ins | No automatic score; grader writes more |

Default logic: analytic for anything substantial or team-graded; holistic only where
its speed is actually needed; single-point for the milestones inside project briefs,
where comments matter more than scores.

## Descriptor-writing rules

1. **Observable qualities, not adverb intensity.** Each level names what is present,
   absent, or different in the work — something a grader can point at.

   | Bad (adverb ladder) | Good (observable) |
   |---------------------|-------------------|
   | Excellent: very thorough analysis / Good: thorough analysis / Fair: somewhat thorough | Excellent: examines all three cases incl. boundary conditions / Good: examines all three cases, boundary conditions absent / Fair: examines one or two cases |
   | Strong understanding of the theory | Applies the theory to the case and states one limitation of that application |
   | Writing is mostly clear | Each paragraph advances one claim; a reader can restate the argument from topic sentences alone |

2. **About the work, never the student.** "Argument lacks counter-evidence," not
   "student doesn't understand argumentation." Rubric language ends up quoted in grade
   disputes; describe the artifact.

3. **Parallel structure across levels.** Each level addresses the same aspects in the
   same order, so the difference between adjacent levels is findable in seconds.

4. **Top level is excellent-achievable, not mythical.** A top descriptor no real
   student artifact ever meets compresses the scale and demoralizes; calibrate it
   against real strong work.

5. **Student-facing language.** Terms taught in the course only; the rubric ships with
   the brief. Jargon students haven't met is a hidden criterion in disguise.

## Common rubric defects

| Defect | Symptom | Fix |
|--------|---------|-----|
| **Adverb ladder** | Levels differ only by very/mostly/somewhat | Rewrite per rule 1 — name the observable difference |
| **Hidden criteria** | Graders dock points for things no row mentions (writing quality, formatting, effort) | Add the criterion to rubric *and* brief, or stop grading it |
| **Double-barreled criteria** | One row scores two things ("clarity and accuracy") — work that's clear but wrong has no cell | Split into two rows with their own weights |
| **Level gaps** | Real work falls between two descriptors and graders improvise | Test descriptors against past borderline work; rewrite until every plausible artifact lands somewhere |
| **Criterion bloat** | 10+ rows; grading time explodes; weights per row become noise | Merge to 4–7 criteria traced to outcomes; cut rows tracing to nothing |
| **Orphan criteria** | A row tracing to no outcome and no stated requirement | Cut it, or surface the expectation in the brief — never grade the unstated |
| **Score-first anchoring** | Levels named A/B/C/D — graders match the student to a grade, then read the descriptor | Name levels by quality words or numbers; let the grade be computed |

## TA calibration protocol

Multiple graders without calibration = different exams for different students. Cost: one
hour up front, repaid in regrade requests that never happen.

**Anchor papers.** Before grading opens, the professor selects 3–5 real (anonymized)
submissions spanning the range — including one borderline case — and scores them
against the rubric with margin notes on *why* each cell was chosen. These anchors are
the rubric's case law; graders consult them before averaging instincts.

**Norming session script (~60 min):**

1. (10 min) Walk the rubric: each criterion's intent, the distinguishing line between
   the top two levels of each — that boundary causes most drift.
2. (15 min) All graders independently score the same anchor — no discussion.
3. (20 min) Compare cell-by-cell. Discuss every divergence ≥1 level until the room
   agrees on what the descriptor means; the professor arbitrates and records the ruling
   on the anchor.
4. (10 min) Score a second anchor independently; agreement should visibly tighten. If
   it doesn't, the rubric has a defect (usually a level gap or double-barrel) — fix the
   rubric, don't blame the graders.
5. (5 min) Logistics: how to flag a submission no descriptor fits (escalate, don't
   improvise), regrade-request routing, and a mid-grading spot-check plan (professor
   re-scores a sample from each grader; drift >1 level on >20% of the sample triggers a
   re-norm).

Record norming decisions with the rubric artifact — next semester's TAs inherit the
case law instead of re-litigating it.
