---
name: reality-check
description: 'Check whether a claimed shipped feature, repo state or goal status holds up in evidence. Use when: comparing a claim with what exists; a gap report is not a verdict.'
---
# Reality Check

Compare an expected state with observable evidence, measure declared goals, or
report native status. Select the requested question; a snapshot needs no
invented completion claim. Return facts and gaps without selecting work.

## Claim comparison

1. Read the exact claim and its source. For a completion claim, enumerate every
   stated goal, including work that was never started. Give each a disposition:
   confirmed with evidence, concrete gap or unverifiable.
2. Inspect relevant files, command outcomes and artifacts. Separate confirmed
   behavior, concrete gaps, incomplete evidence and changed assumptions. Name the
   missing evidence instead of resolving an untestable claim by assertion.
3. Compare proposed scope with the original goal when asked about a plan. Report
   additions that lack authority as scope escalation; the report cannot approve
   them. Repeated measurements use the same question and criteria; a changed
   question starts a different comparison.
4. Return the cited findings with checked and not-checked scope. Keep native
   tracker, Git, runtime, deterministic checks and semantic judgments distinct.

A quick answer can be inline. A selected durable gap report retains
`reality-check-report.v1`: write `reality-check-report.json` under the caller's
chosen destination, default `.agents/scratch/reality-check/<run-id>/`, and run
`skills/reality-check/scripts/validate-output.sh <report.json>`. Include the
checked claim, evidence-backed finding kinds and goal-by-goal dispositions for
completion/status claims. This format permits no `verdict`, `readiness` or
`PASS` field; observations are not independent semantic judgment.

## Goal measurement

Inspect the declared goals source; prefer `GOALS.md` when it and legacy YAML
both exist. Preserve directive and gate identities and report each executable
check with its actual outcome. Run the requested `ao goals` command once:
`measure --json`, `validate --json`, `drift`, `history`, `export`, `meta --json`,
`scenarios` or `render`.

These commands do not edit the goals source, but `measure`, `drift` and `export`
may write best-effort derived snapshots under `.agents/ao/goals/baselines/`.
`render --out <file>` writes a caller-selected spec; never target the goals
source or another non-derived file. Use stdout when no output file is requested.
Return command, exit code, goal-level results, aggregate measurement, missing
evidence and checked/not-checked scope. Do not add, remove, prioritize, migrate
or repair goals, or turn a measurement gap into assigned work.

## Native status

Use `ao status` for the local evidence-store view. It validates content-addressed
intent and verdict artifacts before counting them, reports corruption or
unavailable sources, and shows evidence recency. Its durable stores are
`.agents/ao/intents/sha256` and `.agents/ao/verdicts/sha256`; a count is not a
per-artifact digest inventory. Inspect a specific digest or timestamp only when
that artifact is part of the requested question.

Report caller-supplied subject manifests from their named location. Otherwise
mark manifests, runtime phase, elapsed execution, tool-call activity and remaining
work as not checked. An artifact's recent timestamp proves evidence recency,
not an active worker. Read other tracker, Git or factory facts only from their
own authorized source; do not blend factory completion, green checks and a
fresh verdict into one health judgment. Report unavailable evidence explicitly.

## Boundary

Return the selected report or snapshot. This skill neither changes native state
nor issues semantic PASS, repairs records, schedules or retries work. The
documented goal snapshots and requested report/spec writes are its only output
side effects. A native caller pursuing an authorized outcome uses these facts
and continues its work; the reporting mode does not decide completion for it.
