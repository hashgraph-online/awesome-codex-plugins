# Mode Registry

Canonical list of every mode in the suite. Slash commands in `commands/` map 1:1 onto
entries here. When adding a mode: update the skill's SKILL.md, this registry, and
`docs/ARCHITECTURE.md` together.

## course-designer (7 modes) — Stage 1

| Mode | Command | Purpose |
|------|---------|---------|
| full | `/ts-course` | Complete backward design: outcomes → assessment plan → schedule → syllabus |
| socratic | — (intent-triggered) | Guided dialogue → Course Concept Brief |
| outcomes-only | `/ts-outcomes` | Bloom-tagged learning outcome set |
| syllabus-only | `/ts-syllabus` | Syllabus from existing design |
| redesign | `/ts-redesign` | Diagnostic + prioritized redesign of existing course |
| align-check | `/ts-align` | Read-only constructive-alignment audit (Gate 1.5 standalone) |
| async-design | — | Adapt a confirmed design for online/async/hybrid: modules, sync/async split, engagement, accessibility |

## lesson-builder (8 modes) — Stage 2

| Mode | Command | Purpose |
|------|---------|---------|
| full | `/ts-lesson` | Complete package for one class meeting |
| lecture-notes | — | Prose lecture notes for a session |
| slides-outline | — | Assertion-evidence slide outline |
| activities | `/ts-activities` | Active-learning activity design |
| case-study | — | Teaching case + teaching notes |
| discussion-guide | — | Question ladders + facilitation plan |
| flipped | — | Pre-class spec + in-class application session |
| week-batch | — (pipeline) | Build a passport week / range of weeks |

## assessment-architect (11 modes) — Stage 3

| Mode | Command | Purpose |
|------|---------|---------|
| exam | `/ts-exam` | Blueprint → items → verified key → logistics |
| quiz | — | Low-stakes retrieval sets |
| question-bank | — | Item bank with controlled variants |
| rubric | `/ts-rubric` | Analytic / holistic / single-point rubric |
| project-brief | — | TILT-structured assignment brief |
| integrity-check | `/ts-integrity` | AI-resilience audit per `ts/shared/ai_era_integrity.md` |
| item-analysis | — | Post-exam difficulty / discrimination / distractor analysis |
| answer-key | — | Independent worked key for an existing instrument |
| grade-analysis | — | Final-grade distribution, shape diagnostics, cutoff/curve what-ifs (aggregates only) |
| group-assessment | — | Graded group-project + peer-assessment design with individual accountability |
| accommodate | — | Operationalize an already-granted accommodation into a modified instrument |

## student-mentor (7 modes) — Stage 4

| Mode | Command | Purpose |
|------|---------|---------|
| feedback | `/ts-feedback` | Structured feedback on student work (single / batch) |
| struggling-student | — | Evidence-based intervention plan + outreach draft |
| recommendation-letter | `/ts-letter` | Intake interview → letter draft |
| student-email | — | Difficult communications drafting |
| office-hours | — | Office-hours prep and triage |
| mentoring-plan | — | Advisee expectations doc + milestone map |
| integrity-case | — | Suspected-misconduct companion: factual evidence record + institutional-process routing (no verdict, ever) |

## teaching-reflector (6 modes) — Stage 5

| Mode | Command | Purpose |
|------|---------|---------|
| eval-analysis | `/ts-evals` | Thematic, bias-caveated evaluation analysis |
| midcourse | `/ts-midcourse` | Mid-semester feedback instrument + closing the loop |
| peer-observation | — | Observation prep packet / observation protocol |
| portfolio | — | Teaching portfolio assembly from real artifacts |
| teaching-statement | `/ts-statement` | Socratic elicitation → statement draft |
| sotl | — | Classroom-inquiry design (with IRB pointer) |

## submission-auditor (5 modes) — Stage 4

| Mode | Command | Purpose |
|------|---------|---------|
| spec | `/ts-spec` | Compile template / requirements / rubric / exemplar into a confirmed Submission Spec |
| audit | `/ts-audit` | Check one submission against the spec; feedback report draft |
| batch-audit | `/ts-audit` (multiple) | Per-student reports + class pattern report + fairness record |
| self-check | — | Student-facing pre-submission checklist from the spec |
| calibrate | — | Revise spec checks against professor verdicts on sampled findings |

## teaching-pipeline (5 modes) — Orchestrator

