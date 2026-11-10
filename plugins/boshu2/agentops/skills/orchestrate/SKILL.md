---
name: orchestrate
description: 'Dispatch independent tasks to parallel workers without write collisions, decide what each does next, and recover dead ones. Use when: running or managing two or more agents.'
practices: [team-topologies, evidence-based-engineering, design-by-contract]
hexagonal_role: supporting
consumes: [accepted-intent, native-work-state, candidate-evidence, explicit-role-packets]
produces: [native-handoffs, reconciled-feedback, runtime-evidence, per-packet-results]
context_rel:
- kind: customer-of
  with: codex-exec
- kind: customer-of
  with: claude-exec
- kind: customer-of
  with: agy-native
skill_api_version: 1
user-invocable: true
metadata:
  graph_root: true
  tier: execution
  dependencies: []
  capabilities: [coordinate_native_work, recover_assignments, reconcile_feedback, role_dispatch, observe_workers, dispatch_once]
  effects: [dispatch_authorized_workers, update_native_handoffs, manage_runtime_sessions, invoke_selected_executor]
  canonical_status: canonical
  disposition: keep
output_contract: observed native assignments, per-packet runtime results, exact candidate and judgment references, affected-work handoffs and explicit remaining gaps
---

# Orchestrate

This skill decides what each worker does next and launches it safely. The core
move: send free capacity to finished work that still owes checks, integration
or a judgment before starting anything new, and launch nothing until every
packet in the batch is valid with canonical write scopes that do not collide.
It worked when no finished-but-unchecked candidate waits while new work starts,
no task runs on a closed but unintegrated prerequisite, no two launched workers
share a canonical path or a contended resource, and each packet has a result
naming observed engagement, terminal status and `not_as_briefed`.

One agent and one writer is the default. Give work to parallel workers only
where the pieces are independent: disjoint canonical write scopes and no
contended runtime resource. Dependent or overlapping work stays with one writer
or runs in sequence. Within that, concurrency follows the observed bottleneck:
reserve capacity for integration, review and repair, and reduce new starts
while candidates accumulate.

- Use this skill for the next dispatch, packet checks, launch, observation,
  recovery and integration order.
- Use [Navigate](../navigate/SKILL.md) to pick the next wave on a bead graph
  toward frozen acceptance.
- Use [Validate](../validate/SKILL.md) to judge a result; exit 0, a receipt and
  factory completion never validate output.
- Use [codex-exec](../codex-exec/SKILL.md), [claude-exec](../claude-exec/SKILL.md)
  or [agy-native](../agy-native/SKILL.md) for one headless run the caller
  selected.

## Before any dispatch

- **Finished is not done.** Exit 0, a pushed branch, a closed tracker item or a
  worker saying "done" makes a candidate. It still owes its checks, integration
  and, when one is owed, a fresh judgment.
