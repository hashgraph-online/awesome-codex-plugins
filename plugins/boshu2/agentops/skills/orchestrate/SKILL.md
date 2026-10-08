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

Coordinate caller-authorized work through its existing tracker and runtime.
Use the accepted task or conversation; a clear task needs zero mandatory skills.
Selecting Orchestrate adds in-session guidance, not an AgentOps scheduler, work
index, queue, ownership system, aggregate retry controller or delivery authority.
The caller's tracker owns assignments and dependencies; its runtime owns running
contexts, bounds and supervision; repository policy owns integration and delivery.
Orchestrate decides what each worker does next.
[Agent Native](../agent-native/SKILL.md) launches and observes workers;
[Navigate](../navigate/SKILL.md) picks the wave on a bead graph toward frozen
acceptance and records verdicts.

## Before any dispatch

- **Finished is not done.** Exit 0, a pushed branch, a closed tracker item or a
  worker saying "done" makes a candidate. It still owes its checks, integration
  and, when one is owed, a fresh judgment.
- **Drain before starting.** While candidates wait on checks, repair,
  integration or an owed judgment, free capacity goes there first. A free slot
  alone is not a dispatch reason; start new implementation with what is left.
- **Judges did not author.** Review or validation of a candidate goes to a
  context that did not write it.
- **Readiness is content.** A prerequisite counts only when its bytes are in
  the intended checkout. A closed item whose change is missing, stale or
  unavailable there is not ready: hold its dependents, keep its native status,
  and report the gap.
- **Reconcile before resuming.** Match tracker assignments against observed
  runtime state, validators included, before dispatching. Never duplicate an
  assignment because this conversation lacks it.

## Recover the actual work

Read the accepted outcome, examples and scope from their current owner. Recover
settled caller choices and rationale, completed history, consequential open
questions and the next investigation from the existing native handoff. Do not
repeat settled interviews or require the full transcript. Missing or contradictory
pointers require source investigation, not a guessed decision.

Inspect, together: task acceptance, observed worker/context identity, workspace
and starting content, occupied write scope, pending checks and review, current
candidate identity, integration owner, and the actual content and evidence of
each prerequisite. An empty ready list does not prove completion.

## Choose the next useful dispatch

Concurrency follows the observed bottleneck. Reserve capacity for integration,
review and repair, and reduce new starts while candidates accumulate. Record only
the concrete constraint and next action in the existing native handoff, then
reassess when evidence changes. Do not add a capacity ledger or queue.

Agent Native owns runtime mechanics: executor selection, startup and engagement
evidence, actual context identity, normalized scopes, native waits and
follow-up, bounds and cleanup. One-shot headless runs go through
[Codex Exec](../codex-exec/SKILL.md), [Claude Exec](../claude-exec/SKILL.md) or
[AGY Native](../agy-native/SKILL.md). Concurrent writers require disjoint write
scopes and separate isolation, including generated companions and transitive
effects. Serialize shared paths. A worktree separates Git edits; it does not
establish restricted-source or model-egress enforcement.

Dispatch a genuinely fresh implementer for one coherent accepted task, without
the coordinator's accumulated transcript or unrelated research. A new goal,
role label, cleared summary or resumed author context is not a fresh context.
Pass the accepted examples, applicable constraints, exact starting content,
usable prerequisites, authorized write/output scope, relevant source pointers,
required checks, integration responsibility and real remaining bounds. Expand
pointers when needed; brevity cannot omit a constraint. Record observed native
identity at startup through Agent Native's existing association procedure.

[Implement](../implement/SKILL.md) owns the complete change, meaningful checks
and direct repair. It is optional guidance for that worker, not a compulsory
stage. The handoff returns candidate identity, changed scope, check facts,
discoveries and gaps; prompt delivery proves neither engagement nor acceptance.

## Integrate and obtain judgment

Name the integration responsibility before launch, and decide then whether the
integrated candidate needs a fresh judgment at all. Follow the consumer
repository's integration policy, include all changed paths and generated
companions, and run affected checks on the actual integrated subject.
Acceptance of a leaf does not establish the combined release.

For an ordinary candidate the integrated checks and CI are the gate. Assign one
fresh author-distinct judgment through [Validate](../validate/SKILL.md), the
sole skill owner of acceptance semantics, only when the caller asks, when a
mistake cannot be cheaply undone after it lands (a published release or
instructions users will follow, a security boundary, destroying data or tracker
state, deleting a check that protects the product), or when no deterministic
check covers the changed behavior. Preserve every explicitly required review
leg. Advisory Review, Plan challenge and Council advice are not binding
acceptance and cannot stand in for a judgment the caller requested.

One round. The validator does not re-run the integrated checks. Route back as
repairs only what fails the accepted behavior or would mislead a user, break
install or the CLI, or remove protection for the product; confirm each repair
with a check. Changed candidate bytes need their affected checks rerun; they
need a new judgment only when the caller asks for one. Keep review cost a
fraction of the cost of the work. No report format or persisted artifact is
mandatory unless the caller or an existing consumer requires one.

## Reconcile feedback and resume

Preserve successful and failed evidence in the existing native task or handoff.
Identify affected unfinished work and update its native dependencies or handoff
within authority. Stop or explicitly re-scope an affected active assignment
before it continues on a disproven premise; obtain observable acknowledgment or
stopped runtime state before treating the revision as effective. Unaffected work
continues unchanged. Repeating reconciliation with unchanged facts creates no
new artifact or dispatch.

[Plan](../plan/SKILL.md) owns consequential uncertainty, optional challenge and
refining the next complete slice. Reuse settled decisions and accepted examples;
new evidence may change an approach within the accepted outcome. A different
promised outcome or authority choice returns to the caller. Agent advice cannot
supply that choice. Preserve completed history instead of reopening accepted
work merely to fit a revised story.

Known failures return to the responsible task for direct repair. On a genuine
causal stall, the existing operating contract permits at most one authorized
bounded fresh helper for that incident within remaining bounds; an unhelpful
answer ends that attempt. Cancellation, refusal or exhausted bounds skip help.
Replacement workers, retries, new subjects and compaction never reset those
bounds. Inspect native evidence before replacing a worker; use native waits for
unchanged pending state instead of repeated analysis or probes.

When maintained context could change the next action, use
[Memory find/recall](../memory/references/recall.md); coordination triggers no
automatic capture, import or recall.

A caller-selected external factory keeps its coordinator in control: hand it
source intent through its supported door, never create, scale or repair its
internal sessions by hand, and do not mirror its work in an AgentOps tracker.
Judge the returned exact content independently; factory completion neither
authorizes delivery nor establishes acceptance. For Gas City, follow
[Using GC](../using-gc/SKILL.md).

## Status block

When reporting coordination state, return:

```text
assignments: <worker/context id> -> <task>, state as observed (how)
candidates:  <task> -> <exact ref>; checks <result>; judgment <ref | owed | not owed>
next:        <free capacity> -> <dispatch>, because <observed bottleneck>
held:        <task>, blocked by <prerequisite gap>
handoffs:    <affected work updated, and where>
gaps:        <unobserved state, unknown identities, unresolved dissent>
```
