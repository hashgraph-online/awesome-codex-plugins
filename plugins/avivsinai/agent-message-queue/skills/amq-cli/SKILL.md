---
name: amq-cli
version: 0.77.3 # x-release-please-version
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
eval "$(amq env --me <handle> --export)"
amq drain --include-body
```

For a named session, add `--session <name>` to `amq env`. Treat the evaluated
context as one terminal bound to one session. Use `--session` or `--project` for
deliberate routing; do not point a participating command at another queue with a
raw `--root`.

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

Use `amq <command> --help` for current flags. The repository README is the
canonical setup path.

## Safety and delivery rules

- A wake notification is attention, not consumption proof. Use receipts or
  `--wait-for drained` when delivery proof matters.
- Preserve the existing thread when replying. Drain again after a doorbell;
  the newest complete message body is authoritative.
- Cleanup is explicit through `amq cleanup`. Do not add automatic deletion.
- Before any wake mutation, run `amq wake check --me <handle> --json`. Act only
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
