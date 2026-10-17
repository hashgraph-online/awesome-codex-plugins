# Calibration Session — {{assessment_id}}: {{assessment_title}}

**Course:** {{course_code}} · **Date:** {{session_date}} · **Length:** {{session_length}}
**Instrument:** {{instrument_ref}} · **Rubric:** {{rubric_ref}} (v{{rubric_version}})
**Graders:** {{grader_list}} · **Grading opens:** {{grading_open_date}}
**Facilitator:** {{professor_name}} — the professor rules on disputed interpretations;
rulings bind everyone, including the professor.

## Anchor set

| Anchor | Why chosen | Expected discussion |
|--------|-----------|---------------------|
| {{anchor_id_1}} | clear-high — {{why}} | {{which criterion boundary it confirms}} |
| {{anchor_id_2}} | clear-low — {{why}} | {{...}} |
| {{anchor_id_3}} | borderline — {{why}} | {{which two levels it sits between, on which criterion}} |
| {{anchor_id_4}} | borderline — {{why}} | {{...}} |

All anchors are anonymized before distribution.

## Pre-work (due {{prework_deadline}})

Each grader, independently — no discussion, no comparing notes:

1. Read the rubric and any existing annotations: {{annotations_ref_or_none}}
2. Score every anchor on every criterion; note the rubric language you leaned on for
   each borderline call
3. Submit scores to {{prework_collection — professor only, not the team channel}}

Independent first scores are the whole point; a shared first impression measures
conformity, not agreement.

## Session agenda

| Time | Segment |
|------|---------|
| {{t0}} ({{m}} min) | Rubric walk: each criterion's intent; the line between its top two levels |
| {{t1}} ({{m}} min) | Reveal all pre-work scores per anchor, per criterion |
| {{t2}} ({{m}} min) | Largest gaps first: locate the rubric language causing each split ≥1 level; professor rules; record the ruling below |
| {{t3}} ({{m}} min) | Converge on each anchor's settled scores; re-score {{confirmation_anchor}} independently to confirm tightening |
| {{t4}} ({{m}} min) | Logistics: flagging no-fit submissions, regrade routing, mid-grading spot-check plan |

## Agreement stats

Computed from pre-work vs. converged scores. With {{n_graders}} graders and
{{n_anchors}} anchors these locate discussion, they certify nothing — small N, stated
in any report.

| Criterion | % within one level | Spread (max−min levels) | Notes |
|-----------|--------------------|-------------------------|-------|
| {{criterion_1}} | {{pct}} | {{spread}} | {{e.g., splits on the borderline anchors only}} |
| {{criterion_n}} | | | |
| **Overall** | {{pct}} | | |

Low agreement after a well-run session = rubric defect (level gap, double-barrel)
before grader problem — route to `assessment-architect`.

## Decisions log

Rulings annotate the rubric; they never rewrite it mid-grading (a rewrite is a flagged
professor decision with regrade implications stated first).

| # | Rubric clause (criterion, level) | Agreed interpretation | Anchor that raised it |
|---|----------------------------------|----------------------|----------------------|
| 1 | {{clause}} | {{ruling}} | {{anchor_id}} |

## Post-session distribution checklist

- [ ] Annotated rubric v{{rubric_version + 1}} assembled: original text untouched,
      dated annotations from the decisions log appended
- [ ] Distributed to **every** grader before {{grading_open_date}}; receipt confirmed
- [ ] Decisions log filed with the rubric artifact ({{artifact_path}}) — next term's
      team inherits the case law
- [ ] Spot-check plan scheduled: {{spot_check_plan — e.g., professor re-scores a sample
      from each grader's first batch; drift >1 level on >20% triggers a targeted re-norm}}
- [ ] Open rubric defects (if any) flagged to `assessment-architect`: {{defects_or_none}}
