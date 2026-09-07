---
name: start
description: Launch an ordinary finite local workload as a durable detached process job, then release the assigning Codex turn instead of monitoring it. Use proactively for downloads, builds, test suites, evaluations, benchmarks, inference/model A/B runs, data jobs, and repairs whose underlying work may exceed 60 seconds or has uncertain duration. The user-visible parent must launch the job directly; never delegate local process execution or monitoring to a subagent.
---

# Start Process Job

Resolve `<plugin-root>` as two directories above this `SKILL.md`.

Never search memory for CPJ work; use validated CPJ state.

The user-visible parent owns every CPJ launch and completion. Never delegate
local process execution, launch, waiting, monitoring, or CPJ ownership to a
spawned subagent. A subagent can analyze independent material only.

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

On a consented CPJ `PreToolUse` pause, classify the underlying workload from
context, not its executable name. A qualifying script, download, inference
runner, or wrapper uses its original foreground payload through CPJ without the
escape. Retry with `# cpj:foreground` only when the command is clearly quick,
excluded, persistent, already detached, or explicitly requested in the
foreground. Never escape because it is unfamiliar or to avoid turn release.

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

This boundary has no same-turn wait exception. A request to report the final
result when it finishes is an eventual-delivery request, not permission to keep
the launch turn open. If the user explicitly requires foreground execution in
the same turn, do not use CPJ for that command. State the tradeoff and run the
foreground command only with the user's approval. Never substitute polling.

## Report and stop

Name this workflow **Codex Process Jobs**, never a detached-job skill or
workflow. Before launch, use at most one short sentence: say that Codex Process
Jobs will run it in the background and hand back immediately. Do not narrate
procedure, payload, argv, cwd, controller mechanics, metadata, or validation.

After success, use no more than two short sentences: identify the background
job ID, then say that a completion notification and any requested summary
should appear when it finishes; status is available on request. If delivery is
unavailable or disabled, say completion is recorded and status/result is
available. Never promise an immediate wake.

For `--goal-mode`, say the job is durably tracked under the Goal and will be
picked up by completion delivery, a hook, or Goal continuation. Automatic
continuation is not permission to monitor: do independent work or apply the host
Goal blocked audit.

A job is machine-scoped and survives Codex App, IDE, or CLI exit. Never add
session-exit cleanup. Critical jobs later require explicit approval and
`$cancel --force`.
