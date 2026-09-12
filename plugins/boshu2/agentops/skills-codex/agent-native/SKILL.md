---
name: agent-native
description: 'Dispatch independent tasks to parallel workers or selected persistent roles. Use when: delegation is authorized with disjoint scopes; execution does not validate output.'
---
# Agent Native

Operate caller-selected agent sessions as explicit roles without turning the
runtime into AgentOps lifecycle authority.

For judgment, default to a fresh context in the author's model family.
Cross-model Validate, mixed Council and dueling model perspectives are explicit
caller selections. Follow
[references/model-dispatch.md](references/model-dispatch.md): the working
session is the controller; check the explicitly selected adapter at runtime;
no factory is required and Agent Mail is never the judgment path. The recipe
owns host authorization, finite input/output, timeout and cleanup requirements.

Role requests declare authority; actual native runtime/OS filesystem and egress
controls must enforce it. A prompt, worktree, chmod or unrestricted same-user
process does not establish isolation. Observe synthetic canary denials before
restricted-source work; unavailable protection remains unavailable.

Use native waits or status notifications while workers or checks are pending.
Unchanged state is no reason for another analysis, review or provisional
retrospective. Observation consumes time and context; it is not free. A known
blocking failure deserves action even while other jobs run. For a suspected
stall, inspect observable state before choosing a nudge or replacement within
authority and remaining bounds. Stop observing at terminal status or the end
of the caller's observation window; impatience alone does not justify restart.

Named failure mode — **prompt-send optimism**: treating a successfully
delivered prompt as a working worker; delivery proves transport, not
engagement.

For new authorized work after a worker completes, use the selected runtime's
documented follow-up or resume operation that starts a turn. A message operation
may only queue text for a running worker. Check native state and engagement;
do not treat a queued repair request as a resumed implementation attempt.

Anti-pattern: restarting an unresponsive worker as the first move. Corrective:
capture its observable state first — a restart destroys the evidence of why it
stalled, and rescue is usually cheaper than rerun.

## Roles

- **Orchestrator:** passes focused intent, scope and evidence references, names
  the integration/final-review owner, and reports runtime facts. Retrieve extra
  history only for a consequential uncertainty; a fresh context is not
  necessarily small. A new goal does not clear history or renew spent bounds.
- **Implementer:** may modify only its packet's declared subject.
- **Validator:** receives exact candidate content in a fresh, read-only context.
- **Scribe:** records runtime evidence without judging acceptance.

Reader and Writer are bounded cheap delegations, not roles with authority: a
Reader returns line-referenced bullets over files the caller never loads, and a
Writer lands one patterned file from a spec plus a reference file and returns a
receipt the caller never reads back. Both are caller-selected per call, default
to a cheap model, and yield runtime facts only — a receipt is not validation.
See [context-budget delegation](references/context-budget-delegation.md).

## Contract

For a caller-selected parallel batch, validate every complete packet before the
first launch. Require the selected executor, packet identity and all transitive
effects, with canonical workspace-relative write scopes in separate isolation.
Resolve symlinks and normalize paths; compare scopes case-insensitively so an
alias cannot hide a collision. A lexical disjointness check alone cannot prove
symlink or runtime isolation. The reference batch contract rejects nonempty
`write_scope.exclude` because its proof cannot honor those exclusions.

Dispatch each validated packet once and preserve its identity with the result:
candidate, evidence or executor error. Do not partly launch a batch that later
fails validation, or retry an error as if it had never happened. Native caller
authority determines any repair or follow-up. The developer reference
`scripts/swarm/dispatch_once.py` requires an AgentOps source checkout; it is
exercised by repository tests and is not bundled with standalone skills.
Installed use dispatches through the selected native runtime. This optional
batch mode selects no backlog work, creates no queue and integrates no changes.

1. Require caller intent, role, workspace, authorized source/output scope and
   evidence destination before starting a worker. Pass source-store/project/work
   identity and permitted intent locators before execution can fail. Record this
   dispatch association in caller-owned native comments/metadata or runtime
   facts, with actual worker session/context IDs explicitly unknown until
   observed; a requested ID is not an observed ID. This adds no AO packet schema.
2. Capture observed native runtime/session/context identity at startup, before
   substantive work and independently of final handoff. Return the observation
   through the caller-owned native recording channel with its provenance and
   permitted source locator. Preserve launch failures and unknowns if startup
   never becomes observable. Follow
   [session associations](../cass/references/SESSION_FORMATS.md#work-to-session-associations)
   for separate parent/resume links, supported multi-work spans and frozen source
   bounds. A controller is not necessarily a native parent; every requested
   child and resumed execution needs its own observed association. If recording
   fails, report the gap; do not claim crash recovery from prompt delivery alone.
   Prove runtime readiness and engagement from observable state; a successful
   prompt send is not proof of work.
3. Keep concurrent writers disjoint and isolated. Runtime coordination is not a
   claim, lease, queue, or completion state in AgentOps.
4. Record provider state, transcript references, artifacts, and terminal status.
5. Return runtime evidence to the caller. Do not convert provider retries,
   reconnects, idle states, or failures into Plan, Candidate, or verdict state.
6. A validator session may supply judgment to Validate, but only Validate writes
   `verdict.v2`. The adapter cannot select AgentOps semantics, issue a binding verdict, or turn factory completion into delivery or validation proof.

NTM, Codex exec, native processes, Agent Mail, and Gas City are replaceable
adapters. Use them only when the caller selected that execution shape. A
single local agent pays no factory coordination cost. Model identity, when
recorded, is a declared runtime fact like context identity — see
[references/model-dispatch.md](references/model-dispatch.md).

[Native judgment receipts](references/judgment-receipts.md) defines exact private
receipt references and the independent profile/subject/acceptance checks for
caller-required model diversity. Missing native identity never satisfies a leg.