- **A held step keeps the task open.** When a worker lists a step under
  `not_as_briefed` (refused, held, worked around or unverified), the task is
  not complete. A result marked `out of authority` is not a candidate. Retry
  the step yourself only within your authority and the caller's limits, never
  by the route the worker was denied. Otherwise integrate the finished part
  only if it stands alone, and report the open step as a blocker.
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
  assignment because this conversation lacks it. For each task check who holds
  it, its starting content, its write scope, pending checks, the current
  candidate and who integrates it; an empty ready list does not prove
  completion ([Navigate](../navigate/SKILL.md#rules-that-decide-the-pick)).
- **Decisions are not build work.** A decision item goes to the resolver it
  names ([Navigate](../navigate/SKILL.md#foggy-epics)), never to an
  implementer; with BD, pull build work with `bd ready --exclude-type decision`.

Record only the concrete constraint and next action in the existing native
handoff.

## Check the packets

Dispatch a fresh implementer for one coherent accepted task through the
runtime's task-only dispatch; a forked session, cleared summary or resumed
author context still carries the history
([RPI](../rpi/SKILL.md#delegation-and-handoffs)).

- **Validate the whole batch first.** This list is the one packet contract.
  Every packet needs its packet identity, caller intent with its accepted
  examples, applicable constraints, role, selected executor, workspace,
  starting commit, usable prerequisites, authorized source scope, evidence
  destination, all transitive effects, the actions it must not take (such as
  push, merge, history rewrite, tracker or external writes), the checks it must
  run, who integrates its result, the real remaining bounds, the
  [per-packet result](#per-packet-result) fields, and a canonical
  workspace-relative write scope, generated companions and regeneration outputs
  included, in separate isolation. If any packet is invalid, launch none:
  starting the valid ones and fixing the rest later is a partial launch.
- **Compare canonical scopes.** Resolve symlinks, normalize paths and compare
  case-insensitively so an alias cannot hide a collision. A lexical check alone
  cannot prove symlink or runtime isolation. Disjoint files are not
  independence: workers, readers included, contend on a resource one of them
  writes, installs into or holds exclusively, such as a bound port, a database
  it writes, a package install it mutates or a locked browser profile; give
  each its own instance or serialize only those. A shared model-provider limit
  is backpressure, launched in waves, not serialized
  ([shared runtime](references/launch-and-isolation.md#shared-runtime)).
- **State what a blocked step means.** When the runtime refuses an action or a
  step cannot run in the worker's environment, the worker holds that step and
  whatever depends on it, does not reach the same effect by another route,
  leaves finished edits in place, completes the independent parts and lists
  the step under `not_as_briefed`; an authorized safer alternative stays
  allowed ([change safety](../implement/references/change-safety.md#a-safety-control-refuses-the-operation)).
- **Pass pointers the worker can open.** A link relative to a skill's folder,
  or a file outside the worker's workspace, does not resolve there; pass a
  readable path or paste the rule.
- **Account for every input.** When a packet carries many items, open
  [launch and isolation](references/launch-and-isolation.md#many-items-in-one-packet)
  before launch.

When several workers will apply one set of decisions, such as a batch of
review findings or one rewrite that must read the same in many files, open
[decide once, apply in parallel](references/decide-once-apply-in-parallel.md)
before splitting the work. When the caller wants file bytes kept out of its own
context, open [context-budget delegation](references/context-budget-delegation.md)
before dispatching a `bulk-reader` or `code-writer`. When a packet is a
judgment leg, open [model dispatch](../validate/references/model-dispatch.md)
before launch.

## Launch and observe

1. Record the dispatch association in the caller's native work comments or
   metadata before execution can fail. At startup, capture the observed
   runtime, session and context identity into that record; a requested ID is
   not an observed one. The worker confirms its HEAD is the starting commit
   before its first edit; a mismatch is a launch failure, never repaired by
   reset. When a launch is refused, fails, or reports an authentication-shaped
   error, or before creating a worktree, open
   [launch and isolation](references/launch-and-isolation.md). When a
   tracker item must be tied to the session that worked it, open
   [session associations](references/session-associations.md).
2. **Delivery is not engagement.** A delivered prompt or an acknowledgement
   such as "Got it, starting" proves transport only. Prove engagement from
   observable state: session output, tool activity, changed files.
3. Observe through native waits or status notifications. Unchanged state is no
   reason for another analysis, review or retrospective; a known blocking
   failure deserves action even as other jobs run.
4. **Capture before restart.** Before a nudge, replacement or restart, capture
   the worker's observable state. A restart destroys the evidence of why it
   stalled. Silence alone does not justify a restart.
5. **Dispatch once.** An executor error is a result, not a retry trigger. A
   headless worker cannot ask: on a choice its packet leaves open it takes no
   irreversible or out-of-scope step and returns the choice under `gaps`. New
   authorized work after a worker completes uses the runtime's follow-up or
   resume operation that starts a turn; a queued message is not a resumed
   attempt.
6. A result whose observed tool activity shows an excluded action is
   `out of authority`, not a candidate, whatever its checks show.

When a worker died, evidence disproves a running assignment's premise, a
finished workspace is to be removed, or a caller-selected factory runs the
work, open [recover and resume](references/recover-and-resume.md).

## Integrate and obtain judgment

Name the integration responsibility before launch, and decide then whether the
integrated candidate needs a fresh judgment at all. Follow the consumer
repository's integration policy and run affected checks on the actual
integrated subject. Combine parallel results one at a time in dependency order
and run the affected checks after each, so a failure points at one result; a
merge without conflicts does not show that two changes work together. A result
that conflicts, or whose changed paths or prerequisites changed on the target
after it started, goes back to its author through a follow-up or is redone
from the current target; it is not merged blind. A write outside a worker's
declared scope, or recurring collisions, means the scope split cannot be
trusted for this change: finish the rest serially.

For an ordinary candidate the integrated checks and CI are the gate; assign one
fresh author-distinct judgment only in the costly cases
[Validate](../validate/SKILL.md#when-a-fresh-judgment-is-worth-it) names.
Preserve every explicitly required review leg; advisory Review, Plan challenge
and Council advice cannot stand in for a judgment the caller requested
([advice or acceptance](../review/references/advice-or-acceptance.md#handing-off-to-acceptance)).
Known failures return to the responsible task for direct repair; a genuine
causal stall gets [RPI's one bounded helper](../rpi/SKILL.md#causal-stall-and-bounds).

## Per-packet result

```text
packet_id:        the caller's packet id
executor:         selected runtime; requested model; observed model if reported
observed_session: session/context id the runtime reported, else unknown
engagement:       observable evidence the worker started, else unobserved
last_activity:    time and kind of the last observed tool call, output or file change, else unobserved
terminal_status:  exit or terminal state | running | launch failed | not launched
result:           candidate <ref> | evidence <ref> | out of authority <action> | error <verbatim>
not_as_briefed:   worker-reported steps refused, held, worked around or unverified | none reported
gaps:             recording failures, open choices and unknowns
```

Ask for `not_as_briefed` in the packet: a summary of what the worker did leaves
out what it did not do. Where the adapter returns its own denial record
(`permission_denials`, `denied_actions`), read that too and list a mismatch
under `gaps`.

When the caller asks for coordination status, return the
[status block](references/status-block.md); answer a quick question in prose.
