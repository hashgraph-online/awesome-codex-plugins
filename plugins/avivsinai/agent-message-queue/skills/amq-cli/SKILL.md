---
name: amq-cli
version: 0.115.2 # x-release-please-version
description: Coordinate coding agents through AMQ. Use for agent messages, inboxes, receipts, sessions, wake delivery, cross-project routing, managed launches, or AMQ diagnostics. Use amq-spec for collaborative design; do not use this for general message queues or single-agent work.
metadata:
  short-description: Inter-agent messaging via AMQ CLI
  compatibility: claude-code, codex-cli, grok-cli, antigravity-cli
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

The default drain reads at most 20 messages in filename order, including held
mail. After a full batch, check `amq list --new --limit 1` and continue with bounded drains
as needed; do not assume the inbox is empty. Use `--limit 0` only for a known,
manageable batch. Urgent hold bypass does not change drain order.

Do not run `amq watch`, `amq monitor`, sleep-poll, or start another inbox
watcher under that live wake. A blocking wait holds your turn while the
doorbell queues behind it. When your work is done, finish the turn; do not
keep a tool running or send idle check-ins just to wait for mail.

A wake can hold its first doorbell for routine mail with the `hold_normal` and
`hold_low` settings; `5m` / `30m` is an opt-in example. The configured retry
policy applies after the first attempt.
Urgent priority skips the hold. Ordinary urgent mail still passes through
debounce and input deferral; urgent mail with the configured interrupt label
follows the interrupt path.
Use `--priority urgent` on `send` or `reply` for time-critical verdicts and
unblocking requests. Other review responses remain normal by default.

In Claude Code, `amq wake install-dialog-hook` makes the wake hold its doorbell
while AskUserQuestion, ExitPlanMode, or a permission dialog is open; the held
doorbell arrives after you answer, or when that turn ends.

Wake settings (hold, debounce, preview, bell, input deferral, interrupt notice)
apply to a running wake without a restart: `amq wake config --me <handle>`
shows them, `--hold-normal 5m --wait` sets one and waits for the wake to apply
it, `--unset <key>` falls back, and `--machine` sets this user's default.
Injection flags are fixed for a running wake. Exit codes and recovery are in
[wake operations](https://github.com/avivsinai/agent-message-queue/blob/main/docs/wake-operations.md#live-settings).

Without an injecting wake, use the receive methods in the operations guide.
A notify-only wake (`--inject-mode none`) paired with a supervisor `monitor`
service is a separate supported setup.

## Send useful handoffs

For one related batch, send one completion handoff with artifact paths, the
relevant source or digest, checks, failed or pending parts, and the next action
or actor. Send independent blockers promptly; send a partial result when the
receiver can act on it before the rest finishes.

Send status when work starts, a state, decision, or result changes, or an agreed
escalation is due. Avoid file-by-file completion notices and unchanged check-ins.
Automated callers own duplicate suppression by item, revision, and event;
AMQ threads correlate messages, but do not deduplicate repeated sends.

Use an explicit reply kind for task updates. A reply to a `todo` otherwise
inherits `todo` and can open another request. Progress uses `--kind status`;
completion uses `--kind status --labels done`; cancellation uses
`--kind decision --labels withdrawn`. State the result or cancellation
honestly: withdrawing a request does not mean its feature shipped.
The last `--refs` entry is the direct reply target; a list of refs is lineage,
not a batch-close operation. Close independent requests separately.

An unanswered message is a reply obligation, not evidence that work started.
Use the host harness's task and turn records when activity matters. Keep
declared task state, actual execution, approval waits, and delivery presence
separate. A live wake, a recent message, or an assigned tracker item does not
prove a task is running. Do not create work items from old coordination
messages without confirming an actual requested outcome and remaining gap.

## Route the task

| Need | Read or run |
|---|---|
| Send, reply, drain, inspect receipts, or diagnose | Use [the operations guide](references/operations.md). |
| Two-agent research and design, or a received message labeled `workflow:spec` | Use the `amq-spec` skill: do your own research before you read the partner's, then follow the `spec/<topic>` thread. |
| Co-op roles and phased collaboration | Read [co-op mode](references/coop-mode.md). |
| Claude Code Agent Teams | Read [swarm mode](references/swarm-mode.md). |
| Cross-project delivery or decision threads | Read [cross-project routing](references/cross-project.md). |
| Grok Bot on a registered Mac | Read [registered-machine execution](references/registered-machine.md). Select the machine before you resolve the project or session. |
| Two separate host queues or `amq-bridge` | Use companion `amq-bridge`, never a foreign `--root`. Read [two-host fleets](references/operations.md#two-host-fleets). |
| Symphony or Kanban adapters | Read [integrations](references/integrations.md). |
| Message schema and kinds | Read [message format](references/message-format.md). |
| Multi-round background review | Read [review loop](references/review-loop.md). |
| Buzz, ACP, or `amq-acp` | Companion `amq-acp` queues to `AMQ_ACP_TO`; pool workers must not drain. Chat must not pass `--root`, recipients, or argv, and `[Context]` is not routing. Read [amq-acp](https://github.com/avivsinai/agent-message-queue/blob/main/cmd/amq-acp/README.md). |
| Attach to a running harness session (`amq-remote up`, `submit`, `share`) | Read the [amq-remote reference](https://github.com/avivsinai/agent-message-queue/blob/main/cmd/amq-remote/README.md). |
| Reach this session from Buzz (`/amq-remote`) | Use the `amq-remote` skill. |

Use `amq <command> --help` for current flags. The repository README is the
canonical setup path.

## Safety and delivery rules

- A wake notification is attention, not consumption proof. Use receipts or
  `--wait-for drained` when delivery proof matters. A `drained` receipt proves
  ingestion, not that the requested work is complete.
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
