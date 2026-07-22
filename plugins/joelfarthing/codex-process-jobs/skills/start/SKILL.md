---
name: start
description: Launch a long-running local command as a durable detached process job, then release the assigning Codex turn instead of monitoring it. Use proactively when the user says background, detach, don't block, or keep working; when a command may take over 60 seconds or has uncertain duration; and for CMake builds, test suites, inference/model A/B runs, data processing, or device repair that should survive Codex App, VS Code, or CLI exit.
---

# Start Process Job

Resolve `<plugin-root>` as two directories above this `SKILL.md`. Run the job controller from that active plugin root:

```text
node "<plugin-root>/scripts/job.mjs" start [options] -- <command> [args...]
```

## When to route here

Use this skill instead of a blocking shell call when any of these is true:

- The user asks to background, detach, or keep working while a command runs.
- A local command is likely to take longer than about 60 seconds or its duration is uncertain.
- The user is likely to want lightweight progress checks while the command runs.
- A build, test, inference, evaluation, data-processing, or repair process should survive the current Codex client closing.

Do not route quick commands here merely because detachment is possible. Do not use it for a persistent server or watch process, when the command requires interactive stdin, when it intentionally daemonizes, or when it only starts work in an external service and then exits.

## Launch workflow

1. Require a concrete command and working directory. Do not invent consequential arguments.
2. Preserve direct argv exactly and shell-quote only when presenting it. Do not use `eval`.
3. Use direct argv mode by default. Use `--shell -- '<single command string>'` for Bash composition such as `set -o pipefail`, pipes, redirection, globbing, `[[ ... ]]`, or process substitution. `--shell` is fixed non-login `/bin/bash -c`; on macOS, remain compatible with the system Bash 3.2. Use `--posix-sh` only when the complete command is intentionally limited to portable POSIX `sh` syntax.
4. Add `--name <label>` when a concise recognizable label is useful.
5. Add `--critical` for filesystem/device repair, firmware operations, database migrations, destructive conversions, or any command whose interruption could worsen state.
6. Add `--goal-mode` only when this command belongs to an explicitly active Codex Goal. The visible Goal context is sufficient; if Goal activity is suggested but unclear and the supported `get_goal` tool is available, check it once. Never inspect Codex's private Goal database or infer Goal mode merely from repeated turns.
7. Run the controller once and return its job id, status, and log paths. A successful detached launch completes the job-launch work for this Codex turn even when the higher-level task will eventually depend on the result.
8. Report the launch and end the turn. If the same user request includes independent work, continue only that independent work without monitoring the job, then end the turn.

Supported options before `--`:

- `--name <label>`
- `--cwd <absolute-or-relative-directory>`
- `--critical`
- `--goal-mode`
- `--shell`
- `--posix-sh`
- `--no-notify` to opt out of the owning-thread completion turn
- `--notify-user` to request a best-effort OS notification for this job
- `--no-notify-user` to override a durable OS-notification preference for this job
- `--json`

## Safety and lifecycle

- Detached jobs receive no interactive stdin. If `sudo`, Polkit, a password, a confirmation, or any other prompt may be required, resolve that requirement in the foreground first. Prefer explicitly non-interactive forms such as `sudo -n` when appropriate.
- The launched command must remain in the foreground until its finite work is complete. Do not append `&`, use a daemonizing mode, or route a persistent server/watch process through CPJ. If a command merely asks an external service to begin work and then exits, track that service through its own blocking/status interface instead.
- `--shell` requires executable `/bin/bash`; CPJ checks this before creating the job. It never falls back to `/bin/sh` or the user's `$SHELL`. New shell jobs use non-login `-c` and ignore `BASH_ENV`/`ENV`; `--posix-sh` explicitly uses `/bin/sh -c`.
- A job is machine-scoped and survives Codex App, IDE, or CLI exit. Never add session-exit cleanup.
- Treat a successful controller return as a hard launch-turn release boundary. Do not read the status skill or call status, tail, result, `--wait`, `write_stdin`, sleep, `ps`, or any other polling or process probe for that job in the launch turn. Defer result-dependent work to the completion relay, a later user-initiated turn, or a later automatic continuation of an explicitly active Goal. General instructions to finish the higher-level task, persist, or not stop do not authorize same-turn monitoring; durable job state and the completion relay provide persistence. Only an explicit user request to keep this exact Codex turn open and wait for this process overrides the boundary. Under that override, follow the status skill's one-wait limit and yielded-session rule; inspect a result only after an explicit terminal CPJ state, otherwise end the turn without a replacement probe.
- For an ordinary pending-notification launch, the response MUST state all four facts: the recognizable job label/id and that it is running in the background; completion will be recorded and a live notification may appear; after it finishes, recap the outcome as soon as the conversation can pick it up; the user can request status any time. Paraphrase naturally, but do not omit any fact. Example: “I've started that <job label> in the background as <job-id>. Completion will be recorded; a live notification may appear. After it finishes, I'll recap the outcome as soon as our conversation can pick it up. You can ask me to check status any time.” The completion relay uses a separate transport, so do not promise an immediate live wake, imply that an exchange before completion can report the outcome, or guarantee the first post-terminal prompt while notification delivery is still in flight.
- For a `--goal-mode` launch, say instead that the job is running under the active Goal, completion is recorded durably, automatic Goal continuation or direct idle-thread delivery will pick up the terminal result, and status remains available on explicit user request. Do not imply that CPJ can suppress Goal's automatic `Continue` turns. On those continuations, work independently when possible; when result-gated, do not monitor the job and apply the host Goal blocked audit rather than narrating progress.
- When notification is `disabled` or `unavailable`, explain the status/result fallback instead.
- OS-level user notification is independent of the conversational completion relay. It is opt-in, best-effort, and may be unavailable in a headless Linux session even when conversational completion works.
- Do not place secrets in argv or redirect secrets into tracked logs. The controller stores argv and cwd, but never persists the inherited environment.
- Critical jobs refuse cancellation unless the user later gives explicit approval and `$cancel` is invoked with `--force`.
- The notification relay resumes the owning persistent Codex thread through guarded Desktop IPC or local app-server and starts a minimal synthetic completion turn containing sanitized job metadata only. It never embeds process output. Consent-gated `PostToolUse`, `Stop`, and `UserPromptSubmit` hooks can claim a terminal result at the next supported agent-loop boundary and require one short recap for every claimed completion. Give that recap even if a synthetic assistant announcement already appears in model context, because context does not prove the assigning client rendered it. A possible one-time duplicate is intentional. Explicit status/result requests retrieve durable state directly.

For storage repair specifically, preserve the exact target device, mounted/unmounted state, and repair flags supplied by the user or current diagnostic evidence. Never infer a device node from name alone.
