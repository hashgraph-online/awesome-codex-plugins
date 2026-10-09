---
name: amq-cli
version: 0.94.0 # x-release-please-version
description: Coordinate coding agents through AMQ. Use for agent messages, inboxes, receipts, sessions, wake delivery, cross-project routing, managed launches, or AMQ diagnostics. Use amq-spec for collaborative design; do not use this for general message queues or single-agent work.
metadata:
  short-description: Inter-agent messaging via AMQ CLI
  compatibility: claude-code, codex-cli, grok-cli
---

# AMQ CLI

Use the `amq` CLI for all queue operations. Never edit Maildir files directly.
AMQ transports coordination; the caller or orchestrator still owns task planning,
worktrees, approvals, and delivery.

## Start in the correct context

Inside `coop exec`, use the environment as provided and run bare `amq` commands.
Do not override `--me` or reconstruct the root. Outside it, resolve and export the
complete context before reading or sending:

```bash
amq_context="$(amq env --me "<handle>" --export)" && eval "$amq_context" &&
  amq drain --include-body
```

For a named session, add `--session <name>` to `amq env`. Treat the evaluated
context as one terminal bound to one session. Use `--session` or `--project` for
deliberate routing; do not point a participating command at another queue with a
raw `--root`.

## Receive under a live wake

If session-start context says `wake=live(...)`, or
`amq wake check --me <handle> --json` reports `live_wake: true` with an
injection mode other than `none`, the wake delivers a doorbell for you.
Run `amq drain --include-body` when it fires, then act on the messages.

Do not run `amq watch`, `amq monitor`, sleep-poll, or start another inbox
watcher under that live wake. A blocking wait holds your turn while the
doorbell queues behind it. When your work is done, finish the turn; do not
keep a tool running or send idle check-ins just to wait for mail.

A wake can hold its first doorbell for routine mail with the `hold_normal` and
`hold_low` settings; `5m` / `30m` is an opt-in example. One drain takes all
pending mail, and the configured retry policy applies after the first attempt.
Urgent priority skips the hold. Ordinary urgent mail still passes through
debounce and input deferral; urgent mail with the configured interrupt label
follows the interrupt path.
Use `--priority urgent` on `send` or `reply` for time-critical verdicts and
unblocking requests. Other review responses remain normal by default.

Wake settings (hold, debounce, preview, bell, input deferral, interrupt notice)
live in `.wake.settings` and apply to a running wake. Change your own or a
peer's wake without a restart:

```bash
amq wake config --me <handle>                           # show
amq wake config --me <handle> --hold-normal 5m --wait   # set, wait for apply
amq wake config --me <handle> --unset hold_normal       # back to default
amq wake config --me <handle> --reset --hold-low 30m    # replace the file
```

A refused file shows `file: refused: <err>` with default rows (the wake keeps
its last applied settings); `set` and `--unset` exit 1 and point at `--reset`.
A running wake that reports no live settings shows `unreported`: `--wait` exits
6 after 5 s, and `set`/`--unset` on an absent file exit 6 after the same 5 s.
Causes: an older image, a failed status write, or a resumed wake still storing
its command-line settings in the file (wait a moment). Otherwise restart that
wake (a resume seeds the file) or `--reset` with the full set. A missing
mailbox exits 3.

Flags fixed for a running wake (`--inject-mode`, `--inject-via`, `--inject-arg`,
`--inject-cmd`, `--interrupt-cmd`, `--retry-until`) are refused; restart the
wake through its owning terminal after `amq wake check`. Repair, `coop exec`,
keepalive, and self-upgrade keep the stored settings; a resume with no file
seeds it once from its argv settings flags.

Without an injecting wake, use the receive methods in the operations guide.
A notify-only wake (`--inject-mode none`) paired with a supervisor `monitor`
service is a separate supported setup.

## Route the task

| Need | Read or run |
|---|---|
| Send, reply, drain, inspect receipts, or diagnose | Use [the operations guide](references/operations.md). |
| Two-agent research and design | Use the `amq-spec` skill. |
| Co-op roles and phased collaboration | Read [co-op mode](references/coop-mode.md). |
| Claude Code Agent Teams | Read [swarm mode](references/swarm-mode.md). |
| Cross-project delivery or decision threads | Read [cross-project routing](references/cross-project.md). |
| Grok Bot on a registered Mac | Read [registered-machine execution](references/registered-machine.md). |
| Symphony or Kanban adapters | Read [integrations](references/integrations.md). |
| Message schema details | Read [message format](references/message-format.md). |
| Multi-round background review | Read [review loop](references/review-loop.md). |
| Attach to a running harness session | Read the [amq-remote reference](https://github.com/avivsinai/agent-message-queue/blob/main/cmd/amq-remote/README.md). |

Use `amq <command> --help` for current flags. The repository README is the
canonical setup path.

## Remote

`amq-remote` is a companion binary, not an `amq` subcommand. It attaches to a
harness session that is already running. Targets are declared in
`<AM_ROOT>/extensions/remote/manifest.json` (`claude`, `codex`, `pi`, or
`fake`). `up` supervises the endpoint; `submit`, `status`, `wait`, and
`cancel` talk to it; `share` mints the session body key. A manifest `relay`
object shares a target with its owner over a Buzz relay. DM commands require
the pinned `native_session_id` and run only while that session is attached;
Desktop presence reports the attachment status and honors the pin when one
is set.
`doctor` lists each failing boundary under `failing` and exits 6 while any
remains. Flags and exit codes
are in the [amq-remote reference](https://github.com/avivsinai/agent-message-queue/blob/main/cmd/amq-remote/README.md). The design is
[the remote-control ADR](https://github.com/avivsinai/agent-message-queue/blob/main/docs/adr-remote-control.md). Pinned seams are
[the compatibility manifest](https://github.com/avivsinai/agent-message-queue/blob/main/docs/remote-compat.md).

## Safety and delivery rules

- A wake notification is attention, not consumption proof. Use receipts or
  `--wait-for drained` when delivery proof matters.
- Preserve the existing thread when replying. Drain again after a doorbell;
  the newest complete message body is authoritative.
- Cleanup is explicit through `amq cleanup`. Do not add automatic deletion.
- Before any wake mutation, run `amq wake check --me "<handle>" --json`. Act only
  when `restart_capability=agent_safe`; otherwise preserve state and report the
  required operator action.
- Keep cross-host payloads outside privileged inboxes until the configured
  bridge has authenticated and applied them. Never copy or remote-drain a
  foreign Maildir as a substitute for routing.
- Do not translate native Windows injection into Unix `wake` or `coop exec`.
  Read the platform section in the operations guide when Windows is involved.
- Dangerous provider bypass flags belong only on an operator-controlled direct
  `coop exec` command. Do not place them in committed launch configuration.

The full command catalog, environment precedence, setup flow, platform notes,
operator gates, and examples are in [the operations guide](references/operations.md).
