# Orchestrator Integrations

Use these commands when AMQ is the messaging layer underneath an external orchestrator.

AMQ's core transport is still the **message**. These adapters are intentionally narrow: they translate external lifecycle or task events into ordinary AMQ messages.

## Root Resolution

For orchestrator-spawned agents, make the queue discoverable even when the
process starts outside an AMQ-enabled repo. Global settings are fallbacks and
do not shadow a project-local config:

```bash
export AMQ_GLOBAL_ROOT="$HOME/.agent-mail"
```

Or create `~/.amqrc`:

```json
{"root": ".agent-mail"}
```

Root precedence:

```text
explicit --root > AM_ROOT > project-local .amqrc > AMQ_GLOBAL_ROOT > conditional implicit fallbacks
```

Inside a Git worktree or bare repository, the only implicit fallback is the
repository-local detected `.agent-mail`; an implicit `~/.amqrc` is ineligible.
Outside Git, `~/.amqrc` precedes eligible local `.agent-mail` detection.
Auto-detection covers `.agent-mail/<session>` session roots without `.amqrc`.
Custom root names still need `.amqrc`, explicit flags, or environment variables.

If an orchestrator leaves the terminal pinned to another root while cwd has an
initialized local queue, implicit participating commands refuse rather than
silently using the pin. Repin to the cwd-local queue, route deliberately with
`--session`/`--project`, or pass an explicit `--root` to confirm the active
queue; ordinary pin checks still apply.

## Symphony

Lightweight optional hook adapter.

Patch `WORKFLOW.md` once:

```bash
amq integration symphony init --me codex
amq integration symphony init --me codex --check
```

Emit lifecycle events from hooks:

```bash
amq integration symphony emit --event after_create --me codex
amq integration symphony emit --event before_run --me codex
amq integration symphony emit --event after_run --me codex
amq integration symphony emit --event before_remove --me codex
```

Known limitation: `init` rewrites `WORKFLOW.md` through structured YAML/Markdown parsing, so frontmatter comments and formatting may be normalized.

## Cline Kanban

Experimental bridge. Run it only if you are comfortable depending on a fast-moving preview WebSocket surface:

```bash
amq integration kanban bridge --me codex
amq integration kanban bridge --me codex --workspace-id my-workspace
```

Defaults:

- URL: `ws://127.0.0.1:3484/api/runtime/ws`
- Reconnect delay: `3s`
- Emits only on task session state transitions plus `task_ready_for_review`

## Runtime Diagnostics

```bash
amq doctor --ops
amq doctor --ops --json
amq doctor --root <exact-root> --ops
```

`doctor --ops` adds queue depth, sibling-session backlog hints, oldest unread
age, DLQ state, presence freshness, and integration hints on top of the base
`doctor` checks. A `sibling_backlog` hint includes an exact non-destructive
`amq list --session <name> --me <handle> --new` inspection command.

An explicit doctor root selects the inspected tree without changing the
terminal pin. Inspection continues with a mismatch warning. Mutating doctor
operations (`--fix-mailboxes` or `--ops --fix-wake-locks`) require the target
to match the pin unless the command uses an explicit non-empty `--root`
together with `--ignore-session-pin`. `--base-root` supplies config authority
for the target or one direct child and never waives the pin.

## Message Shape

Integration messages are self-delivered and carry metadata under `context.orchestrator`:

```json
{
  "orchestrator": {
    "version": 1,
    "name": "kanban",
    "transport": "bridge",
    "event": "task_ready_for_review",
    "workspace": {
      "id": "workspace-123",
      "path": "/abs/path/to/worktree"
    },
    "task": {
      "id": "task-42",
      "prompt": "Review PR #47",
      "column": "review",
      "state": "awaiting_review",
      "review_reason": "task_ready_for_review",
      "agent_id": "codex"
    }
  }
}
```

Common labels:

- `orchestrator`
- `orchestrator:symphony` or `orchestrator:kanban`
- `task-state:<state>`
- `handoff`
- `blocking`

For the formal envelope and stability notes, see [`docs/adapter-contract.md`](../../../docs/adapter-contract.md).
