---
name: teaching-pipeline
description: "Full teaching-lifecycle orchestrator for university professors. 4-agent team driving the six sibling skills through staged gates over the Course Passport: design → alignment gate → build → assess → quality gate → semester delivery loop → reflection → next-term improvement. Resumable from the passport at any week of the term; mid-entry at any stage. Triggers on: teach a course, prepare my course, semester, full course pipeline, course lifecycle, new semester, what's next for my course, course status, 开课, 备一门课, 新学期, 整门课, 课程全流程, 教学流程, 下一步."
metadata:
  version: "1.0.0"
  last_updated: "2026-06-10"
  status: active
  pipeline_stage: orchestrator
  related_skills:
    - course-designer
    - lesson-builder
    - assessment-architect
    - student-mentor
    - submission-auditor
    - teaching-reflector
---

# Teaching Pipeline — Course Lifecycle Orchestrator

Orchestrates the whole teaching lifecycle — design, build, assess, deliver, reflect,
improve — by dispatching the six sibling skills in backward-design order over a single
Course Passport (`ts/shared/course_passport_schema.md`). The professor brings the
discipline, the students, and every decision; this skill brings sequence, gates, and
memory across the semester and across terms.

> **Prime rule:** unlike a paper pipeline, teaching is *cyclic and calendar-bound*.
> Stage 4 is a loop, not a step, and Stage 6 feeds Stage 1 of the next term. The
> passport plus today's position in the academic calendar — never the chat history —
> determines what happens next.

## Quick Start

```
I'm teaching a new course on machine learning next semester — run the whole pipeline
新学期要开一门《数据结构》，帮我把整门课准备出来
I already have a syllabus from last year — pick it up from there
It's week 6, what's next for my course?
课程现在什么状态？下一步做什么？
Term just ended, here are my student evals — close out the semester
```

## Modes

| Mode | Trigger intent | What it does |
|------|---------------|--------------|
| `full` | "Teach/prepare a whole course", new course from scratch | Stage 0 onward: intake → passport → all stages in order, every gate, every checkpoint |
| `mid-entry` | Professor arrives with existing materials or mid-process ("I already have a syllabus", "it's week 9") | Detect/ask where they are, validate existing materials into the passport (via course-designer `align-check`, not re-derivation), enter at the matching stage per the routing table below |
| `status` | "What's next?", "course status", 下一步 | Read passport + calendar position; report current stage, gate states, pending confirmations, and the next concrete action. Read-only |
| `new-term` | "Teaching it again", new semester of an existing course | Stage 6 → Stage 1 re-entry: load `iteration_history` evidence + the redesign brief, dispatch course-designer `redesign` with the evidence attached |
| `dashboard` | "Show me my course", "course overview", 课程总览 | Run `python3 scripts/build_dashboard.py <passport>` → single-file `course_dashboard.html` next to the passport: gates (stored + live re-check), outcomes, assessment plan, week-by-week resources with clickable local artifact links, ledger, workload, iteration history. Regenerated at any checkpoint on request — it is a build product of the passport, never hand-edited |

**Mode dispatch rule:** a passport already on disk + a vague request → run `status`
first and propose the next action; never restart `full` on top of an existing passport.
Detect intent in any language.

## Stage Map

```
Stage 0  CONTEXT    — intake → initialize Course Passport            🧑 checkpoint
Stage 1  DESIGN     — course-designer (full | redesign)              🧑 checkpoint
Gate 1.5 ALIGNMENT  — alignment_gate_protocol; BLOCK → back to 1     ✓ machine + professor ack
Stage 2  BUILD      — lesson-builder week-batch, in batches the
                      professor sizes (just-in-time by default)      🧑 checkpoint per batch
Stage 3  ASSESS     — assessment-architect per assessment_plan
                      entry + integrity-check                        🧑 checkpoint per instrument
Gate 3.5 QUALITY    — quality_gate_protocol; BLOCK → back to 2/3     ✓ machine + professor ack
Stage 4  DELIVER    — weekly loop for the whole term:
                      just-in-time builds · student-mentor on demand
                      · midcourse feedback at week 4–6               🧑 checkpoint per cycle
Stage 5  REFLECT    — teaching-reflector eval-analysis +
                      evidence triangulation                         🧑 checkpoint
Stage 6  IMPROVE    — iteration record → passport iteration_history;
                      prioritized change list; offer re-entry:
                      next term → Stage 1 redesign with evidence     🧑 checkpoint
```

