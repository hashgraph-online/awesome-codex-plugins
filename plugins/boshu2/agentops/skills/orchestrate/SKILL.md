---
name: orchestrate
description: 'Coordinate several workers: what idle agents do next, which finished work gets checked first, how to recover a dead one. Use when: managing multiple agents.'
practices: [team-topologies, evidence-based-engineering]
hexagonal_role: supporting
consumes: [accepted-intent, native-work-state, candidate-evidence]
produces: [native-handoffs, reconciled-feedback]
context_rel: []
skill_api_version: 1
user-invocable: true
metadata:
  graph_root: true
  tier: execution
  dependencies: []
  capabilities: [coordinate_native_work, recover_assignments, reconcile_feedback]
  effects: [dispatch_authorized_workers, update_native_handoffs]
  canonical_status: canonical
  disposition: keep
output_contract: observed native assignments, exact candidate and judgment references, affected-work handoffs and explicit remaining gaps
---

# Orchestrate

Coordinate caller-authorized work through its existing tracker and runtime; a
clear task needs zero mandatory skills. The tracker owns assignments and
dependencies, the runtime owns running contexts and bounds, and repository
policy owns integration and delivery. Orchestrate decides what each worker does
next. [Agent Native](../agent-native/SKILL.md) launches and observes workers;
[Navigate](../navigate/SKILL.md) picks the wave on a bead graph toward frozen
acceptance and records verdicts.

## Before any dispatch

- **Finished is not done.** Exit 0, a pushed branch, a closed tracker item or a
  worker saying "done" makes a candidate. It still owes its checks, integration
  and, when one is owed, a fresh judgment.
- **Drain before starting.** While candidates wait on checks, repair,
  integration or an owed judgment, free capacity goes there first: candidates
  that unblock held dependents, then the oldest. A free slot alone is not a
  dispatch reason; start new implementation with what is left.
- **Judges did not author.** Review or validation of a candidate goes to a
  context that did not write it.
- **Readiness is content.** A prerequisite counts only when its bytes are in
  the intended checkout. A closed item whose change is missing, stale or
  unavailable there is not ready: hold its dependents, keep its native status,
  and report the gap.
- **Reconcile before resuming.** Match tracker assignments against observed
  runtime state, validators included, before dispatching. Never duplicate an
  assignment because this conversation lacks it.
