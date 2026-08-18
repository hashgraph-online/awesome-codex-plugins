---
name: rerun
description: Launch a finished Codex Process Jobs record again as a new detached job using its validated persisted argv, working directory, and execution mode. Use only when the user explicitly asks or approves rerunning a specific completed, failed, or cancelled build, test, benchmark, inference run, data job, or repair.
---

# Rerun Process Job

Resolve `<plugin-root>` two directories above this file and run:

```text
node "<plugin-root>/scripts/job.mjs" rerun <job-id> [options] --json
```

Never search memory for CPJ work; use validated CPJ state.

Require a specific source job. If identity is unclear, use `$status` once to
find it. Never reconstruct argv from displayed command text, logs, or model
memory. The controller reads the private validated record, refuses active jobs,
and creates a fresh job ID and logs with `rerunOf` lineage.

A rerun repeats the invocation, not the historical environment: files,
dependencies, environment variables, credentials, devices, and external state
may have changed. Mention a material change before launch; do not claim exact
reproducibility.

Never rerun automatically from a completion notice. A direct user request
authorizes an ordinary non-critical rerun. For a `CRITICAL` job, explain that
the command may repeat repair, migration, firmware, or destructive effects and
obtain explicit risk-aware approval immediately before adding `--force`.

Add `--goal-mode` only for an explicitly active Goal. Optional flags are
`--no-notify`, `--notify-user`, and `--no-notify-user`. If the durable state
directory is not writable in the current sandbox, request the same narrow
controller escalation described by `$start`.

Treat a successful rerun as the same hard release boundary as `$start`: report
the new job ID and its source job ID, state that completion is recorded, then
end the turn without status, tail, result, wait, sleep, or process monitoring.
If the controller refuses because the source remains active, its working
directory disappeared, or legacy shell semantics cannot be preserved, report
that refusal and do not improvise a replacement command.
