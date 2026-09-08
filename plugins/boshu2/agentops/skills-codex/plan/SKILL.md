---
name: plan
description: 'Shape or refine the existing bead or caller intent without a second planning artifact. Triggers: "plan", "discover and plan", "shape this goal", "review write scope", "check scope boundaries", "scope this change".'
---
# Plan

Turn the caller's intent into one bounded, testable behavior in the place that
already owns the work. Prefer the caller's tracker, if any; otherwise the
caller's conversation or supplied text, which the runtime snapshots so later
contexts read and hash the same bytes.

## Prompt

```text
Plan bead ag-1234: "ao gate check lists the probe-coverage row". Shape it in
the bead itself: one active behavior, acceptance examples, non-goals, write
scope as a class (cli/internal/gates/** plus regen outputs), first check
`cd cli && go test ./internal/gates/...`. Update the bead in place.
```

## It's working if

- The bead or issue text itself gains acceptance, non-goals, and write scope;
  no plan file appears under `.agents/` in the diff.
- Write scope names a regen class (`skills/**` plus every output of
  `scripts/regen-all.sh`), not a hand-enumerated path list.
- The plan names one first check as a runnable command, such as
  `bash scripts/check-x.sh`, and a fresh context given only the source can
  start Implement.
- On a risky write scope the plan names the evidence the change will orphan,
  rather than leaving it for verify time.

## Workflow

1. Resolve the intent source and choose one active behavior. When the source
   is not durable, have the runtime pass its exact bytes to the validate
   skill's `scripts/validate.py snapshot-intent --source -` (under
   `skills/validate/` in a checkout, `.agents/skills/validate/` when
   installed) and carry the returned `intent_ref` into later phases.
2. Route the work by type (Integrate, Extend, or Greenfield) and name its
   ground truth, control experiment, and deviation ledger first from
   [references/ground-truth-routing.md](references/ground-truth-routing.md).
   Then inspect only enough real context to make paths, interfaces, and
   evidence concrete, carrying citations forward; research and specialist
   skills are advisory inputs.
3. Ensure the source contains acceptance examples, important non-goals, and the
   allowed write scope. Name the write scope, its effect on acceptance and
   enforcement under [`validate`](../validate/SKILL.md)'s risk rule (unknown risk
   takes stronger review), the caller's `repair_rounds`, the named acceptance
   gap and discriminating check that would establish progress, and the evidence
   this change will orphan: bound scorecards
   or contracts whose evaluator files sit in the write scope. Run
   `bash scripts/evidence-orphans.sh <write scope>` to see that list rather than
   guessing it, and budget recapturing it as work this plan carries, not a
   discovery for verify time. Use lightweight prose or Given/When/Then only
   where it removes ambiguity. Write-scope checks (folded from the retired
   `scope` skill):
   - patterns are normalized repository-relative paths;
   - includes cover the behavior without granting unrelated directories;
   - excludes do not contradict required changes;
   - generated companions that must move with the sources are explicit;
   - no ownership, scheduling, Git, hook, retry, release, or delivery state.
4. Name the first useful acceptance check.
5. If authorized and the source is writable, update that bead or issue in
   place. Otherwise return a concise proposed amendment to the caller.

## Scope admission

At scope, read `boundaries.md` in the rpi skill's `references` directory for
what Plan does not own. In a repository with generated projections, write
scope names generator-owned outputs as a class (the hand-edited sources plus
all outputs of the owning regen commands), because a hand-enumerated list is
falsified the first time a regen command rewrites an unlisted companion.
Before freezing acceptance, enumerate the generated companions, parity twins
such as `skills-codex/`, and tests asserting on the changed paths;
anything unadmitted here surfaces later as an out-of-scope diff or a broken
gate.

A plan is done only when it passes the fresh-context test: a cold context,
given the intent source alone, could execute it. Move any fact that lives only
in the planning conversation into the source before freezing.

Planning produces no AgentOps packet: the runtime carries the source's
reference and digest to detect acceptance drift. Bound the work around the
caller-visible outcome, not files, gates, or reviewer comments; decompose only
when it reduces reasoning cost. An explicitly selected bounded outer goal may
admit a different experiment after informative red within unchanged terminal
acceptance and remaining allowance. A new hypothesis is not an acceptance
expansion; recurrence alone is not proof that the design is wrong. Do not reopen
an accepted plan merely to produce another control artifact.