| Stage | Skill / mode dispatched | Artifacts | Checkpoint / gate |
|-------|------------------------|-----------|-------------------|
| 0 CONTEXT | (this skill) intake | `course_passport.yaml` initialized | 🧑 context confirmed |
| 1 DESIGN | `course-designer` `full` (or `redesign` in `new-term`) | passport design fields, `syllabus.md`, `design_rationale.md` | 🧑 per course-designer's internal checkpoints |
| 1.5 ALIGNMENT | gate_runner → `ts/shared/alignment_gate_protocol.md` | `gates.alignment_gate` findings + status | ✓ machine checks + professor acknowledgment; BLOCK → Stage 1, max 3 rounds |
| 2 BUILD | `lesson-builder` `week-batch` | `lessons/W*` packages, schedule `artifact_refs` | 🧑 per batch |
| 3 ASSESS | `assessment-architect` (`exam`/`quiz`/`project-brief`/`rubric`… per `assessment_plan` type) + `integrity-check` | instruments + rubrics, `ai_resilience` set per assessment | 🧑 per instrument |
| 3.5 QUALITY | gate_runner → `ts/shared/quality_gate_protocol.md` | `gates.quality_gate` findings + status | ✓ machine checks + professor acknowledgment; BLOCK → Stage 2/3, max 3 rounds |
| 4 DELIVER | weekly: `lesson-builder` `week-batch` (next week); `student-mentor` (on demand); `submission-auditor` `spec`/`audit`/`batch-audit` (on demand, when work comes in); `teaching-reflector` `midcourse` (week 4–6) | week materials, mentoring outputs, submission audit reports, midcourse report | 🧑 per weekly cycle; person-affecting outputs per Checkpoint Protocol hard rule |
| 5 REFLECT | `teaching-reflector` `eval-analysis` + triangulation with peer/artifact evidence | evaluation analysis report | 🧑 analysis confirmed |
| 6 IMPROVE | iteration_coach | `iteration_history` entry, prioritized change list, redesign brief | 🧑 record confirmed; offer `new-term` |

**Build-ahead depth (Stage 2):** the pipeline does **not** default to building all 16
weeks up front. At the Stage 2 entry checkpoint the professor chooses a batch depth —
first week only, first unit, through the first exam, or everything. Just-in-time per
week/unit is the recommended default: lessons built months ahead go stale against the
real classroom. The choice is recorded in the passport and drives the Stage 4 loop.

## Mid-Entry Routing

Mid-entry is first-class, not an exception. The orchestrator validates what exists into
the passport (Iron Rule 3) and enters at the earliest stage whose entry invariants are
unmet (`ts/teaching-pipeline/references/pipeline_state_machine.md`).

| "I have…" | Entry point |
|-----------|-------------|
| Nothing — new course, blank page | Stage 0 `full` (offer course-designer `socratic` if aims are vague) |
| An old syllabus / inherited course outline | Stage 0 intake → back-fill passport from the syllabus (confirmed, not assumed) → course-designer `align-check` to validate → Gate 1.5 → Stage 2 (or back to Stage 1 `redesign` if the gate fails) |
| A full confirmed design but no class materials | Validate passport (or build one from the design) → Gate 1.5 if `not_run` → Stage 2 |
| Materials built but no exams/rubrics | Validate → Stage 3 (Gate 1.5 must show `pass`; if `not_run`, run it first — it is cheap and catches what Stage 3 would inherit) |
| Mid-semester, week N, course already running | Validate passport + ask/confirm calendar position → enter the Stage 4 loop at week N; Gates run retroactively only if the professor wants the audit |
| Term just ended, student evals in hand | Validate → Stage 5 (eval-analysis) → Stage 6 |

## Stage 4 — The Weekly Delivery Loop

Stage 4 is the term itself. Each cycle answers **the Monday question**: *"Week N — what's
due?"*

```
each week N of the term:
  1. ORIENT   — passport + calendar: what's taught in W(N+lead), what assessments are
                due/upcoming, what's already built (artifact_refs)
  2. BUILD    — just-in-time window: lesson-builder week-batch for the next unbuilt
                week(s) within the professor's chosen lead time (default: next week)
  3. SUPPORT  — student-mentor on demand ONLY: feedback batches, a struggling student
                the professor brings up, emails, office-hours prep;
                submission-auditor when work comes in: spec confirmed at assignment
                release, audit/batch-audit at collection
  4. MIDCOURSE— at week 4–6 (once): offer teaching-reflector `midcourse` — early
                feedback while there is still time to act on it
  5. CHECK    — 🧑 weekly checkpoint: what shipped, what's pending, next Monday's picture
```

Rules of the loop:

- **Resumable by calendar.** "What week are we in?" is answered from the passport's
  stored term calendar + today's date; a fresh session lands in the right cycle without
  recap. If the calendar was never stored, ask once and store it (Iron Rule 5).
- **Struggling-student support is on-demand and NEVER auto-initiated.** The pipeline
  does not scan grades, attendance, or any data for struggling students — the professor
  brings the concern, with the evidence. Privacy is structural, not configurable.
- **Person-affecting outputs** (feedback on named work, intervention emails, letters)
  follow the Checkpoint Protocol hard rule: evidence-bound, never auto-finalized, final
  human pass — and none of it enters the passport (Iron Rule 6).
- **Midcourse fires once,** in the week 4–6 window, as an offer — the professor may
  decline; the decline is logged so it is not re-offered weekly.

## Agent Team (4)

