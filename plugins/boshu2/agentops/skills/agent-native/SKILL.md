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
runtime facts per packet. Execution does not validate output, and the runtime
never becomes AgentOps lifecycle authority: an adapter cannot select AgentOps
semantics, issue a binding verdict, or turn factory completion into delivery or
validation proof. [Orchestrate](../orchestrate/SKILL.md) decides what to
dispatch and when; this skill launches and observes.

## Before launch, and while running

- **Validate the whole batch first.** Every packet needs its selected executor,
  packet identity, all transitive effects and a canonical workspace-relative
  write scope in separate isolation. If any packet is invalid, launch none:
  starting the valid ones and fixing the rest later is a partial launch.
- **Compare canonical scopes.** Resolve symlinks, normalize paths and compare
  case-insensitively so an alias cannot hide a collision. A lexical check alone
  cannot prove symlink or runtime isolation.
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
  authority.

## Roles

- **Orchestrator:** passes focused intent, scope and evidence references, names
  the integration/final-review owner, and reports runtime facts. Retrieve extra
  history only for a consequential uncertainty; a fresh context is not
  necessarily small. A new goal does not clear history or renew spent bounds.
- **Implementer:** may modify only its packet's declared subject.
- **Validator:** receives exact candidate content in a fresh, read-only context.
  It may supply judgment to Validate; only Validate writes `verdict.v2`.
- **Scribe:** records runtime evidence without judging acceptance.

Reader and Writer are bounded cheap delegations, not roles with authority. A
Reader returns line-referenced bullets over files the caller never loads, in
slices of at most 350 lines. A Writer lands one patterned file from a spec plus
a required reference file and returns a receipt the caller never reads back.
Both are caller-selected per call and yield runtime facts only; a receipt is not
validation. For Codex, use the source-owned `bulk-reader` and `code-writer`
native roles; their model and sandbox are pinned in
[agents/bulk-reader.toml](agents/bulk-reader.toml) and
[agents/code-writer.toml](agents/code-writer.toml).
[Context-budget delegation](references/context-budget-delegation.md) covers
installation, native invocation, opt-in refusal hooks and the limits of role
instructions.

## Launch and observe

1. Before starting a worker, require caller intent, role, workspace, authorized
   source/output scope and evidence destination. Record the dispatch
   association in the caller-owned native channel before execution can fail. A
   requested ID is not an observed ID; worker identity stays unknown until the
   runtime reports it.
2. At startup, before substantive work, capture the observed runtime, session
   and context identity and return it through that channel. Report launch
   failures, recording gaps and unknowns; never fill them in.
   [Session associations](references/session-associations.md#work-to-session-associations)
   owns parent and resume links, multi-work spans and frozen source bounds.
3. Keep concurrent writers disjoint and isolated. Runtime coordination is not a
   claim, lease, queue or completion state in AgentOps.
4. Observe through native waits or status notifications; observation costs time
   and context. Unchanged state is no reason for another analysis, review or
   retrospective, while a known blocking failure deserves action even as other
   jobs run. Stop at terminal status or the end of the caller's window.
5. For new authorized work after a worker completes, use the runtime's
   documented follow-up or resume operation that starts a turn. A message
   operation only queues text for a running worker; a queued repair request is
   not a resumed attempt.
6. Record provider state, transcript references, artifacts and terminal status.
   Provider retries, reconnects, idle states and failures stay runtime facts,
   never Plan, Candidate or verdict state.

The batch contract's reference implementation, `scripts/swarm/dispatch_once.py`,
needs an AgentOps source checkout and is not bundled with installed skills;
installed use dispatches through the selected native runtime. It rejects a
nonempty `write_scope.exclude` because its proof cannot honor exclusions. Batch
mode selects no backlog work, creates no queue and integrates no changes.

## Adapters and judgment

NTM, native processes, Agent Mail, Gas City and the one-shot headless runners
([codex-exec](../codex-exec/SKILL.md), [claude-exec](../claude-exec/SKILL.md),
[agy-native](../agy-native/SKILL.md)) are replaceable adapters. Use one only
when the caller selected that execution shape; a single local agent pays no
factory coordination cost.

For judgment, default to a fresh context in the author's model family.
Cross-model Validate, mixed Council and dueling model perspectives are explicit
caller selections. [Model dispatch](references/model-dispatch.md) owns host
authorization, isolation, finite input/output, timeout and cleanup for each leg;
the working session is the controller, no factory is required, and Agent Mail
is never the judgment path. Role requests declare authority, but only native
runtime/OS filesystem and egress controls enforce it.
[Native judgment receipts](references/judgment-receipts.md) define receipt
references and the checks for caller-required model diversity; missing native
identity never satisfies a leg. For exact native source spans, follow
[bounded raw source reads](references/RAW_SOURCE_READS.md) and its access and
output limits.

## Per-packet result

```text
packet_id:        the caller's packet id
executor:         selected runtime; requested model; observed model if reported
observed_session: session/context id the runtime reported, else unknown
engagement:       observable evidence the worker started, else unobserved
terminal_status:  exit or terminal state | running | launch failed
result:           candidate <ref> | evidence <ref> | error <verbatim>
gaps:             recording failures and unknowns
```
