---
name: tool-design-output
description: 'Design or audit what an agent tool returns: shape and trim payloads, paginate, report partial success, reference files and media, and add next-step hints. Use when tool output bloats the context window.'
user-invocable: true
argument-hint: '[tool whose result shape to design]'
---

# Tool Output Design

Every byte a tool returns costs context tokens and becomes part of the model's next input.
Design the result as that input.

## Procedure

1. **List what the agent needs to decide its next step.** Only those fields are
   essential. Everything else is optional detail or a follow-up call.
2. **Define a flat, named shape** for the result and keep it identical across calls.
3. **Decide the size policy**: default summary, expansion flags, cursor pagination,
   truncation limits, and references for blobs.
4. **Add navigation**: `hasMore` and cursor, GUI URLs, and a next-action hint.
5. **Handle mixed outcomes** with per-item status for anything that touches more than
   one item.
6. **Verify.** Run the tool once and read the raw result. Then run the agent and check how
   much of its context the tool results take. If they dominate, tighten the size policy.

## Rules with examples

### Shape the response (Response Shaper)

Never return the upstream payload as-is. Flatten nesting, select relevant fields, rename
cryptic keys, add computed fields, and convert machine encodings to readable ones
(ISO-8601 datetimes, not epoch seconds; `active: true`, not `status_code: 2`).

Before:

```json
{
  "data": {
    "id": "usr_123",
    "user": {
      "attributes": {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "contact": { "primary_email": "ada@example.com" },
        "perm": { "r": "admin" },
        "st": 2,
        "created": 1719800000
      }
    }
  }
}
```

After:

```json
{
  "id": "usr_123",
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "role": "admin",
  "active": true,
  "createdAt": "2024-07-01T02:13:20Z"
}
```

### Spend tokens deliberately (Token-Efficient Response)

- Essential fields only. Codes over prose where a code is unambiguous.
- Truncate long text fields at a documented length and say so (`"bodyTruncated": true`).
- Count instead of listing when the agent needs the number, not the items.
- Make the expensive part opt-in: `includeBody: false` by default, with the description
  telling the agent which call fetches the full item.
- Log response sizes so oversize results show up in traces.

### Paginate by cursor (Paginated Result)

Page numbers and offsets drift as data changes. A cursor that encodes the last item's
sort key, not a position, does not. Return:

```json
{
  "items": [],
  "count": 50,
  "hasMore": true,
  "nextCursor": "eyJhZnRlciI6ImN0Y18wNTAifQ",
  "nextAction": { "tool": "list_contacts", "args": { "cursor": "eyJhZnRlciI6ImN0Y18wNTAifQ" } }
}
```

Accept `limit` with a sensible default and a hard maximum. Keep ordering stable for the
same query. Always include `hasMore` explicitly, even when false.

### Summary first, detail on request (Progressive Detail)

Default to the summary the agent usually needs. Offer a `detail` enum
(`summary` | `full`) or specific `include*` flags for sections such as comments or
attachments, and document exactly what each level includes. Pair with a `get_*` tool
that returns one item in full.

### Say what to do next (Next-Action Hint)

A result can carry the suggested follow-up: tool name plus the parameters to pass, the
data still required, and alternative paths. This is the tool-side half of dependency
hints and removes a guess from the agent's loop.

```json
{
  "jobId": "job_9",
  "status": "queued",
  "nextAction": { "tool": "check_job_status", "args": { "jobId": "job_9" }, "afterSeconds": 30 }
}
```

### Link to the interface (GUI URL)

Any tool that creates or reads a resource with a web UI returns `viewUrl`, and `editUrl`
where editing exists. Use deep links to the specific resource. Note expiry for links to
sensitive resources.

### Report mixed outcomes per item (Partial Success)

Batch and multi-source tools never collapse to a single boolean. Return successes,
failures with reasons, summary counts, and a retry hint for exactly the failed items:

```json
{
  "total": 3,
  "succeeded": 2,
  "failed": 1,
  "results": [
    { "email": "a@example.com", "ok": true },
    { "email": "b@example.com", "ok": true },
    { "email": "c@example.com", "ok": false, "error": "mailbox full", "retryable": true }
  ],
  "nextAction": { "tool": "send_invites", "args": { "emails": ["c@example.com"] } }
}
```

