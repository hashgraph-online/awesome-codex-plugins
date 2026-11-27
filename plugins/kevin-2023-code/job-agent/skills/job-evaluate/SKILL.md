---
name: job-evaluate
description: "Decide whether one posting is worth applying to. Scores it A–F on six weighted dimensions against the candidate's goals, maps every must-have to evidence in their résumé, adds TrueInterview's match score and the company's real interview record when connected, and writes a two-minute report. Use when the candidate pastes a posting or link, asks \"is this worth applying to?\", \"am I a fit?\", or after a scan to go deeper on a shortlist."
---

# Evaluate a posting

> Connected vs local mode, the workspace, the `job-agent <command>` scripts and the rules: the `job-agent` skill (or `AGENTS.md`). Read it once per session.

`docs/scoring.md` (in the job-agent folder) defines the dimensions, weights and grade bands. Read it once per session.

## Steps

1. **The posting.** A trueinterview.io link → `get_trueinterview_resource`. A job id → `get_job`. An employer link → fetch it (a LinkedIn or Indeed listing: ask for the employer's own link too; it has the full text and the real form). Note if it looks closed or older than 60 days.
2. **Already in play?** Connected: `get_job` and `prepare_application` say `already_tracked`; or `list_applications`. Local: `job-agent track find "<company>"`. If they applied or skipped it, say so first.
3. **The candidate.** Connected: `get_resume`, `list_context_notes`. Local: `profile/profile.yml`, `profile/cv.md`. Both: `job-agent kb search "<company>"` for their own notes, past loops or a recruiter thread.
4. **Fit score.** Connected: `match_resume_to_job` (`job_id`, or `job_description` with the posting text). Use its per-dimension scores and missing skills as evidence for your own scoring, not a replacement for it.
5. **The company.** Connected: `get_company_intel` (process, rounds, topic mix, how loops reported have gone). With a search tool: layoffs, funding, a freeze or reorg in the last six months. Two or three facts.
6. **Score** the six dimensions, one line of reason each. Check deal-breakers first (any hit caps at D, name it).
7. **Must-haves.** Each hard requirement: `met` with the résumé line that shows it, `partial`, or `missing`. Don't stretch.
8. **Report** to `reports/<company>-<role>-<yyyymmdd>.md` (template below).
9. **Record it.** Connected: `track_application` with `status: "saved"` and a one-line `note` with the grade, only if they want to keep it; if they rule it out, `skip_job` with `why`. Local: `job-agent track add --company … --role … --url … --status evaluated --grade <G> --report <path>`.
10. **Answer in five lines or fewer**: grade and verdict, the two strongest reasons, the biggest gap, the next step (tailor and apply / skip / talk to someone there first via `job-outreach`).

## Report template

```markdown
# <Company> — <Role>
<url> · evaluated <yyyy-mm-dd> · **Grade <G> (<score>/100) — <Apply now | Apply | Maybe | Skip>**
<TrueInterview match: NN% — when connected>

## Verdict
Two or three sentences.

## Scores
| Dimension | Score | Why |
| --- | --- | --- |
| Role & level fit | x/25 | … |
| Skills match | x/25 | … |
| Odds | x/15 | … |
| Company & team | x/15 | … |
| Comp & logistics | x/10 | … |
| Goals | x/10 | … |

## Must-haves
| Requirement | Status | Evidence |
| --- | --- | --- |

## Their interview
Process and rounds as reported (source), the topics that come up most. "No data" if none.

## Gaps and how to handle them
## Angle for the CV
## Red flags
## Questions to ask them
```

## Several at once

Connected: `screen_jobs` with up to 10 ids and `match: true`, then full reports only on the ones they pick. Local: quick pass on title, level, location and deal-breakers first.
