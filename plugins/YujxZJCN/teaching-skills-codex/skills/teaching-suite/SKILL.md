---
name: teaching-suite
description: >
  Codex-native Teaching Skills suite for university professors — the full teaching lifecycle: course design, lesson building, assessment, student mentoring, submission auditing, reflection, plus slide-deck rendering, executable labs, video scripting, course publishing, TA coordination, accreditation mapping, bilingual courseware, and learner analysis (学情分析). Use when the user asks to design a course, write outcomes or a syllabus, build a lesson or slides, write an exam/quiz/rubric, check student submissions against a standard, give feedback or a recommendation letter, analyze student evaluations, run a teaching pipeline, or any Claude-style ts-* alias such as /ts-accredit, ts-accredit, /ts-activities, ts-activities, /ts-align, ts-align, /ts-announce, ts-announce, /ts-audit, ts-audit, /ts-calibrate, ts-calibrate, /ts-cohort, ts-cohort, /ts-course, ts-course, /ts-dashboard, ts-dashboard, /ts-deck, ts-deck, /ts-diagnostic, ts-diagnostic, /ts-evals, ts-evals, /ts-exam, ts-exam, /ts-feedback, ts-feedback, /ts-full, ts-full, /ts-glossary, ts-glossary, /ts-integrity, ts-integrity, /ts-lab, ts-lab, /ts-lesson, ts-lesson, /ts-letter, ts-letter, /ts-midcourse, ts-midcourse, /ts-outcomes, ts-outcomes, /ts-redesign, ts-redesign, /ts-rubric, ts-rubric, /ts-script, ts-script, /ts-spec, ts-spec, /ts-statement, ts-statement, /ts-status, ts-status, /ts-syllabus, ts-syllabus, /ts-translate, ts-translate. Triggers on: accreditation, ABET, AACSB, program outcomes, curriculum map, self-study, assessment report, learning outcomes assessment, continuous improvement report, 专业认证, 工程教育认证, 培养方案, 毕业要求, 课程目标达成, 自评报告, 持续改进, 课程矩阵, exam, midterm, final, quiz, test questions, rubric, grading criteria, project brief, assignment design, question bank, item analysis, academic integrity, AI-proof, 出题, 试卷, 考试, 测验, 评分标准, 评分量表, 课程项目, 题库, 试题分析, 学术诚信, translate course materials, bilingual course, English-medium instruction, EMI, terminology glossary, Chinese version, parallel syllabus, 双语教学, 双语课程, 全英文授课, 术语表, 专业术语, 翻译课件, 中英对照, 中文版, student readiness, pre-assessment, diagnostic quiz, pre-lesson questionnaire, prior knowledge survey.
metadata:
  version: "0.2.1"
  upstream_suite: "teaching-skills"
  codex_adapter: true
allowed-tools: Read, Glob, Grep, WebSearch, Bash(python3 *), Bash(python *)
---

# Teaching Suite for Codex

Codex adapter for the **Teaching Skills** suite (course design → build →
assess → deliver → reflect → improve). The vendored upstream content lives
under `ts/`; route through this file first.

