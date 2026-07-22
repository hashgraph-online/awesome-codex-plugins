---
name: cancel
description: Safely request termination of a tracked detached process group using PID identity validation and a SIGTERM-to-SIGKILL grace period. Use only when the user asks to stop a job; critical repair, migration, firmware, or destructive jobs require explicit risk-aware approval and --force.
---

# Cancel Process Job

Resolve `<plugin-root>` as two directories above this `SKILL.md` and run:

```text
node "<plugin-root>/scripts/job.mjs" cancel <job-id> [--force] [--json]
```

## Cancellation rules

- Never cancel a job merely because a Codex task, client, terminal, or session is closing.
- Require a specific job id. Inspect `$status <job-id>` first if identity or current state is uncertain.
- For a non-critical job, the user's direct request to stop that job authorizes normal cancellation.
- For a `CRITICAL` job, explain that interruption can worsen partial state and obtain explicit approval immediately before passing `--force`.
- `--force` bypasses the critical-job guard; it does not skip the graceful phase. The controller sends SIGTERM to the validated process group, waits up to five seconds, then uses SIGKILL only if necessary.
- If PID identity does not match, the controller refuses to signal the process. Do not work around that protection with an untracked `kill` unless the user separately authorizes manual recovery after inspection.

For filesystem or device repair, cancellation can leave metadata partially rewritten. Prefer waiting unless continued execution presents a greater concrete risk.
