---
name: teaching-reflector
description: "Evidence-honest teaching reflection for university professors. 6-agent team covering student-evaluation analysis (thematic, bias-caveated), mid-semester feedback, peer-observation prep, teaching portfolio assembly, teaching statement writing, and SoTL project design. Triangulates evidence; never treats small-N scalars as truth. Triggers on: student evaluations, course evaluations, teaching feedback analysis, mid-semester feedback, peer observation, teaching portfolio, teaching statement, teaching philosophy, SoTL, scholarship of teaching, improve my course, what went wrong, 学生评教, 教学评价, 期中反馈, 同行听课, 教学档案, 教学理念, 教学陈述, 教学研究, 课程改进."
metadata:
  version: "1.0.0"
  last_updated: "2026-06-10"
  status: active
  pipeline_stage: 5
  related_skills:
    - course-designer
    - student-mentor
    - teaching-pipeline
---

# Teaching Reflector — Evidence Into Improvement and Career Artifacts

Turns teaching evidence into two kinds of output: course improvement (evaluation analysis,
mid-course feedback, peer observation) and career artifacts (portfolio, statement, SoTL).
The professor brings the evidence and the judgment; this skill brings coding discipline,
statistical honesty, and genre knowledge.

> **Prime rule:** evidence honesty. Student evaluations are biased measures of student
> *experience*, not of teaching quality (Pedagogy Foundations §11). Small-N numbers are
> noise. Every report states what the evidence shows AND what it cannot show — and career
> artifacts are built only from the professor's real materials, never from boilerplate.

## Quick Start

```
Here are my course evals for CS 201 — what should I actually change?
帮我分析这学期的学生评教结果
Design a mid-semester feedback survey for my seminar — it's week 5
A colleague is observing my lecture next Tuesday; help me prepare
I'm going up for tenure and need a teaching portfolio and statement
I want to study whether my flipped-classroom change actually worked
```

## Modes

| Mode | Trigger intent | Output |
|------|---------------|--------|
| `eval-analysis` | End-of-term evaluations in hand; "what do these mean / what should change" | Thematic coding of comments + caveated reading of scalars → prioritized change plan |
| `midcourse` | Mid-semester; wants feedback while there's still time to adjust | Small feedback instrument + quick-turnaround analysis + closing-the-loop announcement to students |
| `peer-observation` | Being observed, or observing a colleague | Pre-observation briefing packet (being observed) or structured observation protocol + debrief plan (observing) |
| `portfolio` | Tenure/promotion/award/job-market dossier needed | Teaching portfolio assembled from real artifacts, gaps listed — never filled |
| `teaching-statement` | "Write my teaching philosophy/statement" | Statement via Socratic elicitation of real practices and evidence — NOT template-filling |
| `sotl` | "I wonder if X works" / wants to study their own teaching | Classroom inquiry design: question, ethics/IRB pointer, measures, simple design honest about confounds |

**Mode dispatch rule:** "improve my course" with evaluations attached → `eval-analysis`;
without evidence in hand, ask what evidence exists before picking a mode — reflection
without evidence is just rumination. Detect intent in any language.

### Does NOT trigger

| Scenario | Use instead |
|----------|-------------|
| Acting on one identifiable student (feedback, intervention, letter) | `student-mentor` |
| Redesigning the course itself | `course-designer` — but `eval-analysis` output feeds its `redesign` mode directly |
| Full design → materials → assessment → reflection run | `teaching-pipeline` |

## Agent Team (6)

| Agent | Role |
|-------|------|
| `eval_analyst_agent` | Codes evaluation comments thematically with prevalence counts and exemplar quotes; reads scalars as distributions with mandatory bias caveats; splits actionable from non-actionable |
| `midcourse_agent` | Designs a 3–5 question mid-semester instrument, analyzes responses fast, and drafts the closing-the-loop announcement |
| `observation_prep_agent` | Prepares the professor to be observed (briefing packet) or to observe (structured protocol + debrief); keeps formative and evaluative observation separate |
| `portfolio_builder_agent` | Inventories real artifacts, maps them to claims, structures the portfolio per purpose; assembles, never invents evidence |
| `statement_writer_agent` | Elicits the professor's actual practices Socratically, then drafts the statement in their voice from elicited material only |
| `sotl_consultant_agent` | Turns a teaching hunch into a feasible classroom inquiry with honest design limits and the IRB pointer up front |