This is the sibling Codex distribution of the Claude Code suite
[`YujxZJCN/teaching-skills`](https://github.com/YujxZJCN/teaching-skills). Same
workflow content, Codex-native packaging.

## First Rule — load lazily

Do **not** load the whole suite by default. Select one workflow, read that
workflow's `ts/<skill>/WORKFLOW.md`, then load only the agent, reference, or
template files needed for the user's current stage. The vendored workflow entry
files are named `WORKFLOW.md` (not `SKILL.md`) so Codex registers only this one
router skill instead of every vendored workflow.

## Non-negotiables (apply in every workflow)

These are the suite's standing rules. Read `ts/shared/checkpoint_protocol.md`
and `ts/shared/pedagogy_foundations.md` when a task touches them; never violate
them even when reading lazily:

1. **The professor is the pilot.** Surface every consequential default at a
   checkpoint; respect "just proceed"; never auto-finalize person-affecting output.
2. **No invented context.** Empty learner/institution facts are asked for or
   marked `[NEEDS PROFESSOR INPUT: …]`; uncertain domain claims get `[VERIFY: …]`.
3. **Person-affecting outputs are evidence-bound** (feedback, letters,
   interventions): only material the professor provided, no invented anecdotes,
   verify-before-send reminder, and **student data never enters the Course
   Passport** (`ts/shared/course_passport_schema.md`).
4. **Integrity by design, not detection** (`ts/shared/ai_era_integrity.md`): no
   AI-detection tools, ever.
5. **Evidence honesty.** Student evaluations are biased small-N signal, not a score.

## Course Passport & validators

State lives in `course_passport.yaml` (`ts/shared/course_passport_schema.md`),
not the conversation. The deterministic layer travels to Codex — run it when
Python 3 is available:

```bash
python3 ts/scripts/check_passport.py course_passport.yaml          # structure + id mirrors
python3 ts/scripts/check_alignment_gate.py course_passport.yaml    # Gate 1.5, A1–D3
python3 ts/scripts/build_dashboard.py course_passport.yaml         # single-file HTML overview
```

## Workflow Router

Choose the workflow by intent, then read its `WORKFLOW.md`:

| User intent | Read first |
|---|---|
| Accreditation and program-assessment documentation for university professors | `ts/accreditation-mapper/WORKFLOW.md` |
| Builds assessment instruments for university professors — pipeline Stage 3 | `ts/assessment-architect/WORKFLOW.md` |
| Bilingual course-material maintenance for university professors — default EN ⇄ 简体中文, language-pair agnostic | `ts/bilingual-courseware/WORKFLOW.md` |
| Learner and cohort analysis (学情分析) for university professors — cross-cutting support for design, builds, and the weekly loop | `ts/cohort-analyst/WORKFLOW.md` |
| Backward course design for university professors | `ts/course-designer/WORKFLOW.md` |
| Student-facing communication and packaging for university professors, derived entirely from the Course Passport | `ts/course-publisher/WORKFLOW.md` |
| Slide deck production for university professors | `ts/deck-studio/WORKFLOW.md` |
| Executable teaching-artifact builder for STEM professors — pipeline Stage 2 extension | `ts/lab-forge/WORKFLOW.md` |
| Class-meeting materials builder for university professors | `ts/lesson-builder/WORKFLOW.md` |
| Recorded-media scripting for university professors | `ts/media-scripter/WORKFLOW.md` |
| During-semester student support for university professors | `ts/student-mentor/WORKFLOW.md` |
| Specification-driven submission auditing for university professors | `ts/submission-auditor/WORKFLOW.md` |
| Teaching-team management for university professors | `ts/ta-coordinator/WORKFLOW.md` |
| Full teaching-lifecycle orchestrator for university professors | `ts/teaching-pipeline/WORKFLOW.md` |
| Evidence-honest teaching reflection for university professors | `ts/teaching-reflector/WORKFLOW.md` |

For a whole-course or multi-stage request ("teach / prepare my course", "new
semester"), start with `ts/teaching-pipeline/WORKFLOW.md`; it orchestrates the
others through the alignment and quality gates.

## Claude-Style Alias Router

Codex does not install Claude slash commands, but this package emulates their
intent. If the request starts with a slash alias (`/ts-exam`) or a plain alias
(`ts-exam`), strip the alias token, read the matching `ts/commands/<alias>.md`
recipe, then route to the workflow below. The `model:` field in any recipe
frontmatter is a Claude hint only — Codex uses the current model.

| Alias | Read recipe | Then route to |
|---|---|---|
| `/ts-accredit`, `ts-accredit` | `ts/commands/ts-accredit.md` | `ts/accreditation-mapper/WORKFLOW.md` in `map` mode |
| `/ts-activities`, `ts-activities` | `ts/commands/ts-activities.md` | `ts/lesson-builder/WORKFLOW.md` in `activities` mode |
| `/ts-align`, `ts-align` | `ts/commands/ts-align.md` | `ts/course-designer/WORKFLOW.md` in `align-check` mode |
| `/ts-announce`, `ts-announce` | `ts/commands/ts-announce.md` | `ts/course-publisher/WORKFLOW.md` in `announcement` mode |
| `/ts-audit`, `ts-audit` | `ts/commands/ts-audit.md` | `ts/submission-auditor/WORKFLOW.md` in `audit` mode |
| `/ts-calibrate`, `ts-calibrate` | `ts/commands/ts-calibrate.md` | `ts/ta-coordinator/WORKFLOW.md` in `calibration` mode |
| `/ts-cohort`, `ts-cohort` | `ts/commands/ts-cohort.md` | `ts/cohort-analyst/WORKFLOW.md` in `cohort-profile` mode |
| `/ts-course`, `ts-course` | `ts/commands/ts-course.md` | `ts/course-designer/WORKFLOW.md` in `full` mode |
| `/ts-dashboard`, `ts-dashboard` | `ts/commands/ts-dashboard.md` | `ts/teaching-pipeline/WORKFLOW.md` in `dashboard` mode |
| `/ts-deck`, `ts-deck` | `ts/commands/ts-deck.md` | `ts/deck-studio/WORKFLOW.md` in `deck` mode |
| `/ts-diagnostic`, `ts-diagnostic` | `ts/commands/ts-diagnostic.md` | `ts/cohort-analyst/WORKFLOW.md` in `instrument` mode |
| `/ts-evals`, `ts-evals` | `ts/commands/ts-evals.md` | `ts/teaching-reflector/WORKFLOW.md` in `eval-analysis` mode |
| `/ts-exam`, `ts-exam` | `ts/commands/ts-exam.md` | `ts/assessment-architect/WORKFLOW.md` in `exam` mode |
| `/ts-feedback`, `ts-feedback` | `ts/commands/ts-feedback.md` | `ts/student-mentor/WORKFLOW.md` in `feedback` mode |
| `/ts-full`, `ts-full` | `ts/commands/ts-full.md` | `ts/teaching-pipeline/WORKFLOW.md` in `full` mode |
| `/ts-glossary`, `ts-glossary` | `ts/commands/ts-glossary.md` | `ts/bilingual-courseware/WORKFLOW.md` in `glossary` mode |
| `/ts-integrity`, `ts-integrity` | `ts/commands/ts-integrity.md` | `ts/assessment-architect/WORKFLOW.md` in `integrity-check` mode |
| `/ts-lab`, `ts-lab` | `ts/commands/ts-lab.md` | `ts/lab-forge/WORKFLOW.md` in `lab` mode |
| `/ts-lesson`, `ts-lesson` | `ts/commands/ts-lesson.md` | `ts/lesson-builder/WORKFLOW.md` in `full` mode |
| `/ts-letter`, `ts-letter` | `ts/commands/ts-letter.md` | `ts/student-mentor/WORKFLOW.md` in `recommendation-letter` mode |
| `/ts-midcourse`, `ts-midcourse` | `ts/commands/ts-midcourse.md` | `ts/teaching-reflector/WORKFLOW.md` in `midcourse` mode |
| `/ts-outcomes`, `ts-outcomes` | `ts/commands/ts-outcomes.md` | `ts/course-designer/WORKFLOW.md` in `outcomes-only` mode |
| `/ts-redesign`, `ts-redesign` | `ts/commands/ts-redesign.md` | `ts/course-designer/WORKFLOW.md` in `redesign` mode |
| `/ts-rubric`, `ts-rubric` | `ts/commands/ts-rubric.md` | `ts/assessment-architect/WORKFLOW.md` in `rubric` mode |
| `/ts-script`, `ts-script` | `ts/commands/ts-script.md` | `ts/media-scripter/WORKFLOW.md` in `script` mode |
| `/ts-spec`, `ts-spec` | `ts/commands/ts-spec.md` | `ts/submission-auditor/WORKFLOW.md` in `spec` mode |
| `/ts-statement`, `ts-statement` | `ts/commands/ts-statement.md` | `ts/teaching-reflector/WORKFLOW.md` in `teaching-statement` mode |
| `/ts-status`, `ts-status` | `ts/commands/ts-status.md` | `ts/teaching-pipeline/WORKFLOW.md` in `status` mode |
| `/ts-syllabus`, `ts-syllabus` | `ts/commands/ts-syllabus.md` | `ts/course-designer/WORKFLOW.md` in `syllabus-only` mode |
| `/ts-translate`, `ts-translate` | `ts/commands/ts-translate.md` | `ts/bilingual-courseware/WORKFLOW.md` in `translate` mode |

## What is vendored

`ts/` contains every skill's `WORKFLOW.md` + `agents/` + `references/` +
`templates/`, the `shared/` contracts (passport schema, gate protocols, pedagogy
foundations, AI-era integrity, checkpoint protocol), the tool-agnostic
`scripts/` (validators + dashboard), the `commands/` alias recipes, and
`MODE_REGISTRY.md`. The Claude Code plugin loader files are intentionally not
vendored. See `manifest.json` for the source commit pin.
