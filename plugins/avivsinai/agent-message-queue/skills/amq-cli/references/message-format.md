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
| `todo` | `status` | normal | Assign work. |

## Integration metadata

Messages emitted by `amq integration ...` commands carry orchestrator metadata
under `context.orchestrator`; the shape and labels are in
[integrations](integrations.md#message-shape).

## Verified Buzz event

A prompt that `amq-acp` delivers from a Buzz DM can carry
`context.buzz.event`: the event's signed fields (`id`, `pubkey`,
`created_at`, `kind`, `tags`, `content`, `sig`), re-encoded; verification
uses the values. `amq-acp` writes the key only when it fetched the event by
the id of the DM's triggering event, the id and signature verify, the id
matches, the kind is 9 (a plaintext channel message), and the event has
exactly one `h` tag, equal to the channel the prompt arrived on. Otherwise it
writes no key and the message is unverified; there is no partial form.

The key's presence is not provenance: any local sender can write header
context (`amq send --context`, `amq reply --context`). A gate that acts on the
event re-runs every check itself:

- the id (NIP-01 `CheckID`) and the signature (`VerifySignature`);
- kind 9;
- exactly one `h` tag, equal to the channel the gate expects;
- `pubkey` equal to the owner key the gate pins itself.

The event proves that `pubkey` signed `content` in that channel at
`created_at`; it does not say who owns the agent. The gate also acts on
`content` (never on the body), records consumed event ids, bounds both the
age and the future skew of `created_at`, and binds the answer to its request
(a reply tag that names the request event, or a nonce in `content`).
