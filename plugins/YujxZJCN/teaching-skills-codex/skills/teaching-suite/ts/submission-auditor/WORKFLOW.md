---
name: submission-auditor
description: "Specification-driven submission auditing for university professors. 4-agent team that compiles a professor's template, requirements doc, rubric, or exemplar into a checkable Submission Spec, audits student submissions (single or batch) against it with evidence-located findings, and produces per-student feedback reports plus a class-level pattern report. Works for any genre: lab reports, papers, theses, code projects, presentation decks. Triggers on: check submissions, format check, check against template, does this meet the requirements, lab report check, audit student work, compliance check, submission requirements, batch check, 检查作业, 格式检查, 格式审查, 实验报告检查, 论文格式, 检查是否符合要求, 批量检查, 提交规范."
metadata:
  version: "1.0.0"
  last_updated: "2026-06-10"
  status: active
  pipeline_stage: 4
  related_skills:
    - assessment-architect
    - student-mentor
    - teaching-pipeline
---

# Submission Auditor — Specification-Driven Submission Review

Turns "here's my standard, check their work against it" into a disciplined three-step
flow: **compile the spec → audit with located evidence → report at two altitudes**
(per-student feedback, class-level patterns). The professor's standard is the law; this
skill makes it checkable, applies it consistently across every submission, and reports
honestly about which checks were mechanical and which were judgment.

> **Prime rule:** an audit finding without a location in the student's work does not
> exist. Every finding cites where it looked ("§3 Results, p.2: figure has no caption"),
> and every judgment-type finding quotes the evidence it judged. "Generally weak
> formatting" is not a finding.

## Quick Start

```
Here's my lab report template — check these 40 submissions against it
这是我的实验报告模板，帮我检查这批学生提交的格式和内容是否符合要求
Does this thesis draft meet our department's format requirements? (attach both)
Build a submission checklist students can self-check before the deadline
```

## Modes

| Mode | Trigger intent | Output |
|------|---------------|--------|
| `spec` | "Here's my template/requirements" (first contact with a new standard) | Compiled Submission Spec — every requirement made checkable, classified deterministic vs judgment, confirmed at a checkpoint |
| `audit` | "Check this submission" with a spec (or material to compile one) | Audit findings + per-student feedback report draft |
| `batch-audit` | "Check these N submissions" | Per-student reports + class-level pattern report + consistency record |
| `self-check` | "Make a checklist students can use themselves" | Student-facing self-check version of the spec (deterministic checks only, supportive phrasing) |
| `calibrate` | "The audit was too strict/lenient on X" or professor reviews a sample | Spec revision pass: tighten/loosen checks against professor verdicts on sampled findings; revisions logged in the spec |

**Mode dispatch rule:** no confirmed spec yet → `spec` mode always runs first, whatever
was asked. Auditing against an unconfirmed standard produces authoritative-looking
reports built on guesses — the blueprint-first rule of `assessment-architect`, applied
to checking.

### Does NOT trigger

| Scenario | Use instead |
|----------|-------------|
| Designing the assignment, template, or rubric itself | `assessment-architect` |
| Qualitative feedback beyond the spec (style, argument coaching) | `student-mentor` `feedback` |
| Grading / assigning scores | This skill audits compliance; scoring is the professor's act (see Iron Rule 4) |
| Checking AI-resilience of the assignment design | `assessment-architect` `integrity-check` |

## Agent Team (4)

| Agent | Role |
|-------|------|
| `spec_compiler_agent` | Compiles template/requirements/rubric/exemplar into the Submission Spec; classifies checks deterministic vs judgment; pushes ambiguous requirements back to the professor instead of guessing |
| `format_auditor_agent` | Runs deterministic checks: structure, required sections, length, citation format presence, figures/tables/captions, naming, file conventions — location-cited PASS/FAIL/NOT_EVALUABLE per check |
| `content_auditor_agent` | Runs judgment checks: content requirements judged against quoted evidence from the submission; every verdict labeled JUDGMENT with confidence; never drifts beyond the spec |
| `report_writer_agent` | Two-altitude reporting: per-student feedback report (formative, per `ts/student-mentor/references/feedback_principles.md` structure) + class-level pattern report; runs the batch fairness pass |

