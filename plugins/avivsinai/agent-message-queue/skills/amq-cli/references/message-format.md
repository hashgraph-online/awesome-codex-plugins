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
  "notify": "wake",
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
- `notify`: optional (`wake` or `passive`). Missing or empty uses normal wake eligibility. Passive mail stays readable and drains normally, but never starts or extends a turn. Sends refuse urgent plus passive, and stored urgent messages remain eligible. A reply chooses its own intent. A follow-up or news notice carries the intent the sender chose with `--reminder-notify`.
- `kind`: optional; one of the kinds below.
- `labels`: optional list of tags for filtering.
- `context`: optional JSON object for structured metadata.
- `reply_by`: optional RFC 3339 UTC time, to the second, by which the sender expects a reply; advisory; set by a send or reply with `--follow-up`.
- `news_by`: optional RFC 3339 UTC time, to the second, by which the sender expects the recipient's first reply about this request; advisory; set by a send or reply with `--news-within`.

Routing fields (set automatically by CLI — do not hand-craft):
- `reply_to`: optional sender identity for routing replies (e.g., `claude@collab`). Set on cross-session and cross-project sends.
A binary older than the release that added `reply_by` ignores it, and a bridge of that age that re-marshals a header on receipt drops it on that copy.
- `reply_project`: optional sender project name for cross-project reply routing (e.g., `my-project`). Present only on cross-project messages.
- `from_project`: optional sender project identity stamped on cross-project sends.

Notes:
- Don’t edit message files directly; use the CLI.
- On macOS and Linux, publication into `inbox/new` is a no-replace rename: a
  colliding name keeps the existing file and the new attempt, rather than
  overwriting. Readers still scan only `new` and `cur`.
- The CLI fills `id` and `created`. A single-recipient send defaults to the pair's
  thread. Set `--thread` explicitly when sending to multiple recipients.
- `reply_to`, `reply_project`, and `from_project` are transport metadata stamped by the CLI.
- Delivery outcomes are tracked separately in consumer-local receipt files. `drained` means the consumer ingested the message; `dlq` means ingest failed and the message moved to DLQ.
- `amq drain --for-turn` writes the same `drained` receipt for a passive message it shows as a digest: the consumer ingested the original, which stays in `inbox/cur`, and received its compact representation. Neither the receipt nor the digest proves that the model read every byte of the body or did the work.

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

## Decision for the owner

A question to the owner (`user`) may carry its options under
`context.decision`; the board's Inbox shows it as one card with one answer
command per option:

```json
{"decision": {
  "options": [
    {"label": "Opt-in", "summary": "Off unless the user turns it on.", "pros": ["no surprise for current users"], "cons": ["few will find it"]},
    {"label": "On by default", "summary": "On for every wake.", "pros": ["protects everyone"], "cons": ["changes behaviour for current users"]}
  ],
  "recommended": "Opt-in",
  "blocking": false,
  "if_later": "The guard stays opt-in; nothing waits."
}}
```

Send it with `amq send --to user --kind question --subject "..." --body @file
--context @decision.json`. `send` and `reply` refuse, as a usage error that
names the field, a decision that is not an object with 2 to 6 options; a
label that is empty, longer than 40 characters, starts or ends with white
space, starts with `-` or `@`, repeats another label (ignoring case), or holds
a control character (C0, DEL, C1, or the Unicode line and paragraph
separators U+2028 and U+2029); a summary longer than 200 characters; more than 5 pros or 5 cons,
or one longer than 120 characters; a `recommended` that is not one of the
labels; a `blocking` that is present and not `true` or `false`; an `if_later` longer than 200
characters; or an unknown field. A message with no `decision` key is not
checked. The board reads the decision by the same rule and shows a message
whose decision breaks it as a plain question.

## Verified Buzz event

A message that the machine agent inside `amq-remote serve` delivers from the
owner's Buzz channel message to a session's AMQ inbox carries
`context.buzz.event`: the event's signed fields (`id`, `pubkey`,
`created_at`, `kind`, `tags`, `content`, `sig`), re-encoded; verification
uses the values. The machine agent delivers a message only for an event that
the relay sent it and that passes every check: the id and signature verify,
the kind is 9 (a plaintext channel message), the event has exactly one `h`
tag, equal to a channel the machine agent serves, and `pubkey` is the owner's
key. An event that fails a check is dropped and delivers no message; there is
no partial form.

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
