---
name: using-gc
description: Operate an explicitly selected Gas City as
---
# Using GC

Use Gas City only when the caller explicitly selects it. Treat it as a
replaceable execution adapter, not a completion or correctness boundary.

Keeping quest state inside the substrate is what keeps GC replaceable: the
moment a GC "close" is read as an AgentOps completion, swapping the executor
would silently change what "done" means.

Named failure mode — **quest-state leakage**: a GC stall, retry, or internal
close surfacing in a report as if it were an RPI phase or verdict.

Anti-pattern: falling back to Gas City because it happens to be running.
Corrective: route through GC only on explicit operator selection; an available
substrate is not a selected one.

1. Accept complete explicit packets and a caller-selected city/executor.
2. Map each packet to one role and disjoint workspace.
3. Observe runtime state and return candidate, evidence, or error per packet.
4. Keep GC quests, attempts, stalls, and internal close state inside the
   substrate. They do not become Plan, Candidate, RPI, or verdict state.
5. A fresh GC judge may provide evidence to Validate; only Validate writes
   `verdict.v2`.

This skill performs no automatic selection, retry, semantic validation, Git,
integration, closure, release, or delivery.
