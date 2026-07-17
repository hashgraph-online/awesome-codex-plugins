---
name: agy-native
description: Use an explicitly selected AGY runtime for
---
# AGY Native

Use AGY only when the caller explicitly selects that runtime. Discover its live
command surface before acting and scope every session to the supplied workspace
and packet.

Discovering the live command surface before acting works because AGY's CLI
changes faster than any skill text: a remembered flag is a guess, while a
freshly listed one is evidence.

Named failure mode — **wrapper drift**: invoking AGY through remembered
syntax that silently changed, producing runs that look scoped but are not.

Anti-pattern: reusing one AGY session for both author and validator roles
because starting a second session is slower. Corrective: keep the identities
distinct; a shared session forfeits the fresh-judgment guarantee that makes
the validator's evidence usable.

- Keep author and validator sessions distinct when AGY supplies both roles.
- Persist the runtime conversation/context identity and artifact references.
- Validators remain read-only and hand judgment to Validate; they do not write
  the core verdict directly.
- AGY plugin, memory, permission, retry, and session state remain substrate facts
  and never become AgentOps phase, queue, or completion state.
- Never invoke `claude -p` through an AGY wrapper.

Return evidence to the caller and stop. Installation, plugin mutation, and
recurring scheduling require separate explicit authorization.
