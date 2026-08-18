---
name: agy-native
description: 'Use an explicitly selected AGY runtime for Triggers: "agy", "antigravity", "AGY evidence".'
---
# AGY Native

Use AGY only when the caller explicitly selects that runtime. Discover its live
command surface with `agy --help` (and `agy models` for the current model set)
before acting, and scope every session to the supplied workspace and packet.

Discovering the live command surface before acting works because AGY's CLI
changes faster than any skill text: a remembered flag is a guess, while a
freshly listed one is evidence.

## Permission posture (disclose it; never assume it)

The posture a run gets is chosen by flags, so name it explicitly:

- Default `agy` runs interactively and prompts for each tool permission.
- `--dangerously-skip-permissions` auto-approves every tool call — use it only
  when the packet's declared effects and the caller's authorization cover that
  blast radius.
- `--sandbox` restricts the session's terminal access.
- Print mode (`agy -p` / `--print`) is the sanctioned headless path and carries
  a built-in `--print-timeout` (default 5m); a run that exceeds it is killed and
  reported as timed out, not as a result.

A reader who sets none of these gets AGY's interactive default, not a scoped
run. Match the posture to the declared effects and disclose which one was used.

## When AGY is unavailable

If `agy` is not installed or its command surface cannot be discovered, report the
absence as a disclosed fact and stop. Do not fall back to another runtime, do not
guess a command surface, and never route through `claude -p`.

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