| Agent | Role |
|-------|------|
| `pipeline_orchestrator_agent` | Dispatch: reads passport, determines stage, invokes sibling skill modes, enforces stage order and gate blocking, routes mid-entry, collapses checkpoints on "just proceed" |
| `passport_keeper_agent` | State: passport read/validate/append per schema iron rules; reconciles hand-edited passports by asking; emits the `status` report; resume protocol for fresh sessions |
| `gate_runner_agent` | Gates: executes both gate protocols verbatim at 1.5 and 3.5; read-only except `gates.*`; findings cite passport ids; 3-round escalation rule |
| `iteration_coach_agent` | Stage 6: assembles semester evidence into the iteration record, prioritizes changes (impact × effort × evidence-confidence), writes `iteration_history`, prepares next term's redesign brief; protects what worked |

## Iron Rules

1. **The passport is the single source of truth.** State lives in
   `course_passport.yaml`, never in the conversation. A fresh session loads the
   passport and continues; anything not in the passport did not happen, and no skill
   assumes context the passport doesn't contain (Passport Iron Rule 2).
2. **Gates are non-skippable in pipeline mode.** Gate 1.5 and 3.5 always run and always
   end in professor acknowledgment. A BLOCK returns to the producing stage for at most
   3 fix-and-rerun rounds; a BLOCK that survives 3 rounds is escalated to the professor
   as a recorded design decision, not repeated a fourth time. (Standalone sibling-skill
   use never forces a gate.)
3. **Stage order is enforced downward only.** Backward design (Pedagogy Foundations §1):
   no materials before confirmed outcomes, no instruments before a confirmed assessment
   plan, no delivery before the Quality Gate. But mid-entry *validates* existing work
   into the passport via `align-check` — it never makes a professor re-derive a design
   they already have.
4. **Checkpoint provenance.** `confirmed_by_professor` is set only at a real
   confirmation (Passport Iron Rule 4). "Just proceed" collapses checkpoints to minimal
   confirmations per the Checkpoint Protocol — it never skips the confirmation itself,
   and person-affecting outputs never collapse.
5. **Calendar honesty.** Never invent the academic calendar — term dates, breaks, exam
   weeks, add/drop deadlines are institutional facts. Ask once at Stage 0 (or first
   need), store in the passport, and compute "what week is it?" from that record only.
6. **Person-affecting work stays out of the passport.** Stage 4 outputs about
   identifiable students follow the Checkpoint Protocol's hard rule (evidence-bound,
   final human pass); student names, grades, and case details are never written into
   `course_passport.yaml` or any pipeline state file.

## Extension Skills

Seven extension skills attach to pipeline stages on demand. The orchestrator offers
them where they fit but never requires them — gates do not depend on extensions.

| Stage | Extension dispatched | When |
|-------|---------------------|------|
| 1 / 6 | `accreditation-mapper` | Professor faces accreditation/program reporting; Stage 6 iteration records feed its continuous-improvement narrative |
| 2 | `deck-studio` | After lesson-builder slide outlines — render actual decks with the course theme |
| 2 | `media-scripter` | Flipped/online courses — script the recorded mini-lectures the flipped spec calls for |
| 2–3 | `lab-forge` | STEM courses — executable labs, per-student datasets, autograders (output feeds submission-auditor) |
| 4 | `course-publisher` | Weekly loop — announcements, weekly emails, course site, LMS packaging |
| 4 | `ta-coordinator` | Courses with TAs — onboarding before week 1, calibration before first graded assessment, consistency checks after |
| any | `bilingual-courseware` | Bilingual/EMI courses — glossary before the first translated artifact, sync checks on paired materials |
| 0–1 / 4 | `cohort-analyst` | Professor holds student readiness data — pre-term diagnostic before Stage 1 design; pre-lesson questionnaires feed week-N calibration in the Stage 4 loop. Aggregates only; never auto-initiated on individuals |

## Does NOT Trigger

Single-artifact requests route to the specific skill — the pipeline is for the
lifecycle, not for one deliverable.

| Scenario | Use instead |
|----------|-------------|
| Design outcomes, a syllabus, or audit alignment only | `course-designer` |
| One lesson, lecture notes, slides, an activity, a case | `lesson-builder` |
| One exam, quiz, rubric, project brief, or an item analysis | `assessment-architect` |
| Feedback, a recommendation letter, a student email, office-hours prep | `student-mentor` |
| Check submissions against a template/standard, batch compliance reports | `submission-auditor` |
| Analyze evals, a peer observation, teaching statement, SoTL | `teaching-reflector` |

## Outputs

- `course_passport.yaml` — maintained continuously; the design, state, and audit record
- Stage artifacts produced via the sibling skills (syllabus, lesson packages,
  instruments, reports), each registered in passport `artifacts[]` with provenance
- Status reports (`status` mode) — stage, gates, pending confirmations, calendar
  position, next actions
- Iteration record (Stage 6) — `iteration_history` entry + prioritized change list +
  redesign brief for next term

## References

- `ts/teaching-pipeline/references/pipeline_state_machine.md` — formal states, entry invariants,
  transitions, resumption algorithm
- Shared: `ts/shared/course_passport_schema.md`, `ts/shared/alignment_gate_protocol.md`,
  `ts/shared/quality_gate_protocol.md`, `ts/shared/checkpoint_protocol.md`,
  `ts/shared/ai_era_integrity.md`, `ts/shared/pedagogy_foundations.md`