## Workflow (`batch-audit` mode)

```
Phase 0  SPEC       — load confirmed Submission Spec (or run `spec` mode first)
         🧑 checkpoint: spec confirmed — which checks are deterministic, which are
            judgment, severities, and what the professor chose NOT to check
Phase 1  AUDIT      — per submission: format_auditor (deterministic) then
                      content_auditor (judgment) → findings ledger per student,
                      every finding location-cited
Phase 2  FAIRNESS   — report_writer cross-submission pass: same defect ⇒ same
                      severity and same wording class everywhere; judgment-check
                      verdicts spot-compared across submissions for drift
Phase 3  REPORT     — per-student feedback reports (drafts) + class pattern report
                      (defect frequencies, common misses, spec ambiguities surfaced
                      by the data)
         🧑 checkpoint: professor reviews JUDGMENT findings sample + pattern report
            before any per-student report is released
```

The class pattern report routes two ways: high-frequency misses are a *teaching* signal
(offer a `lesson-builder` remediation segment or an announcement draft), and recurring
spec ambiguities are a *spec* signal (offer `calibrate` mode). Both feed passport
`iteration_history` as evidence — with no student-identifying data (counts only).

## Iron Rules

1. **Spec before audit.** No submission is audited against an unconfirmed spec. The
   spec checkpoint must show the professor what will be checked, how each check is
   classified, and what was left uncheckable (`NOT_CHECKABLE` items are listed, not
   silently dropped).
2. **Deterministic / judgment separation is visible everywhere.** A missing section is
   a fact; "the discussion does not adequately address error sources" is a judgment.
   The spec classifies every check; audit output labels every finding; per-student
   reports phrase judgment findings as observations with quoted evidence, not verdicts.
3. **Evidence location is mandatory.** Every finding carries section/page/line (or
   file/line for code); every judgment finding quotes what it judged. A finding the
   auditor cannot locate is reported as the auditor's failure, not the student's.
4. **Audit, don't grade.** Output is compliance findings, never scores. If the
   professor explicitly maps spec checks to rubric points, the skill computes the
   mapping as a *draft* with the mapping shown — and the person-affecting hard rule
   applies in full (`ts/shared/checkpoint_protocol.md`).
5. **Batch fairness is a checked property, not an assumption.** The fairness pass runs
   on every batch; its record (checks compared, drift found and fixed) ships with the
   batch. Same defect, same treatment — audit order must not change outcomes.
6. **Privacy.** Submissions are pseudonymized in session where feasible; reports use
   the professor's chosen identifiers; nothing student-identifying enters the Course
   Passport (counts and patterns only). Per-student reports are drafts with the
   verify-before-release reminder — and this skill never posts, emails, or publishes
   them.
7. **The spec is the boundary.** Auditors do not flag things the spec doesn't cover,
   however tempting — off-spec observations go to a separate "outside the spec" note
   for the professor only, at most once per batch. Scope creep in an audit is unfairness
   in disguise: it applies a rule students were never given.

## Outputs

- `submission_spec.md` — the confirmed spec (from `ts/submission-auditor/templates/submission_spec_template.md`)
- `audit/<student-id>_report.md` — per-student feedback report drafts
  (from `ts/submission-auditor/templates/feedback_report_template.md`)
- `audit/class_pattern_report.md` — frequencies, common misses, teaching signals,
  spec-ambiguity signals, fairness-pass record
- `self_check.md` (`self-check` mode) — student-facing checklist
- Passport: `iteration_history` evidence entry (anonymous counts), `artifacts[]` ledger

## References

- `ts/submission-auditor/references/spec_design_guide.md` — how to write checkable requirements; the
  deterministic/judgment classification test; common check library by genre (lab
  report, paper, thesis, code project, presentation)
- `ts/submission-auditor/templates/submission_spec_template.md`
- `ts/submission-auditor/templates/feedback_report_template.md`
- Shared: `ts/shared/checkpoint_protocol.md` (person-affecting hard rule),
  `ts/shared/pedagogy_foundations.md` §6 §8, `ts/student-mentor/references/feedback_principles.md`
