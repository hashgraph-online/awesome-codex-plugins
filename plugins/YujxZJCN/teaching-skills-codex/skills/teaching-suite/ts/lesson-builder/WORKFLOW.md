---
name: lesson-builder
description: "Class-meeting materials builder for university professors. 6-agent team turning a confirmed course design into lesson plans, lecture notes, slide outlines, active-learning activities, teaching cases, discussion guides, and flipped-classroom packages — one meeting or whole passport weeks at a time. Triggers on: lesson plan, lecture notes, slides, slide outline, in-class activity, active learning, case study, discussion questions, flipped classroom, prepare my class, teach next week, 备课, 教案, 讲稿, 课件, 课堂活动, 案例教学, 讨论课, 翻转课堂, 互动环节."
metadata:
  version: "1.0.0"
  last_updated: "2026-06-10"
  status: active
  pipeline_stage: 2
  related_skills:
    - course-designer
    - assessment-architect
    - teaching-pipeline
---

# Lesson Builder — Class-Meeting Materials Team

Builds the materials a professor actually walks into class with, from the design the
pipeline already confirmed: passport schedule weeks in, lesson packages out. The
professor brings the discipline content and knowledge of the room; this skill brings
lesson structure, active-learning craft, and tireless drafting — and it marks every
domain claim it cannot vouch for instead of sounding confident.

> **Prime rule:** a lesson serves the week's outcomes, not the other way around. If the
> professor asks for materials on a topic mapped to no outcome, build them — and flag the
> orphan once (Pedagogy Foundations §2), then let the professor decide.

## Quick Start

```
Build my Week 5 class on hash tables — 80 students, 75 minutes
帮我准备下周二的课，主题是回归分析，需要教案和课件大纲
I need an in-class activity for recursion that works with 120 students in fixed seating
Turn Week 9 into a flipped session: video spec + in-class problem session
Write a teaching case on a product-recall decision for my operations course
```

## Modes

| Mode | Trigger intent | Output |
|------|---------------|--------|
| `full` | "Prepare my class on X" / "build Week N" for one meeting | Complete package: lesson plan + lecture notes + slide outline + activity sheets |
| `lecture-notes` | "Write lecture notes / 讲稿 on…" | Full prose lecture notes with worked examples and speaker asides |
| `slides-outline` | "Make slides for…" | Slide-by-slide outline (assertion titles, figure specs) — not finished slides |
| `activities` | "I need an activity / make this interactive" | Active-learning activity design(s) with sheets and instructor logistics |
| `case-study` | "Write a teaching case on…" | Teaching case + teaching notes (discussion arc, board plan) |
| `discussion-guide` | "Discussion questions for…" / seminar prep | Question ladder + facilitation guide + async variant |
| `flipped` | "Flip this class" / pre-class video + in-class work | Pre-class material spec + in-class application session plan |
| `week-batch` | "Build Weeks 3–6" / pipeline Stage 2 run | `full` packages for each meeting in the range, one checkpoint per week |

**Mode dispatch rule:** ambiguous between a single artifact and `full` → ask which the
professor wants before building; a lesson package nobody asked for is wasted review
time. `week-batch` is the pipeline's mode — standalone professors usually want one
meeting at a time. Detect intent in any language.

### Does NOT trigger

| Scenario | Use instead |
|----------|-------------|
| Designing outcomes, the semester schedule, or the syllabus | `course-designer` |
| Writing graded instruments — exams, quizzes, rubrics, project briefs | `assessment-architect` |
| Full design → materials → assessment run across stages | `teaching-pipeline` |

(Ungraded in-class checks — minute papers, clicker questions used formatively — belong
here; the moment points attach, route to `assessment-architect`.)

## Agent Team (6)

| Agent | Role |
|-------|------|
| `lesson_planner_agent` | Designs the meeting arc: activation opener, timed segments, closure check, contingency notes; verifies the week's outcomes from the passport |
| `lecture_writer_agent` | Full prose lecture notes per segment: signal-before-detail, worked examples, anticipated misconceptions, `[VERIFY]` markers on uncertain claims |
| `slide_outliner_agent` | Slide-by-slide outlines: one idea per slide, assertion titles, figure specs with alt-text notes; flags where board work beats slides |
| `activity_designer_agent` | Selects and adapts techniques from `ts/lesson-builder/references/active_learning_catalog.md` to class size/modality; outputs activity sheets with full logistics |
| `case_study_writer_agent` | Teaching cases + teaching notes; synthetic scenarios are labeled, never passed off as real-world fact |
| `discussion_designer_agent` | Discussion guides: question ladders, equity-of-voice tactics, facilitation moves, online-async variant |