### Reference large data instead of embedding it (Resource Reference)

Files and blobs travel as typed URIs (`resource://files/abc`, with `contentType`,
`sizeBytes`, and a name) that other tools resolve. The conversation carries the
reference, not the bytes. Handle expired or missing references with a clear error.

### One vocabulary across the set (Canonical Tool Model)

Define canonical shapes (`User`, `Task`, `Event`, `Page`) once and map every tool's
upstream response onto them. Same field names for the same concept everywhere
(`createdAt` in every tool, never `created`, `creationDate`, and `ts` in three tools).
Consistent shapes are what let one tool's output feed the next tool's input without a
transformation step in the agent's head.

## Anti-patterns

- Returning `response.json()` from the upstream API.
- An unbounded array with no `limit`, no cursor, and no count.
- `hasMore` omitted when false, so the agent cannot tell "done" from "unknown".
- A batch tool that throws on the first failure and discards the successes.
- Different tools naming the same field differently.
- Embedding a 200 KB document body in a result the agent only needed the title from.

For error shapes, retry classification, and step failure defaults, see
`tool-design-errors`.

## On Runtype

- Runtime tool results go to the model directly. An `external` tool returns the
  upstream body unchanged (its `body` template maps the request, not the response), so
  shape a noisy payload in a `flow` tool whose `api-call` step feeds a `transform-data`
  step. A `custom` code tool has no network egress unless it opts in with
  `networkAccess` (an `allowedHostnames` list is the safe form); without it, the tool can
  shape only what arrives in its parameters.
- A `flow` tool returns the value that the flow's final executed step wrote. Set
  `outputVariable` to return one named flow variable instead, such as the
  `transform-data` output, and `outputMapping` to select a dot path inside it. A
  `_`-prefixed variable is rejected, and a variable the flow never assigned fails the
  tool call. See [Flow tools](https://docs.runtype.com/developer-guides/guides/runtime-tools#flow-tools).
- If you run your own MCP server, apply these rules to its results. You cannot reshape
  a third-party MCP server's results, so prefer its narrower tools.
- `paginate-api` is the platform's pagination step for upstream lists (cursor, offset,
  page, or `Link` header).
- **Empty is not the same as failed.** A fetch-class step (`fetch-url`, `api-call`,
  `crawl`, `search`) with `errorHandling` unset swallows a failure into
  `defaultValue` (or an empty result) and reports success, so a downstream
  `transform-data` or `upsert-record` runs over zero rows as if the API returned
  nothing. `validate_flow` warns with `FETCH_CLASS_SWALLOWING_FEED`; set
  `errorHandling: { "onError": "fail" }` when an empty result must not look like a real
  one. Unlike these steps, `paginate-api` fails by default.
- `upsert-record` needs a JSON object as its source. `validate_flow` warns with
  `UPSERT_RECORD_SOURCE_NOT_JSON` when a text prompt feeds it, and the write fails at
  runtime. Set the prompt's `responseFormat` to `"json"`, shape the value in
  `transform-data`, or set `contentField` on the upsert step to wrap the string.
- Store large content in a record and return its id. The agent calls `get_record` to
  fetch it.
- Binary media over 4 KB in a tool result, such as a screenshot or a generated image,
  becomes a `runtype-asset://` handle automatically, so later turns carry the handle, not
  the bytes. Handles expire after 7 days. To accept one, declare the parameter with
  `contentEncoding: "base64"`, and Runtype substitutes the stored bytes before the call:

  ```json
  { "image": { "type": "string", "contentEncoding": "base64" } }
  ```

- The model receives each new tool result in full; Runtype does not truncate it for
  you. Older results outside the recent window (40,000 tokens by default) are masked:
  the model sees only a short "cleared" placeholder, not a trimmed copy. Write anything
  the agent needs in later turns to a record. See [Context compaction](https://docs.runtype.com/user-guide/agents/creating-and-configuring-agents#context-compaction).
- To verify a result shape, run the tool with `execute_tool` and read the raw result.
  After an agent run, the **Context window** bar in
  [Logs](https://docs.runtype.com/user-guide/logs/working-with-logs) shows the share of
  input tokens that tool results take, and hints when they dominate.