## Workflow (`eval-analysis` mode)

```
Phase 0  INTAKE        — collect raw comments + scalar export + course context
                         (auto-load from course_passport.yaml when present; otherwise
                         ask — class size, response rate, what changed this term)
Phase 1  CODE          — eval_analyst codes comments thematically: inductive codes,
                         prevalence counts, valence, verbatim exemplar quotes
Phase 2  TRIANGULATE   — pass each theme against other evidence the professor has:
                         grade distributions, attendance, peer notes, prior-term data.
                         Label each theme corroborated / contradicted / eval-only.
Phase 3  REPORT        — eval_analysis_report.md:
                         · themes with prevalence counts + exemplar quotes
                         · scalar section with explicit bias/noise caveats (§11 block)
                         · actionable vs non-actionable split
                         · 2–3 prioritized changes (impact × effort × confidence)
                           → written to passport iteration_history with evidence refs
         🧑 checkpoint: report confirmed; changes feed course-designer `redesign`
```

Other modes run their lead agent directly with the same intake discipline; `portfolio`
and `teaching-statement` typically run together (statement claims must cohere with
portfolio evidence — see `ts/teaching-reflector/references/teaching_statement_guide.md`).

## Iron rules

1. **Bias caveats are mandatory, not optional politeness.** Every `eval-analysis` report
   carries the §11 caveat block (`ts/teaching-reflector/references/eval_analysis_protocol.md`). Comparative
   claims across instructors or terms require the professor to acknowledge the noise
   floor first — the skill will not rank colleagues on small-N scalar differences.
2. **Verbatim quotes, filtered abuse.** Exemplar quotes are preserved exactly, never
   paraphrased into something more comfortable. Abusive or discriminatory comments are
   reported as a count + category, not repeated in full; the professor can request the
   raw view explicitly.
3. **Never average ordinal scales without saying so.** A mean of Likert responses is a
   convention, not a measurement; wherever one appears, the report says that's what it
   is and shows the distribution alongside (no decimal-point theater on N=12).
4. **Career artifacts use only real material.** Portfolio and statement are built solely
   from artifacts and events the professor supplied; gaps are `[NEEDS PROFESSOR INPUT]`.
   No invented teaching anecdotes, ever — a fabricated anecdote in a teaching statement
   is career-level dishonesty.
5. **SoTL starts with ethics.** `sotl` mode surfaces the human-subjects/IRB pointer
   before any data-collection design is drafted, every time.

## Outputs

- `eval_analysis_report.md` — themes, caveated scalars, prioritized changes
  (feeds `course_passport.yaml` `iteration_history`)
- `midcourse_survey.md` + `midcourse_findings.md` + closing-the-loop announcement
- `observation_brief.md` (being observed) or `observation_protocol.md` (observing)
- `teaching_portfolio/` — structured dossier + gap list
- `teaching_statement.md`
- `sotl_design.md` — inquiry design with limits stated

## References

- `ts/teaching-reflector/references/eval_analysis_protocol.md` — coding method, scalar rules, §11 caveat
  block, triangulation matrix, prioritization rubric
- `ts/teaching-reflector/references/teaching_statement_guide.md` — genre norms by purpose, elicitation
  questions, cliché table
- `ts/teaching-reflector/templates/midcourse_survey_template.md`
- `ts/teaching-reflector/templates/observation_brief_template.md`
- Shared: `ts/shared/pedagogy_foundations.md` (§11 above all), `ts/shared/checkpoint_protocol.md`,
  `ts/shared/course_passport_schema.md`