- **Decisions are not build work.** A decision item goes to the resolver it
  names ([Navigate](../navigate/SKILL.md#foggy-epics)), never to an
  implementer; with BD, pull build work with `bd ready --exclude-type decision`.

## Recover the actual work

Read acceptance, examples, scope, settled choices and open questions from their
owner and the existing native handoff, without repeating settled interviews or
requiring the full transcript; a missing or contradictory pointer needs source
investigation, not a guess. For each task, check who holds it, its workspace and
starting content, the write scope it occupies, pending checks and review, the
current candidate, who integrates it, and whether each prerequisite's content
is present. An empty ready list does not prove completion
([Navigate](../navigate/SKILL.md#rules-that-decide-the-pick)).

## Choose the next useful dispatch

Concurrency follows the observed bottleneck. Reserve capacity for integration,
review and repair, and reduce new starts while candidates accumulate. Record only
the concrete constraint and next action in the existing native handoff, then
reassess when evidence changes. Do not add a capacity ledger or queue.

[Agent Native](../agent-native/SKILL.md#before-launch-and-while-running) owns
runtime mechanics, disjoint write scopes and isolation; one-shot headless runs
go through [Codex Exec](../codex-exec/SKILL.md),
[Claude Exec](../claude-exec/SKILL.md) or [AGY Native](../agy-native/SKILL.md).
Serialize shared paths, generated companions included. A worktree separates Git
edits; it does not enforce restricted-source or model-egress limits
([model dispatch](../agent-native/references/model-dispatch.md)).

Dispatch a genuinely fresh implementer for one coherent accepted task, without
the coordinator's transcript or unrelated research; a new goal, role label,
cleared summary or resumed author context is not fresh. Pass the accepted
examples, applicable constraints, exact starting content, usable prerequisites,
authorized write/output scope, source pointers, required checks, integration
responsibility and real remaining bounds; brevity cannot omit a constraint. A
pointer counts only if the worker can open it: a link relative to a skill's own
folder, or a file outside the worker's workspace, does not resolve there, so
pass a path it can read or paste the rule itself. Record the worker's observed
identity at startup through Agent Native's association procedure.

[Implement](../implement/SKILL.md) owns the complete change, meaningful checks
and direct repair; it is optional guidance for that worker, not a compulsory
stage. The handoff returns candidate identity, changed scope, check facts,
discoveries and gaps; prompt delivery proves neither engagement
([Agent Native](../agent-native/SKILL.md#before-launch-and-while-running)) nor
acceptance.

When several workers apply one set of decisions, such as a batch of review
findings or one rewrite that must read the same in many files, make each
decision once in one context and send workers only what was decided. A worker
returns an uncovered case, or a blocker with evidence the decider could not see,
instead of improvising or reopening the decision; the decider settles it and
never drops it. [Decide once, apply in parallel](references/decide-once-apply-in-parallel.md)
covers both shapes.

## Integrate and obtain judgment

Name the integration responsibility before launch, and decide then whether the
integrated candidate needs a fresh judgment at all. Follow the consumer
repository's integration policy, include all changed paths and generated
companions, and run affected checks on the actual integrated subject.
Acceptance of a leaf does not establish the combined release. Within that
policy, combine parallel results one at a time in dependency order and run the
affected checks after each, so a failure points at one result; a merge without
conflicts does not show that two changes work together. A result that
conflicts, or whose own changed paths or prerequisites changed on the target
after it started, goes back to its author through a follow-up that authorizes
that update ([Agent Native](../agent-native/SKILL.md#launch-and-observe)), or
is redone from the current target, and reruns its checks; it is not merged
blind. A write outside a worker's declared scope, or collisions that keep
recurring, show the scope split cannot be trusted for this change: finish the
rest serially.

For an ordinary candidate the integrated checks and CI are the gate; assign one
fresh author-distinct judgment only in the costly cases
[Validate](../validate/SKILL.md#when-a-fresh-judgment-is-worth-it) names, and
Validate owns the single round, what counts as a finding, and when a repair
needs only its checks rerun. Preserve every explicitly required review leg;
advisory Review, Plan challenge and Council advice cannot stand in for a
judgment the caller requested
([advice or acceptance](../review/references/advice-or-acceptance.md#handing-off-to-acceptance)).

## Reconcile feedback and resume

Preserve successful and failed evidence in the existing native task or handoff,
and update affected unfinished work's native dependencies or handoff within
authority. Stop or explicitly re-scope an affected active assignment before it
continues on a disproven premise; the revision takes effect only on observable
acknowledgment or stopped runtime state. Unaffected work continues unchanged;
reconciling unchanged facts creates no new artifact or dispatch.

[Plan](../plan/SKILL.md) owns consequential uncertainty and refining the next
slice. New evidence may change an approach within the accepted outcome; a
different promised outcome or authority choice returns to the caller, never to
agent advice. Do not reopen accepted work to fit a revised story.

Known failures return to the responsible task for direct repair; a genuine
causal stall gets [RPI's one bounded helper](../rpi/SKILL.md#causal-stall-and-bounds),
and replacement workers, retries, new subjects and compaction never reset its
bounds. Use native waits for unchanged pending state instead of repeated
analysis or probes.

To recover a dead worker, confirm its process stopped, not only its pane;
capture its state and preserve its partial work recoverably; move its tracker
assignment to the replacement rather than filing a duplicate; and start the
fresh worker from that branch as exact starting content while dependents hold.

When maintained context could change the next action, use
[Memory find/recall](../memory/references/recall.md).

A caller-selected external factory keeps its coordinator in control: hand it
source intent through its supported door, never run its sessions by hand or
mirror its work in a second tracker, and judge the returned content
independently; its completion neither authorizes delivery nor establishes
acceptance. For Gas City, follow [Using GC](../using-gc/SKILL.md).

## Status block

When the caller asks for coordination status, return this shape; answer a quick
question in prose. No other report or persisted artifact is required unless an
existing consumer needs one.

```text
assignments: <worker/context id> -> <task>, state as observed (how); last activity <time, kind> | unobserved
candidates:  <task> -> <exact ref>; checks <result>; judgment <ref | owed | not owed>
next:        <free capacity> -> <dispatch>, because <observed bottleneck>
held:        <task>, blocked by <prerequisite gap>
handoffs:    <affected work updated, and where>
gaps:        <unobserved state, unknown identities, unresolved dissent>
```
