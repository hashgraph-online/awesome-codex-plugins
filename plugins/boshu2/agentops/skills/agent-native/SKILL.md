---
name: agent-native
description: 'Dispatch independent tasks to parallel workers or subagents without write collisions. Use when: running or planning agents in parallel, even two; check scopes before any launch.'
practices: [team-topologies, design-by-contract]
hexagonal_role: supporting
consumes: [explicit-role-packets]
produces: [runtime-evidence, worker-handoff, per-packet-results]
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
  tier: meta
  dependencies: []
  capabilities: [role_dispatch, observe_workers, handoff, dispatch_once]
  effects: [manage_runtime_sessions, invoke_selected_executor]
  canonical_status: canonical
  disposition: keep_optional_adapter
output_contract: runtime evidence and per-packet candidate, evidence, or error for explicit authorized work
---

# Agent Native

Launch and observe caller-selected agent sessions as explicit roles, and return
runtime facts per packet. Execution does not validate output: no adapter issues
a binding verdict or turns factory completion into delivery or validation proof.
[Orchestrate](../orchestrate/SKILL.md) decides what to dispatch and when; this
skill launches and observes.

## Before launch, and while running

- **Validate the whole batch first.** Every packet needs its selected executor,
  packet identity, all transitive effects, the actions it must not take (such
  as push, merge, history rewrite, tracker or external writes) and a canonical
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
- **Delivery is not engagement.** A delivered prompt or an acknowledgement
  proves transport only; reading it as a working worker is prompt-send
  optimism. Prove engagement from observable state: session output, tool
  activity, changed files.
- **Capture before restart.** Before a nudge, replacement or restart, capture
  the worker's observable state. A restart destroys the evidence of why it
  stalled, and rescue is usually cheaper than rerun. Silence or impatience alone
  does not justify a restart; any replacement stays within authority and
  remaining bounds.
