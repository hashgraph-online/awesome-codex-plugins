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
- `schema`: integer message schema version; this document describes version 1.
- `id`: globally unique message id (also the filename stem on disk).
- `from`: sender handle.
- `to`: list of receiver handles.
- `thread`: thread id string. For p2p, use `p2p/<a>__<b>` with lexicographic ordering.
- `subject`: optional short summary.
- `created`: RFC3339 timestamp.
- `refs`: optional list of related message ids (e.g., replies).
- `priority`: optional (`urgent`, `normal`, `low`).
- `kind`: optional; one of the kinds below.
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

## Message kinds

| Kind | Reply kind | Default priority | Purpose |
| --- | --- | --- | --- |
| `review_request` | `review_response` | normal | Request review. |
| `review_response` | - | normal | Return review findings. |
| `question` | `answer` | normal | Ask for a decision or fact. |
| `answer` | - | normal | Answer a question. |
| `decision` | - | normal | Record a decision. |
| `brainstorm` | - | normal | Explore options. |
| `status` | - | low | Report progress or state. |
| `todo` | - | normal | Assign work. |

## Integration metadata

Messages emitted by `amq integration ...` commands carry orchestrator metadata
under `context.orchestrator`; the shape and labels are in
[integrations](integrations.md#message-shape).
