# Message Format Cheatsheet

AMQ messages are Markdown files with a JSON frontmatter header:

```text
---json
{
  "schema": 1,
  "id": "<msg_id>",
  "from": "claude",
  "to": ["codex"],
  "thread": "p2p/claude__codex",
  "subject": "Optional summary",
  "created": "<RFC3339 timestamp>",
  "refs": ["<related_msg_id>"],

  "priority": "normal",
  "kind": "question",
  "labels": ["bug", "parser"],
  "context": {"paths": ["internal/cli/send.go"], "focus": "error handling"},

  "reply_to": "claude@collab",
  "reply_project": "my-project",
  "from_project": "my-project"
}
---
<markdown body>
```

Field notes:
- `schema`: integer schema version (currently 1).
- `id`: globally unique message id (also the filename stem on disk).
- `from`: sender handle.
- `to`: list of receiver handles.
- `thread`: thread id string. For p2p, use `p2p/<a>__<b>` with lexicographic ordering.
- `subject`: optional short summary.
- `created`: RFC3339 timestamp.
- `refs`: optional list of related message ids (e.g., replies).
- `priority`: optional (`urgent`, `normal`, `low`).
- `kind`: optional (e.g., `review_request`, `review_response`, `question`, `answer`, `status`, `todo`).
- `labels`: optional list of tags for filtering.
- `context`: optional JSON object for structured metadata.

Routing fields (set automatically by CLI — do not hand-craft):
- `reply_to`: optional sender identity for routing replies (e.g., `claude@collab`). Set on cross-session and cross-project sends.
- `reply_project`: optional sender project name for cross-project reply routing (e.g., `my-project`). Present only on cross-project messages.
- `from_project`: optional sender project identity stamped on cross-project sends.

Notes:
- Don’t edit message files directly; use the CLI.
- On macOS and Linux, publication into `inbox/new` is a no-replace rename: a
  colliding name keeps the existing file and the new attempt, rather than
  overwriting. Readers still scan only `new` and `cur`.
- The CLI auto-fills `id`, `created`, and a default `thread` when not provided.
- `reply_to`, `reply_project`, and `from_project` are transport metadata stamped by the CLI.
- Delivery outcomes are tracked separately in consumer-local receipt files. `drained` means the consumer ingested the message; `dlq` means ingest failed and the message moved to DLQ.

## Integration Metadata

Messages emitted by `amq integration ...` commands store orchestrator-specific metadata under `context.orchestrator`.

Example:

```json
{
  "labels": ["orchestrator", "orchestrator:kanban", "task-state:awaiting_review", "handoff"],
  "context": {
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
        "state": "awaiting_review"
      }
    }
  }
}
```

Label conventions:

- Always: `orchestrator`, `orchestrator:<name>`
- When state is known: `task-state:<state>`
- Review-ready handoffs: `handoff`
- Failed / interrupted work: `blocking`
