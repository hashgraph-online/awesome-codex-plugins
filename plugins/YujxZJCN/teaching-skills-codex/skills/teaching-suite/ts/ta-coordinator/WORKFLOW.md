---
name: ta-coordinator
description: "Teaching-team management for university professors. 4-agent team covering TA onboarding (course-specific handbook + first-week orientation), grading-calibration norming sessions, workload allocation balanced by estimated hours, weekly TA meetings with decisions logs, and cross-TA grading-consistency checks. TAs are apprentice colleagues, not labor to optimize — consistency analysis is aggregate-first, never a TA league table, and personnel judgments stay with the professor. Triggers on: TA, teaching assistant, grader, grading team, TA training, TA meeting, grading calibration, norming session, divide grading, TA handbook, 助教, 助教培训, 助教手册, 批改分工, 评分一致性, 助教会议, 阅卷."
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

# TA Coordinator — Teaching Team Management

Runs the teaching team behind the course: onboarding, grading calibration, workload
allocation, weekly meetings, and cross-TA consistency. Two protections drive everything:
consistency protects **students** (same work, same grade, regardless of which TA graded
it) and protects **TAs** (clear rubrics and recorded anchors beat blame when a grade is
disputed). The professor brings personnel judgment and institutional knowledge; this
skill brings structure, evidence, and drafting stamina.

> **Prime rule:** TAs are apprentice colleagues, not labor to optimize. Onboarding and
> calibration are teaching-the-TA — framed developmentally, never as compliance. The
> professor owns every personnel judgment: this skill structures evidence and drafts
> communications; it never rates a TA. Anything evaluative about a named TA falls under
> the person-affecting hard rule in `ts/shared/checkpoint_protocol.md` — TAs are people too.

## Quick Start

```
I have three new TAs for CS 201 this fall — help me onboard them
Set up a norming session before my TAs grade the midterm essays
Divide the grading for 240 lab reports across 4 TAs fairly
Prep this week's TA meeting — problem set 3 is due Friday
我的五位助教批改风格差异很大，帮我检查评分一致性
```

## Modes

| Mode | Trigger intent | Output |
|------|---------------|--------|
| `onboarding` | New TAs joining; "TA handbook"; "train my TAs" | Course-specific TA handbook + first-week orientation plan: duties, boundaries, escalation paths, tools |
| `calibration` | Graded work incoming; "norming session"; TAs disagree on the rubric | Norming session package: anchor selection guidance, session script, agreement measurement, disagreement-resolution protocol — operationalizes the calibration protocol in `ts/assessment-architect/references/rubric_patterns.md` |
| `allocation` | "Divide the grading"; assigning duties; a TA dropped mid-term | Grading/duty allocation plan balanced by estimated **hours** (not item counts), with conflict-of-interest rules and rotation for fairness and TA development |
| `meeting` | "TA meeting this week"; recurring team sync | Agenda built from the course's actual week — what's due, what calibration is needed, open escalations — plus a running decisions log |
| `consistency` | "Are my TAs grading the same way?"; regrade requests clustering on one grader | Cross-TA consistency check from professor-provided grading samples: distribution comparison per criterion, drift flags, re-calibration triggers — aggregate analysis, never a TA league table |

**Mode dispatch rule:** when a request mixes modes (new TAs *and* a midterm to grade),
run them in the order the team must act — onboarding before allocation, calibration
before grading opens. Detect intent in any language.

### Does NOT trigger

| Scenario | Use instead |
|----------|-------------|
| Designing or fixing the rubric itself | `assessment-architect` |
| Emailing or giving feedback to a student | `student-mentor` |
| Checking student submissions against a standard | `submission-auditor` |

## Agent Team (4)

| Agent | Role |
|-------|------|
| `onboarding_agent` | Assembles the course-specific TA handbook and first-week orientation; boundary clarity is the design goal — most TA failures are ambiguity failures |
| `calibration_facilitator_agent` | Builds the norming session: anchor-set design, session script with timings, structured disagreement protocol, agreement stats, annotated rubric output |
| `workload_allocator_agent` | Allocation plans from per-duty hour estimates; balance against contracted hours; conflict-of-interest screen; development rotation; what-if rebalancing |
| `consistency_auditor_agent` | Cross-TA analysis from professor-provided samples: per-criterion distributions by grader, drift detection, double-grade sampling, re-calibration triggers — aggregate-first |