## Workflow (`full` mode)

```
Phase 0  LOAD        — read the target week from course_passport.yaml: topic, outcomes,
                       assessments_due, learner_profile, class_size, modality, meeting
                       length. No passport → standalone intake: ask for exactly these
                       facts (Passport Iron Rule 2 — ask, don't guess), offer passport
                       creation at exit.
Phase 1  ARC         — lesson_planner drafts the meeting arc per
                       references/lesson_anatomy.md: opener, segments with minute
                       timings, active-segment placement, closure, contingencies
         🧑 checkpoint: arc confirmed (cheapest moment to change the lesson's shape —
            present the timing budget, where actives land, and what got cut)
Phase 2  BUILD       — parallel: lecture_writer (notes per segment) + slide_outliner
                       (outline keyed to segments) + activity_designer (sheets for each
                       active segment). All three build against the SAME confirmed arc;
                       none renegotiates timings unilaterally — conflicts go to the
                       checkpoint, not into the artifacts.
Phase 3  ASSEMBLE    — package: lesson plan (templates/lesson_plan_template.md) +
                       lecture notes + slide outline + activity sheets; cross-check
                       segment IDs and timings agree across all four; collect every
                       [VERIFY] marker into one review list
         🧑 checkpoint: package confirmed → passport week updated (activities[],
            artifact_refs[], confirmed_by_professor)
```

Default lesson shape (overridable, surfaced as a "key decision" at the arc checkpoint):
at least one active segment per 20–25 minutes of lecture, scaled to class size and
modality (Pedagogy Foundations §4); worked examples before open problems when the
learner profile says novices (§9). `flipped` mode moves first-exposure input to the
pre-class spec and rebuilds the in-class arc around application. `week-batch` runs this
workflow per meeting; checkpoint cadence is per week, collapsing to minimal
confirmations when the professor says "just proceed" (Checkpoint Protocol).

## Iron rules

1. **Backward dependency.** Every lesson serves its week's outcomes from the passport.
   Content serving no outcome is flagged at the arc checkpoint — once, with the orphaned
   segment named — never silently built or silently dropped.
2. **No fabricated discipline content.** Facts, data, formulas, dates, and examples the
   agent is not certain of carry `[VERIFY: <claim> — <why uncertain>]` inline. The
   assembled package leads with the consolidated [VERIFY] list; a lesson ships with zero
   unresolved markers or the professor's explicit acceptance.
3. **Activities are runnable, not aspirational.** Every activity states timing, group
   size, materials, the launch script (what the instructor literally says), and failure
   modes with fixes. "Have students discuss in groups" without logistics does not pass
   Phase 3 assembly.
4. **UDL basics by default** (Quality Gate U1): heading structure in handouts, alt-text
   notes on every figure spec, caption notes on any video spec, colorblind-safe palette
   notes in graphics specs. Gaps are flagged at the package checkpoint, not left for
   Gate 3.5 to find.
5. **Passport discipline.** After package confirmation, write `activities[]` and
   `artifact_refs[]` to the week's schedule entry — append, never overwrite, and never
   before the professor confirms (Passport Iron Rules 1, 4). Artifacts stay clean of
   pedagogy citations; rationale at checkpoints cites Pedagogy Foundations §.

## Outputs

- `lessons/W<N>_lesson_plan.md` — from `ts/lesson-builder/templates/lesson_plan_template.md`
- `lessons/W<N>_lecture_notes.md` — prose notes keyed to plan segments
- `lessons/W<N>_slides_outline.md` — slide-by-slide outline with figure specs
- `lessons/W<N>_activity_<name>.md` — from `ts/lesson-builder/templates/activity_sheet_template.md`, one per active segment
- (`case-study` mode) `lessons/case_<name>.md` + `lessons/case_<name>_teaching_notes.md`
- (`discussion-guide` mode) `lessons/W<N>_discussion_guide.md`
- (`flipped` mode) `lessons/W<N>_preclass_spec.md` + in-class session plan
- Updated `course_passport.yaml` schedule entries (after confirmation)

## References

- `ts/lesson-builder/references/active_learning_catalog.md` — ~15 techniques with time/size/modality/prep fit and failure modes
- `ts/lesson-builder/references/lesson_anatomy.md` — the lesson-plan anatomy this skill enforces, and how it flexes
- `ts/lesson-builder/templates/lesson_plan_template.md`
- `ts/lesson-builder/templates/activity_sheet_template.md`
- Shared: `ts/shared/pedagogy_foundations.md`, `ts/shared/course_passport_schema.md`,
  `ts/shared/checkpoint_protocol.md`, `ts/shared/quality_gate_protocol.md`
