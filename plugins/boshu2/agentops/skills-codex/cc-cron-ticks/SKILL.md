---
name: cc-cron-ticks
description: Run cron tick scheduling.
---

# cc-cron-ticks (Codex)

This is the Codex-runtime entry point. The full doctrine — overview, critical
constraints, the four-phase workflow, output spec, quality rubric, examples,
troubleshooting, and currency anchor — lives in the source skill
[`../../skills/cc-cron-ticks/SKILL.md`](../../skills/cc-cron-ticks/SKILL.md).
Read it first.

Codex has **no `CronCreate`/`CronList`/`CronDelete` tools and no `schedule`
surface** — that scheduler surface does not exist here. The execution
profile for delivering the same outcome (a wall-clock-cadenced, idempotent drive
tick) on Codex is in [`prompt.md`](./prompt.md): use OS-level scheduling
(launchd / systemd-timer / `cron(8)`) firing a thin idempotent tick body, never
a different agent CLI as the executor.
