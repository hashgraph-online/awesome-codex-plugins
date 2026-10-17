# Weekly Email — {{course_code}} · Week {{N}} · {{send_date}}

**Subject:** [{{course_code}}] Week {{N}} — {{one_headline_item — the single most
action-relevant fact this week, e.g., "quiz Thursday, project proposals back"}}

---

{{greeting — calibrated from professor's prior emails; default plain: "Hi everyone,"}}

## This week

{{this_week_items — one line each, deadline bolded, from passport schedule[W{{N}}] and
assessment_plan; lead with whatever is due soonest:}}

- {{due_item — e.g., "Problem set 4 due **Wednesday, Oct 8, 17:00** — submit via
  {{submission_route}}"}}
- {{in_class_item — e.g., "Thursday: quiz on weeks 4–5 (15 min, closed book, 5%)"}}

## Next week

{{next_week_prep — what to prepare, from schedule[W{{N+1}}]; only items requiring
student action before the class meeting:}}

- {{prep_item — e.g., "Read {{reading_ref}} before Tuesday — we'll work problems
  from it in class"}}
- {{upcoming_deadline_radar — anything due within ~2 weeks worth a forward flag}}

## Changes

{{changes_block — OMIT THIS SECTION ENTIRELY IF NONE. Echoes of already-announced
changes are marked as repeats: e.g., "(Repeat from Tuesday's announcement) Thursday's
lecture is in **B204**."}}

---

{{help_footer — from passport policies + professor-supplied routes; identical wording
every week so it's findable, e.g.: "Stuck? Office hours {{office_hours}}, course forum
{{forum_link}}, or reply to this email. Late work: see the late policy, syllabus §{{n}}."}}

{{professor_signoff — calibrated from prior emails; never AI-generic}}

---
---

## Instructor-side block (not sent — delete before sending, or keep for your records)

### Fact trace

Every factual claim above, sourced:

| Claim in email | Passport field / source |
|----------------|------------------------|
| {{claim_1 — e.g., "PS4 due Wed Oct 8"}} | {{source — e.g., assessment_plan[A4].week + term calendar}} |
| {{claim_2 — e.g., "quiz counts 5%"}} | {{source — e.g., assessment_plan[A5].weight}} |
| {{claim_3}} | {{source — or [NEEDS PROFESSOR INPUT: ...] if shipped as a visible gap above}} |

### Consistency check

- [ ] Dates/weights above match the syllabus — {{check_result — any contradiction is a
  BLOCK-grade flag, resolved before this draft is sent}}
- [ ] Dates above match the course site schedule table — {{check_result}}
- [ ] Changes block matches what was actually announced (comms_calendar) — {{check_result}}
- Comms-calendar items folded in or flagged this week: {{comms_planner_notes —
  e.g., "A1 logistics email due by Friday (2-week rule) — drafted separately"}}

> ⚠️ **Draft only (non-removable):** This skill does not send email. Review the facts
> above against your own records, fill any [NEEDS PROFESSOR INPUT] markers, and send it
> yourself. Status in `comms/comms_calendar.md` moves to `sent` only when you confirm.
