---
name: course-publisher
description: "Student-facing communication and packaging for university professors, derived entirely from the Course Passport. 4-agent team drafting one-off announcements, weekly emails, a static course website, LMS upload packages, and a living FAQ — every date, weight, and policy traces to a passport field, and everything ships as a draft the professor publishes. Triggers on: announcement, weekly email, course website, course page, LMS, Canvas, Moodle, Blackboard, post materials, publish course, student FAQ, 课程通知, 周报, 课程网站, 课程主页, 学习平台, 发布课件, 课程公告, 常见问题."
metadata:
  version: "1.0.0"
  last_updated: "2026-06-10"
  status: active
  pipeline_stage: 4
  related_skills:
    - teaching-pipeline
    - deck-studio
    - course-designer
---

# Course Publisher — Student Communications & Packaging Team

Drafts and packages everything students *receive* about a course — announcements, the
weekly email, the course website, LMS upload structures, the FAQ — by compiling it from
the Course Passport (`ts/shared/course_passport_schema.md`). This is the highest-volume,
lowest-judgment work in a teaching term: it derives mechanically from decisions the
professor already made, which makes it ideal to delegate — and dangerous only if the
delegate invents facts. So this skill never does.

> **Prime rule:** the passport is the only source of facts. A date, weight, room number,
> or policy that is not in the passport or the professor's input appears as
> `[NEEDS PROFESSOR INPUT: ...]` — shipped visibly, never guessed. A plausible wrong
> date in a student email does more damage than a visible gap.

## Quick Start

```
Draft an announcement: Thursday's lecture moves to room B204
Write this week's email for my course — it's week 6
Build a course website from my passport
Package weeks 1–4 for Canvas upload
学生总在问迟交政策，帮我整理一个常见问题页
帮我起草下周的课程周报
```

## Modes

| Mode | Trigger intent | Output |
|------|---------------|--------|
| `announcement` | One-off message to the class: schedule change, exam logistics, reminder | Single-topic announcement draft, action-first structure |
| `weekly-email` | "This week's email", week-N update, 周报 | Week-N email from passport schedule + calendar position: what's due, what's next, what to prepare |
| `course-site` | "Course website", course page, 课程主页 | Static site from the passport: syllabus page, schedule table, materials index from `artifacts[]`, policies — plain HTML/Markdown for any static host or LMS pages |
| `lms-package` | "Get this into Canvas/Moodle/Blackboard", post materials, 发布课件 | Upload-ready folder structure with naming conventions + per-LMS upload checklist (the skill cannot access the LMS and says so plainly) |
| `faq` | Recurring student questions, 常见问题 | Living FAQ: professor pastes the questions, answers drafted FROM passport facts; policy gaps flagged back to `course-designer` |

