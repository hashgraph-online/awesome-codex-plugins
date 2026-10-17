---
name: cancel
description: Safely request termination of a tracked detached process group using PID identity validation and a SIGTERM-to-SIGKILL grace period. Use only when the user asks to stop a job; critical repair, migration, firmware, or destructive jobs require explicit risk-aware approval and --force.
---

# Cancel Process Job

Resolve `<plugin-root>` as two directories above this `SKILL.md` and run:

```text
node "<plugin-root>/scripts/job.mjs" cancel <job-id> [--force] --json
```

Never search memory for CPJ work; use validated CPJ state.

If `${CODEX_HOME:-$HOME/.codex}/process-jobs` is not writable in the current
sandbox, request narrow controller escalation on the first call; do not probe
for a predictable `EPERM`.

Never cancel because a Codex task, client, or terminal is closing. Require a
specific job id; use `$status <job-id>` first only if identity/state is unclear.
A direct request authorizes normal cancellation of a non-critical job.

For a `CRITICAL` job, explain that interruption can worsen partial state and
obtain explicit approval immediately before `--force`. This bypasses only the
critical guard: the controller still validates PID identity, sends SIGTERM to
the process group, waits up to five seconds, and uses SIGKILL only if needed.
Never bypass an identity refusal with untracked `kill` without separate
authorization after inspection.

Filesystem/device repair can leave metadata partially rewritten. Prefer waiting
unless continued execution presents a greater concrete risk.