- **Dispatch once.** Keep each packet's identity with its result. An executor
  error is a result, not a retry trigger; repair and follow-up are the caller's
  authority. A launch call the runtime refuses, so that its worker never
  starts, is not a launch: correct a malformed call once, and treat a
  concurrency or capacity limit as backpressure, waiting natively for a slot
  and launching the validated batch in waves under it; what each freed slot
  runs first stays the caller's decision
  ([Orchestrate](../orchestrate/SKILL.md#before-any-dispatch)). Running a
  packet inline or elsewhere is the caller's disclosed choice
  ([refused launches](references/launch-and-isolation.md#refused-launches)).
- **Account for every input.** When a packet carries many items (files,
  records, issues), give each a stable ID before launch and join the returned
  results back to that list. An item with no result is missing, not done; an
  output with no matching input is unexplained. Report both by ID. Name each
  return field and its allowed values in the packet when results will be
  counted, sorted, deduplicated or compared; parsed prose is where counts drift.
- **Prove integration before removal.** Before a caller-authorized removal of
  a finished worker's workspace, branch or stash, compare its content with the
  integration target as it stands now, by patch or file diff, not by merged
  status or by matching the commit that was merged: squash and rebase hide
  ancestry. Preserve uncommitted, unique or unintegrated content in
  a recoverable form, such as an archive ref or bundle, first. Report what was
  kept, what was removed and the evidence for each.

## Roles

- **Orchestrator:** passes focused intent, scope and evidence references, names
  the integration/final-review owner, and reports runtime facts. Retrieve extra
  history only for a consequential uncertainty; a fresh context is not
  necessarily small.
- **Implementer:** may modify only its packet's declared subject.
- **Validator:** receives exact candidate content in a fresh, read-only context
  and supplies judgment to [Validate](../validate/SKILL.md), which alone writes
  `verdict.v2`.

Reader and Writer are bounded cheap delegations, not roles with authority. A
Reader returns line-referenced bullets over files the caller never loads, in
slices of at most 350 lines. A Writer lands one patterned file from a spec plus
a required reference file and returns a receipt the caller never reads back.
Both are caller-selected per call and yield runtime facts only; a receipt is not
validation. For Codex, use the source-owned `bulk-reader` and `code-writer`
native roles; their model and effort are pinned in
[agents/bulk-reader.toml](agents/bulk-reader.toml) and
[agents/code-writer.toml](agents/code-writer.toml), and each runs in the parent
session's sandbox, which a role file cannot override.
[Context-budget delegation](references/context-budget-delegation.md) covers
installation, native invocation, opt-in refusal hooks and the limits of role
instructions.

## Launch and observe

1. Before starting a worker, require caller intent, role, workspace, starting
   commit, authorized source/output scope and evidence destination. Record the
   dispatch association in the caller's native work comments or metadata, or in
   existing runtime facts, before execution can fail. A requested ID is not an
   observed ID; worker identity stays unknown until the runtime reports it.
2. At startup, before substantive work, capture the observed runtime, session
   and context identity and return it to that same record. Before its first
   edit, the worker confirms its HEAD is that starting commit; a mismatch is a
   launch failure, never repaired by reset. Report launch failures, recording
   gaps and unknowns; never fill them in. An authentication-shaped error from a
   sandboxed launch does not prove a logged-out account
   ([launch and isolation](references/launch-and-isolation.md#authentication-shaped-errors)).
   [Session associations](references/session-associations.md#work-to-session-associations)
   owns parent and resume links, multi-work spans and frozen source bounds.
3. Keep concurrent writers disjoint and isolated, using the selected runtime's
   own isolation where it has one and never nesting a worktree inside the
   session's own ([workspace isolation](references/launch-and-isolation.md#workspace-isolation)).
   Runtime coordination is not a claim, lease, queue or completion state in
   AgentOps.
4. Observe through native waits or status notifications; observation costs time
   and context. Unchanged state is no reason for another analysis, review or
   retrospective, while a known blocking failure deserves action even as other
   jobs run. Stop at terminal status or the end of the caller's window.
5. A headless worker cannot ask: on a choice its packet leaves open it takes no
   irreversible or out-of-scope step on a guess and returns the choice under
   `gaps` ([open choices](references/launch-and-isolation.md#open-choices)).
   For new authorized work after a worker completes, including an answer that
   settled intent supplies, use the runtime's documented follow-up or resume
   operation that starts a turn. A message operation only queues text for a
   running worker; a queued repair request is not a resumed attempt.
6. Record provider state, transcript references, artifacts and terminal status.
   Provider retries, reconnects, idle states and failures stay runtime facts,
   never Plan, Candidate or verdict state. A result whose observed tool
   activity shows an excluded action is out of authority, not a candidate,
   whatever its checks show.

## Adapters and judgment

NTM, native processes, Agent Mail, Gas City and the one-shot headless runners
([codex-exec](../codex-exec/SKILL.md), [claude-exec](../claude-exec/SKILL.md),
[agy-native](../agy-native/SKILL.md)) are replaceable adapters. Use one only
when the caller selected that execution shape; a single local agent pays no
factory coordination cost.

Judgment defaults to a fresh context in the author's model family; cross-model
legs are explicit caller selections. [Model dispatch](references/model-dispatch.md)
owns each leg's authorization, isolation, bounds and cleanup, and Agent Mail is
never the judgment path. Role requests declare authority, but only native
runtime/OS filesystem and egress controls enforce it.
[Native judgment receipts](references/judgment-receipts.md) check
caller-required model diversity; missing native identity never satisfies a leg.
For exact native source spans, follow
[bounded raw source reads](references/RAW_SOURCE_READS.md).

## Per-packet result

```text
packet_id:        the caller's packet id
executor:         selected runtime; requested model; observed model if reported
observed_session: session/context id the runtime reported, else unknown
engagement:       observable evidence the worker started, else unobserved
last_activity:    time and kind of the last observed tool call, output or file change, else unobserved
terminal_status:  exit or terminal state | running | launch failed | not launched
result:           candidate <ref> | evidence <ref> | out of authority <action> | error <verbatim>
gaps:             recording failures and unknowns
```
