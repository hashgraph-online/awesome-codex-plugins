---
name: agent-native
description: Operate explicit orchestrator, implementer
---
# Agent Native

Operate caller-selected agent sessions as explicit roles without turning the
runtime into AgentOps lifecycle authority.

For caller-elected multi-model judgment (mixed council, dueling perspectives,
cross-model validate), follow
[references/model-dispatch.md](references/model-dispatch.md): the working
session is the controller; probe `codex-exec` and `ntm` at runtime; never
require either; never use Agent Mail for judgment; never invoke `claude -p`.

Role separation works because each role's authority is checkable from its
packet: a worker that cannot exceed its declared subject cannot corrupt a
sibling's evidence, so factory failures stay local instead of systemic.

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

1. Require an explicit packet, role, workspace, context identity, and evidence
   destination before starting a worker.
2. Prove runtime readiness and engagement from observable state; a successful
   prompt send is not proof of work.
3. Keep concurrent writers disjoint and isolated. Runtime coordination is not a
   claim, lease, queue, or completion state in AgentOps.
4. Record provider state, transcript references, artifacts, and terminal status.
5. Return runtime evidence to the caller. Do not convert provider retries,
   reconnects, idle states, or failures into Plan, Candidate, or verdict state.
6. A validator session may supply judgment to Validate, but only Validate writes
   `verdict.v2`.

NTM, Codex exec, native processes, Agent Mail, and Gas City are replaceable
adapters. Use them only when the caller selected that execution shape. A
single local agent pays no factory coordination cost. Model identity, when
recorded, is a declared runtime fact like context identity — see
[references/model-dispatch.md](references/model-dispatch.md).
