---
name: tool-design-output
description: 'Design agent tool results, including pagination, partial success, context size, and actionable next steps.'
user-invocable: true
argument-hint: '[tool whose result shape to design]'
---

# Tool Output Design

Every byte a tool returns is paid for in context tokens and in the agent's attention. The
result is not a data dump; it is the next prompt the agent reads. Design it as one.

## Procedure

1. **List what the agent needs to decide its next step.** Only those fields are
   essential. Everything else is optional detail or a follow-up call.
2. **Define a flat, named shape** for the result and keep it identical across calls.
3. **Decide the size policy**: default summary, expansion flags, cursor pagination,
   truncation limits, and references for blobs.
4. **Add navigation**: `hasMore` and cursor, GUI URLs, and a next-action hint.
5. **Handle mixed outcomes** with per-item status for anything that touches more than
   one item.

## Rules with examples

### Shape the response (Response Shaper)

Never return the upstream payload as-is. Flatten nesting, select relevant fields, rename
cryptic keys, add computed fields, and convert machine encodings to readable ones
(ISO-8601 datetimes, not epoch seconds; `active: true`, not `status_code: 2`).

Before:

```json
{
  "data": {
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

Page numbers drift as data changes; cursors do not. Return:

```json
{
  "items": [],
  "count": 50,
  "hasMore": true,
  "nextCursor": "eyJvZmZzZXQiOjUwfQ",
  "nextAction": "Call list_contacts(cursor=\"eyJvZmZzZXQiOjUwfQ\") for more"
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
    { "id": "a", "ok": true },
    { "id": "b", "ok": true },
    { "id": "c", "ok": false, "error": "mailbox full", "retryable": true }
  ],
  "retryHint": "Retry with send_invites(emails=[\"c@example.com\"])"
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

## On Runtype

- Runtime tool results feed the model directly. An `external` tool returns the
  upstream body unchanged (its `body` template maps the request, not the response), so
  shape a noisy payload in a `flow` tool whose `api-call` step feeds a `transform-data`
  step, or in a downstream `transform-data` step. A `custom` code tool has no network
  egress: it shapes only what arrives in its parameters. The same rules apply to MCP
  tools surfaced through `discover_mcp_server_tools`.
- A `transform-data` step is the place to shape a third-party payload once instead of
  in every prompt; `paginate-api` is the platform's cursor-pagination step for
  upstream lists.
- **Empty is not the same as failed.** A fetch-class step (`fetch-url`, `api-call`,
  `crawl`, `search`) with `errorHandling` unset swallows a failure into
  `defaultValue` (or an empty result) and reports success, so a downstream
  `transform-data` or `upsert-record` runs over zero rows as if the API returned
  nothing. `validate_flow` warns with `FETCH_CLASS_SWALLOWING_FEED`; set
  `errorHandling: "fail"` when an empty result must not look like a real one.
- `upsert-record` needs a JSON object as its source (`responseFormat: "json"` on the
  producing prompt step, or a transform output); a string source is rejected as
  `UPSERT_RECORD_SOURCE_NOT_JSON`. Shape the result before it reaches a record.
- Large artifacts belong in records or artifacts, referenced by id, not in the message;
  `get_record` is the resolver for that reference.
- Persona renders the first assistant text block prominently, so a tool whose result
  is meant for display should return the final shape, not a preamble.
