---
name: reality-check
description: 'Audit claims that work is done or shipped against the diff or repo. Use when: asked whether something really got done, even if it looks obvious.'
practices: [design-by-contract, evidence-based-engineering]
hexagonal_role: domain
consumes: [caller-question, native-source-evidence]
produces: [reality-check-report.v1, goal-measurement-report, native-status-snapshot]
context_rel:
- kind: supplier-to
  with: plan
skill_api_version: 1
user-invocable: true
metadata:
  tier: judgment
  dependencies: []
  capabilities: [compare_claim_to_evidence, measure_declared_goals, report_native_status]
  effects: [write_advisory_gap_report, write_goal_snapshot, write_requested_rendered_spec]
  canonical_status: canonical
  disposition: keep_strategy
output_contract: cited claim comparison; validated reality-check-report.v1 for durable gap reports; measured goal results or observable native status
---
# Reality Check

Compare an expected state with observable evidence, measure declared goals, or
report native status. Select the requested question; a snapshot needs no
invented completion claim. Return facts and gaps without selecting work.
Neighbours: advice on a plan or change is [Review](../review/SKILL.md); an
acceptance verdict on a finished change is [Validate](../validate/SKILL.md).

## Claim comparison

Enumerate every stated claim, including work that was never started, and give
each its own disposition: **confirmed** (cite the evidence), **gap** (cite what
is missing or contradicts it) or **unverifiable** (name the evidence that would
settle it). The named failure mode is auditing only what the diff touched: a
claimed item with no trace in the evidence is a gap, not something to leave out
of the report.

1. Read the exact claim and its source, and split it into its separate items.
2. Inspect the relevant files, command outcomes and artifacts, separating
   confirmed behavior, concrete gaps, incomplete evidence and changed
   assumptions. Credit only what the evidence shows: a reported run without its
   output, behavior left to a default or another component, and a test that
   exercises code without asserting the claimed outcome are unverifiable, not
   confirmed. Name the missing evidence instead of resolving an untestable
   claim by assertion.
   For a claim that behavior is implemented, search the code behind it for
   pretend implementations: constant or hard-coded results, TODO or
   not-implemented branches, sample data, or test doubles outside test code.
   Trace each hit to its callers before classifying it. A placeholder that a
   production path reaches makes the item a gap; a double used only by tests,
   or code nothing calls, does not.
3. When asked about a plan, compare proposed scope with the original goal;
   additions that lack authority are scope escalation the report cannot approve.
   Repeated measurements reuse the same question and criteria; a changed
   question starts a different comparison.
4. Return the ledger with checked and not-checked scope. Keep native tracker,
   Git, runtime, deterministic-check and semantic-judgment facts distinct.

```text
Claim: <the claim as stated, and where it came from>
| # | Stated item | Disposition | Evidence, or what would settle it |
|---|---|---|---|
| 1 | <item> | confirmed / gap / unverifiable | <file:line, command output, artifact> |
Checked: <what was inspected>. Not checked: <what was not>.
```

The ledger reports evidence; it carries no verdict, readiness call or PASS.

A quick answer is inline. A selected durable gap report uses
`reality-check-report.v1`: write `reality-check-report.json` under the caller's
chosen destination, default `.agents/scratch/reality-check/<run-id>/`, and check
it with this skill's `scripts/validate-output.sh <report.json>`. Record the
claim, evidence-backed finding kinds and the per-item dispositions in
`coverage`. The format permits no `verdict`, `readiness` or `PASS` field;
observations are not independent semantic judgment.

## Establish the requested outcome

A request to check a stated claim (done, shipped, fixed, every item complete)
against the evidence selects the claim comparison above without another
question; so do explicit requests to measure declared goals or report native
status. A bare readiness question with no claim and no settled purpose is
ambiguous: ask once whether the caller wants advisory findings or an acceptance
judgment, and wait. A claim audit is not acceptance and cannot substitute for
Validate's fresh, author-distinct judgment. If acceptance is wanted, hand off and
report a missing fresh reviewer as a gap, never as validation that occurred.
Shared routing and handoff detail:
[advice or acceptance](../review/references/advice-or-acceptance.md).

## Health snapshot

For "is this repository healthy" or "do the checks pass", run the project's
own read-only checks: those declared in its instructions or CI configuration,
or found in its build files. Prefer a `--check`, dry-run or verify variant
when one exists. List any step that writes tracked files, publishes, deploys
or needs credentials as not run, with the reason. Record what you selected and
where it came from. Run each one separately and keep going after a failure so
later results are not lost.
Report each check as passed, failed, not run because the tool is unavailable,
or not determined because its output could not be captured, and take the result
from the exit status rather than from parsing the output. Name declared checks
you did not run. Do not fix anything, and do not fold the results into one
score that hides a failure.

## Goal measurement

Running `ao goals` against the declared goals source, its derived snapshots and
what to return are in [goals](references/goals.md). Do not add, remove,
prioritize, migrate or repair goals, or turn a measurement gap into assigned work.

## Native status

Reading the evidence store with `ao status`, and what a snapshot cannot show,
are in [status](references/status.md). A recent artifact timestamp proves
evidence recency, not an active worker.

## Boundary

Return the selected report or snapshot. This skill neither changes native state
nor issues semantic PASS, repairs records, schedules or retries work. The
documented goal snapshots and requested report/spec writes are its only output
side effects. A native caller pursuing an authorized outcome uses these facts
and continues its work; the reporting mode does not decide completion for it.
