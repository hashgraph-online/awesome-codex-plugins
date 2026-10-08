# Cohort Profile — {{course_code}}: {{course_title}}

**Instrument:** {{instrument_title_and_type — e.g., "W0 prerequisite diagnostic,
ungraded, 9 items (5–10 min)"}} · **Administered:** {{date}}
**Respondents:** N = {{N}} of {{enrolled}} enrolled ({{response_rate}}% response)
**Instrument strength:** {{one line from analytics_honesty.md §1 — e.g., "diagnostic
quiz, 1–2 items per concept: flags concepts, does not measure them; supports
lesson-level calibration, not structural redesign"}}

> **Reading this profile honestly:** These findings come from {{instrument_short}} —
> a coarse signal: {{k}} items per concept can flag a concept, not measure it.
> N = {{N}} of {{enrolled}} ({{response_rate}}% response); non-respondents are not
> random and skew toward the students a diagnostic most concerns, so aggregates
> describe **respondents**, not the class. Self-report items measure confidence, not
> ability, and are sectioned separately. This profile describes the cohort's current
> evidence on one date; it does not predict any individual student's future, and no
> finding here should become a label attached to a student. *(This block is not
> removable — analytics_honesty.md §1–§4.)*

## Per-concept readiness

{{One row per probed concept. Distribution sketch, not just a rate — counts per
outcome band, e.g., "▰▰▰▰▰▰▱▱▱▱ 31/52".}}

| Concept | Recall correct | Transfer correct | Distribution sketch | Reading |
|---------|---------------|------------------|---------------------|---------|
{{rows — e.g., "Pointers | 38/52 (73%) | 16/52 (31%) | recall ▰▰▰▰▰▰▰▱▱▱ · transfer ▰▰▰▱▱▱▱▱▱▱ | recall solid, transfer weak → inert knowledge pattern"}}

## Misconception prevalence *(two-tier logic — counted separately)*

| Misconception | Right answer + right reasoning | Right answer + WRONG reasoning | Wrong answer, misconception reasoning | Other / guessed |
|---------------|-------------------------------|--------------------------------|---------------------------------------|-----------------|
{{rows — counts of N respondents; the right-answer-wrong-reasoning column is often
the largest actionable finding}}

## Heterogeneity assessment

{{Shape per concept and overall: roughly uniform / skewed / bimodal — with the
teaching implication named, e.g., "Programming experience is bimodal (19/52 none,
23/52 one course or more): differentiation case, not a pace change." Below small-N
thresholds: "too few responses to characterize" (analytics_honesty.md §4).}}

## Self-report findings *(SELF-REPORT — confidence, not measured ability)*

{{Confidence/self-efficacy aggregates, kept strictly out of the readiness sections.
Where a concept has both a measured item and a confidence item, report the
calibration gap at cohort level — e.g., "recursion: mean confidence 3.9/5 (label:
convention applied to ordinal data) vs 31% transfer-correct — the cohort over-rates
this concept (analytics_honesty.md §3)". Delete section if no self-report items.}}

## Proposed passport update *(aggregates only — written ONLY after 🧑 confirmation)*

```yaml
learner_profile:
  cohort_evidence:
    - instrument: "{{instrument_title_and_type}}"
      date: "{{date}}"
      n: {{N}}
      enrolled: {{enrolled}}
      response_rate: {{response_rate}}
      key_aggregates:
        - "{{concept}}: {{recall_pct}}% recall-correct, {{transfer_pct}}% transfer-correct ({{shape}})"
        - "{{further aggregate lines}}"
      heterogeneity: "{{overall shape line}}"
      self_report_note: "{{confidence aggregates, labeled self-report — or 'no self-report items'}}"
  known_difficulties:
    - "{{misconception}} — {{prevalence}}% of respondents chose the {{distractor}} reasoning ({{instrument_short}}, {{date}}, N={{N}})"
```

{{Verbatim — what is shown here is exactly what gets written. No names, no
per-student rows, no individual-level fact (SKILL iron rule 1).}}

## Recommended next actions — routed by skill

| Finding | Recommended action | Routed to |
|---------|-------------------|-----------|
{{rows — each action traceable to a finding above, e.g.:
"Pointers: 31% transfer-correct | reteach via worked-example segment in W2 | lesson-builder (lesson-calibration mode)"
"Schedule assumes recursion fluency by W3; evidence says otherwise | pacing flag — W3 plan review | course-designer (schedule amendment at checkpoint)"
"Gambler's-fallacy reasoning at 38% | seed peer-instruction distractor + exam distractor pool | lesson-builder / assessment-architect"}}

**Individual follow-ups:** this profile contains none, by design. If the professor
wants to support specific students, they initiate that with the evidence they hold —
route to `student-mentor`. This skill does not nominate students.

*🧑 Checkpoint: profile reviewed and passport block confirmed verbatim before
writing (`ts/shared/checkpoint_protocol.md`).*
