---
name: agent-native
description: 'Operate explicit orchestrator, implementer, validator, and scribe roles through a caller-selected agent runtime. Triggers: "agent-native factory", "role-shaped agent panes", "persistent workers".'
---
# Agent Native

Operate caller-selected agent sessions as explicit roles without turning the
runtime into AgentOps lifecycle authority.

For multi-model judgment (mixed council, dueling perspectives, cross-model
validate, which is default on risky surfaces per ADR-0017 and caller-elected
otherwise), follow
[references/model-dispatch.md](references/model-dispatch.md): the working
session is the controller; check the explicitly selected adapter at runtime;
no factory is required and Agent Mail is never the judgment path. The recipe
owns host authorization, finite input/output, timeout and cleanup requirements.

Role requests declare authority; actual native runtime/OS filesystem and egress
controls must enforce it. A prompt, worktree, chmod or unrestricted same-user
process does not establish isolation. Observe synthetic canary denials before
restricted-source work; unavailable protection remains unavailable.

When a worker looks stuck, score interventions by evidence and reversibility
before acting: observe more (free, fully reversible), then nudge, then replace
the worker, then restart the runtime — escalate only when observable state,
not impatience, rules out the cheaper step. Stop the observe-nudge cycle once
the worker reaches a terminal status or the caller's observation window ends;
past that point further intervention manufactures noise, not evidence.

Named failure mode — **prompt-send optimism**: treating a successfully
delivered prompt as a working worker; delivery proves transport, not
engagement.

Anti-pattern: restarting an unresponsive worker as the first move. Corrective:
capture its observable state first — a restart destroys the evidence of why it
stalled, and rescue is usually cheaper than rerun.

## Roles

- **Orchestrator:** passes explicit packets and reports runtime facts.
- **Implementer:** may modify only its packet's declared subject.
- **Validator:** receives exact candidate content in a fresh, read-only context.
- **Scribe:** records runtime evidence without judging acceptance.

## Contract

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
