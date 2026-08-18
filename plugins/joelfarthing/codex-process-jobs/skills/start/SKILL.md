---
name: start
description: Launch an ordinary finite local workload as a durable detached process job, then release the assigning Codex turn instead of monitoring it. Use proactively for builds, test suites, evaluations, benchmarks, inference/model A/B runs, data jobs, and repairs whose underlying work may exceed 60 seconds or has uncertain duration, even when a task-specific workflow emits a quick wrapper or launcher. Also use when the user explicitly asks to enable or disable CPJ's experimental live CLI completion delivery.
---

# Start Process Job

Resolve `<plugin-root>` as two directories above this `SKILL.md`.

Never search memory for CPJ work; use validated CPJ state.

## Optional live CLI completion

Only when the user explicitly requests it, configure CPJ's experimental live
CLI delivery with:

```text
node "<plugin-root>/scripts/job.mjs" config --cli-live-injection true --json
codex app-server daemon start
```

The official App Server daemon must be running before an ordinary `codex` TUI
starts, so tell the user to restart every open CLI session afterward. Do not
enable remote control, create another service, edit Codex configuration, or
start the daemon merely because a job was launched. The normal CPJ fallback
remains authoritative if the daemon or its private socket is unavailable.

Disable the CPJ preference with `config --cli-live-injection false`. Stop the
official daemon only if the user explicitly asks and it is not needed by other
Codex work.

## Launch exactly once

Prefer direct argv:

```text
node "<plugin-root>/scripts/job.mjs" start \
  --name "<label>" --cwd "<working-directory>" --json -- \
  <command> [args...]
```

Use fixed non-login Bash only for a validated shell composition:

```text
node "<plugin-root>/scripts/job.mjs" start \
  --name "<label>" --cwd "<working-directory>" --shell --json -- \
  '<single finite foreground command>'
```

All controller options, including `--json`, MUST precede `--`; that separator
ends controller parsing. Shell mode requires exactly one command string after
it. Never use `eval`.

CPJ writes private durable state under
`${CODEX_HOME:-$HOME/.codex}/process-jobs`. Before the first controller call,
use the host permission context instead of probing the filesystem. If that
directory is not writable in the current sandbox, request
`sandbox_permissions: "require_escalated"` on the first call with a narrow
justification and, when supported, prefix
`["node", "<plugin-root>/scripts/job.mjs"]`. Do not waste a call on a
predictable `EPERM`, weaken the sandbox, or edit Codex configuration.

## Route and compose

Use CPJ when the user asks to detach/background work, or when a finite local
workload may exceed about 60 seconds, has uncertain duration, should survive a
client exit, or merits later lightweight status checks.

Exclude quick commands, interactive stdin, servers/watchers, intentional
daemons, remote/external services, and fire-and-exit launchers. The tracked
process must remain in the foreground until the real workload ends.

Task-specific skills own command construction, preflight checks, arguments, and
correctness gates. CPJ owns execution lifecycle for qualifying finite local
workloads. Preserve a validated foreground argv or shell string. If a workflow
emits a detached launcher, do not pass that launcher through CPJ unchanged:
prefer its foreground payload, or a supported mode that remains alive until the
workload finishes and propagates its terminal status. Otherwise leave it with
its external lifecycle owner.

## Required choices

- Require a concrete command and cwd; never invent consequential arguments.
- Default to direct argv. Use `--shell` for Bash features and `--posix-sh` only
  for intentionally portable POSIX syntax.
- Add `--critical` for repair, firmware, migration, destructive conversion, or
  any operation whose interruption could worsen state.
- Add `--goal-mode` only when this command belongs to an explicitly active
  Codex Goal. If unclear and `get_goal` exists, check once; never inspect private
  Goal storage or infer Goal mode from repeated turns.
- Optional controller flags before `--`: `--no-notify`, `--notify-user`,
  `--no-notify-user`, and `--json`.

Detached work receives no interactive stdin. Resolve passwords, confirmations,
sudo, or Polkit in the foreground first and prefer non-interactive checks such
as `sudo -n`. `--shell` requires `/bin/bash` and must remain compatible with
macOS Bash 3.2. Never put secrets in argv or tracked logs.

For storage repair, preserve the evidenced target device, mount state, and
flags. Never infer a device node from its name.

## Hard turn boundary

Treat a successful controller return as a hard launch-turn release boundary.
Do not read the status skill or call status, tail, result, `--wait`,
`write_stdin`, sleep, `ps`, or another process probe in the launch turn.
Result-dependent work resumes through completion delivery, a later
user-initiated turn, or a later automatic continuation of an explicitly active
Goal. If the same user request includes independent work, continue only that
independent work.

Only an explicit user request to keep this exact Codex turn open and wait
overrides the boundary. Then follow the status skill's one-wait and
yielded-session rule; inspect a result only after an explicit terminal CPJ
state. Never substitute polling.

## Report and stop

For an ordinary pending notification, state conversationally:

1. the label/id and that it is running in the background;
2. completion is recorded and a live notification may appear;
3. after it finishes, recap the outcome as soon as the conversation can pick it
   up; and
4. status is available on request.

Do not guarantee an immediate wake. If notification is unavailable or disabled,
explain the status/result fallback.

For `--goal-mode`, say the job is durably tracked under the Goal and will be
picked up by completion delivery, a hook, or Goal continuation. Automatic
continuation is not permission to monitor: do independent work or apply the host
Goal blocked audit.

A job is machine-scoped and survives Codex App, IDE, or CLI exit. Never add
session-exit cleanup. Critical jobs later require explicit approval and
`$cancel --force`.