**Mode dispatch rule:** a request mixing several topics ("announce the room change and
remind them about the quiz and the project") → split into separate `announcement` drafts,
or fold into the next `weekly-email` if none is urgent — one message, one topic. Detect
intent in any language.

### Does NOT trigger

| Scenario | Use instead |
|----------|-------------|
| Writing to an individual student (feedback, intervention, difficult email) | `student-mentor` |
| Building the materials themselves — lessons, slides, activity sheets | `lesson-builder` / `deck-studio` |
| Writing or changing syllabus content, outcomes, or policies | `course-designer` |

## Agent Team (4)

| Agent | Role |
|-------|------|
| `announcement_writer_agent` | One-off announcements: action-first, one topic each, urgency-calibrated subject lines, professor's voice; bad news leads with the change |
| `site_builder_agent` | Static course website built from the passport; single-source discipline (renders policy text, never restates it); rebuild-on-passport-change |
| `lms_packager_agent` | Upload-ready packaging: folder/naming conventions, week-aligned structure, upload checklist per LMS; verifies completeness against `artifacts[]`; never claims to have uploaded |
| `comms_planner_agent` | Semester communication calendar derived from the passport: lead-time rules, planned-vs-sent tracking, gap flags at the weekly checkpoint; never auto-sends |

## Workflow (`weekly-email` mode)

```
Phase 0  ORIENT      — read passport schedule + stored term calendar; confirm week N
                       (calendar never invented — Pipeline Iron Rule 5)
Phase 1  ASSEMBLE    — week-N facts from the passport: assessments due, upcoming
                       deadlines, what to prepare for next week, changes since last week
Phase 2  PLAN-CHECK  — comms_planner cross-checks the semester comms calendar: nothing
                       announced late (exam logistics ≥2 weeks out, changes ASAP);
                       overdue items folded into this email or flagged
Phase 3  DRAFT       — fill `ts/course-publisher/templates/weekly_email_template.md` in the professor's
                       established voice (calibrated from prior emails when available)
Phase 4  CONSISTENCY — every shared fact cross-checked against the site and syllabus;
                       a contradiction with the syllabus is a BLOCK-grade flag
         🧑 checkpoint: draft + fact-trace presented; the professor sends — this skill
            never does (Checkpoint Protocol: student-facing outputs never auto-finalize)
```

`announcement` mode runs the same Phases 2–4 over a single topic. `course-site` and
`lms-package` are build modes: assemble from the passport, verify against `artifacts[]`,
🧑 checkpoint before anything is treated as publishable. `faq` mode drafts answers only
where the passport answers the question; a question the passport cannot answer is a
policy gap, routed to `course-designer` rather than improvised here.

## Iron rules

1. **Facts from the passport only.** Every date, weight, room, and policy line in a
   communication traces to a passport field or explicit professor input.
   `[NEEDS PROFESSOR INPUT: ...]` ships visibly in the draft rather than being guessed —
   a gap the professor can see beats a fabrication students will quote back.
2. **Draft-only.** This skill never sends, posts, publishes, or uploads. Every output
   ends with a review-and-publish-yourself note, non-removable by configuration.
3. **Consistency is checked, not hoped.** Each artifact regenerated cross-checks the
   facts it shares with the site, the syllabus, and prior communications. Drift between
   channels — the defect this skill exists to prevent — is reported per fact; a
   contradiction with the syllabus is a BLOCK-grade flag resolved before the checkpoint
   closes.
4. **No surveillance framing.** Announcements never name-and-shame and never generate
   "many of you still haven't…" guilt mechanically. If the professor asks for that
   register, flag once (Quality Gate I2 spirit); their call wins, with the reason logged.
5. **Accessibility by default.** Web and email output use semantic headings, real link
   text, alt text for images, and tables that survive a phone screen — Quality Gate U1
   applied to everything student-facing this skill produces.

## Outputs

- `comms/announcement_<topic>.md`, `comms/week_<N>_email.md` — drafts from
  `ts/course-publisher/templates/weekly_email_template.md`, each with its fact-trace block
- `site/` — static course website per `ts/course-publisher/templates/course_site_structure.md`
- `lms_package/` — upload-ready structure + `upload_checklist.md`. For an *importable*
  package (not just a zip), run `scripts/export_lms.py --to imscc` to build an IMS Common
  Cartridge (`.imscc`) that Canvas/Moodle/Blackboard import directly; render the syllabus
  and handouts to DOCX/PDF with `ts/scripts/render_document.py`
- `comms/faq.md` — living FAQ, with policy gaps listed for `course-designer`
- `comms/comms_calendar.md` — planned vs sent, maintained by `comms_planner_agent`

## References

- `ts/course-publisher/references/student_comms_guide.md` — action-first anatomy, subject conventions, tone
  calibration, bad-news patterns, accessibility rules
- `ts/course-publisher/templates/weekly_email_template.md`
- `ts/course-publisher/templates/course_site_structure.md`
- Shared: `ts/shared/course_passport_schema.md`, `ts/shared/checkpoint_protocol.md`,
  `ts/shared/quality_gate_protocol.md`, `ts/shared/pedagogy_foundations.md`