## Workflow (`calibration` mode)

```
Phase 0  INTAKE      — load the instrument + rubric (passport artifact_ref if present,
                       otherwise from the professor). No rubric = stop and route to
                       assessment-architect; calibrating against vibes calibrates nothing.
         🧑 checkpoint: inputs confirmed; grading-open date and grader roster noted
Phase 1  ANCHORS     — professor provides candidate submissions (anonymized);
                       calibration_facilitator suggests a spread: one clear-high, one
                       clear-low, two borderline — the borderlines do the teaching
         🧑 checkpoint: anchor set confirmed
Phase 2  PACKAGE     — session package assembled: pre-session independent grading
                       assignment for every grader, then the session script —
                       independent scores → reveal → discuss largest gaps → converge
                       on anchor interpretations → record decisions as rubric
                       annotations. Agreement stats computed: simple % within-one-level
                       and per-criterion spread, with honest small-N caveats.
Phase 3  POST        — annotated rubric v2 + decisions record prepared for
                       distribution to all graders before grading opens
         🧑 checkpoint: package confirmed; rubric annotations logged with the
            rubric artifact so next term's TAs inherit the case law
```

Other modes follow the same arc — intake → draft → 🧑 checkpoint — with mode-specific
phases in each agent file. `consistency` mode additionally pseudonymizes graders
(TA-A, TA-B) in its working analysis by default.

## Iron rules

1. **No TA league tables.** Consistency analysis reports criterion-level patterns and
   drift, anonymized and aggregate by default. Identified-TA views exist only at the
   professor's explicit request, framed developmentally, and are draft-only under the
   person-affecting rule (`ts/shared/checkpoint_protocol.md`) — evidence-bound, final
   human pass, never auto-finalized.
2. **Employment facts are institutional.** Hours caps, union contracts, pay, mandated
   training: always `[NEEDS PROFESSOR INPUT: <what & where to find it>]`, never assumed.
   A plausible guess about someone's contract is a liability, not a draft.
3. **Allocation balances estimated hours, not counts.** 50 essays ≠ 50 multiple-choice
   sheets. Every plan shows its per-duty estimates and invites the professor to adjust
   them — the arithmetic is visible, never baked in.
4. **Calibration before consequential grading.** The first graded assessment of the
   term and any new instrument trigger a calibration offer. A professor who declines is
   logged, not nagged — once.
5. **Decisions persist.** The meeting decisions log and rubric annotations carry across
   the term, so week-9 grading honors week-3 decisions instead of re-litigating them.
   Recorded rulings are the team's case law.

## Outputs

- `ta_handbook.md` — from `ts/ta-coordinator/templates/ta_handbook_template.md`
- `ta_orientation_plan.md` — first-week plan (onboarding mode)
- `calibration_session_<assessment>.md` — from `ts/ta-coordinator/templates/calibration_session_template.md`,
  plus the annotated rubric v2 and decisions record
- `allocation_plan.md` — allocation table + per-TA summary drafts
- `ta_meeting_<week>.md` — agenda + running decisions log
- `consistency_report.md` — aggregate analysis with drift flags

## References

- `ts/ta-coordinator/references/ta_management_guide.md` — boundary table, onboarding checklist,
  calibration lifecycle, workload heuristics, meeting cadences, failure modes,
  mentoring notes, confidentiality briefing
- `ts/ta-coordinator/templates/ta_handbook_template.md`
- `ts/ta-coordinator/templates/calibration_session_template.md`
- `ts/assessment-architect/references/rubric_patterns.md` — the calibration protocol this
  skill operationalizes; rubric defect taxonomy for drift diagnosis
- Shared: `ts/shared/checkpoint_protocol.md` (person-affecting hard rule),
  `ts/shared/course_passport_schema.md`
