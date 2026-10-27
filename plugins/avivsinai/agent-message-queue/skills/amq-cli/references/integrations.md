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

Or create `~/.amqrc` with `{"root": ".agent-mail"}`. Root precedence and the
Git worktree rules are in [Environment Rules](operations.md#environment-rules).

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

Use `amq doctor --ops`; see [Diagnostics](operations.md#diagnostics).

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

For the formal envelope and stability notes, see [the adapter contract](https://github.com/avivsinai/agent-message-queue/blob/main/docs/adapter-contract.md).