| Mode | Command | Purpose |
|------|---------|---------|
| full | `/ts-full` | Stage 0 → 6 lifecycle over the Course Passport |
| mid-entry | — (intent-triggered) | Validate existing materials, enter at the right stage |
| status | `/ts-status` | Passport + calendar position → what's next |
| new-term | — | Stage 6 → Stage 1 redesign re-entry with evidence |
| dashboard | `/ts-dashboard` | Single-file HTML course overview with local artifact links (`ts/scripts/build_dashboard.py`) |

---

# Extension skills

Production, operations, and compliance layers on top of the core pipeline. Each works
standalone; the pipeline dispatches them on demand at their stage.

## deck-studio (6 modes) — Stage 2 extension

| Mode | Command | Purpose |
|------|---------|---------|
| deck | `/ts-deck` | Outline/notes → rendered slide deck via real toolchain (Marp/Pandoc/Beamer/python-pptx) |
| theme | — | Course-wide visual theme: typography, colors, layout masters |
| figure | — | One code-rendered diagram/chart (matplotlib/mermaid/TikZ), colorblind-safe |
| handout | — | Deck → student handout variant |
| restyle | — | Audit + rebuild an existing deck against the slide design rules |
| poster | — | Academic/teaching poster |

## lab-forge (6 modes) — Stage 2 extension (STEM)

| Mode | Command | Purpose |
|------|---------|---------|
| lab | `/ts-lab` | Complete lab package: handout + starter + data + verified solution + grader |
| dataset | — | Synthetic datasets with planted, recoverable properties; per-student variants |
| starter-code | — | Scaffold repo: stubs with contracts, runs as shipped |
| autograder | — | Visible + hidden test suites, partial-credit map, feeds submission-auditor |
| solution | — | Reference solution produced by solving + executing; grading notes |
| variant | — | N difficulty-equivalent variants with the equivalence argument |

## course-publisher (5 modes) — Stage 4 extension

| Mode | Command | Purpose |
|------|---------|---------|
| announcement | `/ts-announce` | One-off action-first announcement draft |
| weekly-email | — | Week-N email from passport schedule + calendar |
| course-site | — | Static course website generated from the passport |
| lms-package | — | Upload-ready artifact packaging + per-LMS checklist |
| faq | — | Living FAQ answered from passport facts |

## accreditation-mapper (4 modes) — Stage 1 extension

| Mode | Command | Purpose |
|------|---------|---------|
| map | `/ts-accredit` | Course LO → program outcome → standard criteria matrix with evidence status |
| evidence | — | Evidence package assembly from passport artifacts |
| gap | — | Coverage gap analysis → remediation routed to course-designer |
| self-study | — | Self-study section drafts, claim strength capped by evidence status |

## ta-coordinator (5 modes) — Stage 4 extension

| Mode | Command | Purpose |
|------|---------|---------|
| onboarding | — | Course-specific TA handbook + orientation plan |
| calibration | `/ts-calibrate` | Grading norming session package + agreement stats |
| allocation | — | Hours-balanced duty allocation plan |
| meeting | — | Weekly TA meeting agenda + decisions log |
| consistency | — | Cross-TA grading consistency analysis (aggregate-first) |

## media-scripter (5 modes) — Stage 2 extension

| Mode | Command | Purpose |
|------|---------|---------|
| script | `/ts-script` | Mini-lecture video script: narration + visual cues + timing |
| storyboard | — | Shot-by-shot plan for screencasts/demos |
| series | — | Topic → 6–9 min episode sequence with retrieval questions |
| captions | — | Raw transcript → accurate captions + readable transcript |
| audio | — | Podcast-style adaptation with chapter markers |

## cohort-analyst (5 modes) — Cross-cutting support (学情分析)

| Mode | Command | Purpose |
|------|---------|---------|
| instrument | `/ts-diagnostic` | Design an ungraded pre-course diagnostic / pre-lesson questionnaire |
| cohort-profile | `/ts-cohort` | Analyze results → aggregate readiness profile → passport `learner_profile` |
| lesson-calibration | — | Profile → reteach/skip/pacing adjustments for a specific lesson or week |
| grouping | — | Evidence-based grouping plans (pseudonymized) |
| progress | — | Cohort-level trajectory re-analysis mid-term |

## bilingual-courseware (4 modes) — Cross-cutting support

| Mode | Command | Purpose |
|------|---------|---------|
| glossary | `/ts-glossary` | Course terminology glossary: candidates proposed, professor confirms |
| translate | `/ts-translate` | Glossary-bound translation with pedagogical-equivalence pass |
| parallel | — | Paired-version sync: propagate changes, detect drift |
| check | — | Read-only terminology consistency audit across materials |

---

**Total: 89 modes across 15 skills (6 core + teaching-pipeline + 8 extensions), 76 agents.**
