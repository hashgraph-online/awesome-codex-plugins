---
name: tool-design-errors
description: 'Design actionable agent tool errors, ambiguity handling, retry guidance, and fallback behavior, or debug an agent that loops on or misreads a failing tool.'
user-invocable: true
argument-hint: '[tool whose failure paths to design]'
---

# Tool error design

An agent that receives only `429` either retries in a tight loop or gives up. An agent
that receives "Rate limited. Wait 30 seconds, or reduce `batchSize` to 50 and retry"
makes a better second call. Give every error a class, a reason, and the next call to
make. Design the failure paths with the same care as the success path.

## Procedure

1. **List every way the tool can fail**: bad input, missing prerequisite, not found,
   ambiguous match, upstream unavailable, rate limit, timeout, permission denied,
   missing scope, partial completion.
2. **Classify each failure** into exactly one class (below). The class tells the agent
   whether to retry, change the call, ask the user, or have the user re-authenticate.
3. **Write the recovery text** for each failure: what went wrong, why, and the exact
   next call.
4. **Decide the ambiguity policy** for any natural-identifier input: thresholds for
   auto-accept, confirm, and reject.
5. **Decide the degradation policy** for multi-source or multi-step tools: what the
   tool returns when part of the work fails.
6. **Test by reading the error cold**: could an agent with only the tool description
   and this error message make a better second call? If not, rewrite it.

## Rules with examples

The names in parentheses are the pattern names that the tool-design skills share.

All examples use one error envelope: `class`, `message`, `reason`, `recoverySteps`,
and, where they apply, `retryAfterSeconds`, `options`, or `suggestions`. Use the same
envelope in every tool in the set.

### Every error carries a class (Error Classification)

| Class          | Meaning                                 | Agent should                     |
| -------------- | --------------------------------------- | -------------------------------- |
| `retryable`    | Transient. Likely to succeed later      | Wait `retryAfterSeconds`, retry  |
| `permanent`    | Will not succeed without a changed call | Change parameters or tool        |
| `userInput`    | Needs a human decision                  | Ask the user                     |
| `authRequired` | Credential or scope missing or expired  | Ask the user to reconnect access |

Use the same class vocabulary in every tool in the set. Map upstream errors onto it
inside the tool, so the agent never sees vendor-specific codes. Retryable errors always
carry `retryAfterSeconds`.

### Every error guides recovery (Recovery Guide)

Use structure, not prose:

```json
{
  "class": "permanent",
  "message": "User not found",
  "reason": "No user matches \"jon smith\"",
  "recoverySteps": [
    "Call search_users(query=\"jon smith\") to list candidates",
    "Retry with the user's email address instead of a display name"
  ],
  "suggestions": [{ "id": "usr_1", "name": "Jon Smyth", "email": "jon@example.com" }]
}
```

Include concrete tool names and parameter values, not "check your input". Name
alternative tools when one exists. For a rate limit, say how long to wait and what size
to reduce.

### Ambiguity returns options, never a guess (Confirmation Request)

When a natural identifier matches more than one record, do not pick one. Return the
matches with enough detail to tell them apart (name, email, last activity), cap the
list at five to ten, and state the exact call to make for each option:

```json
{
  "class": "userInput",
  "message": "3 contacts match \"Alex\"",
  "reason": "The name \"Alex\" is not unique",
  "options": [
    { "contactId": "c_1", "name": "Alex Kim", "email": "alex.kim@example.com" },
    { "contactId": "c_2", "name": "Alex Reyes", "email": "areyes@example.com" }
  ],
  "recoverySteps": ["Call update_contact(contactId=...) with one of the ids above"]
}
```

Zero matches is a `permanent` error with suggestions, not an empty list that reads as
success.

### Thresholds decide when to ask (Fuzzy Match Threshold)

Confirming every match is slow. Never confirming is dangerous. Pick thresholds and
document them. A reasonable starting point:

- Above 90% confidence: auto-accept, and log the match for audit.
- 50% to 90%: return the candidates as a confirmation request.
- Below 50%: reject with a "try a different identifier" recovery step.

Expose the threshold as a parameter with a safe default when callers need to tune it.
Command tools with irreversible effects should set the auto-accept bar higher than
query tools.

### Return what worked (Graceful Degradation)

A tool that aggregates from several sources or performs several steps returns the parts
that succeeded, names the parts that failed, states completeness, and says how to get
the rest:

```json
{
  "completeness": "partial",
  "crm": { "...": "..." },
  "billing": null,
  "errors": [
    {
      "source": "billing",
      "class": "retryable",
      "reason": "Billing service unavailable (503)",
      "retryAfterSeconds": 60
    }
  ],
  "recoverySteps": ["Call get_unified_profile again in 60 seconds for billing data"]
}
```

A total failure that hides a successful partial result wastes the work already done and
the tokens already spent.

### Provide an alternative when the primary is down (Fallback Tool)

For critical capabilities, define a fallback order (`slack`, then `email`, then `sms`).
Either switch transparently and report `channelUsed` and `wasFallback: true`, or return
a `permanent` error that names the fallback tool to call. Never fall back silently to a
command whose side effects differ from the one requested.

### Timeouts are errors too

A timeout returns a `retryable` error that says what timed out, how long the limit is,
whether partial results are attached, and whether an async variant exists. See
`tool-design-execution` for the boundary itself.

## Anti-patterns

- Passing the upstream exception string or HTTP status through as the error.
- "Invalid input" with no field name and no valid values.
- Picking the first fuzzy match on a command tool.
- Throwing on the first failed item in a batch.
- A retryable error with no `retryAfterSeconds`, so the agent retries immediately.
- Success-shaped responses for failures (`{ "items": [] }` when the query was invalid).
- Recovery text written for the developer ("see logs") instead of the agent.

## On Runtype

### What the model receives

- **Runtype classifies every failed tool call.** The model receives
  `{ error, errorType }`, where `errorType` is one of `auth`, `rate_limited`,
  `upstream_4xx`, `upstream_5xx`, `timeout`, `invalid_args`, `not_configured`,
  `aborted`, or `unknown`. Runtype sets it from the HTTP status first, then from the
  error text. It does not tell the model whether to retry. Your classes add to
  `errorType`: return the matching status (429 with `retryable`, 401 or 403 with
  `authRequired`, 400 or 422 with `permanent`) and put your class and recovery steps
  in the error body.
- **For an `external` tool, shape the error in your own endpoint.** Return a non-2xx
  status and a compact JSON body. The model sees
  `External tool "TOOL_NAME" failed: HTTP STATUS — ` followed by the first 500
  characters of the body. Response headers such as `Retry-After` are
  dropped. Put `class`, `retryAfterSeconds`, and the first recovery step at the top of
  the body. A 2xx response that carries an error payload counts as a success and gets
  no `errorType`.
- **To classify a third-party API you do not control**, wrap the call in a `flow` tool.
  An `api-call` step with `errorHandling: "continue"` writes its `defaultValue` when
  the call fails, so set `defaultValue` to a structured error object, and add a
  `transform-data` step that gives success and failure one result shape. If the step
  has a `responseMapping`, the mapping also applies to `defaultValue`, so map the error
  fields too. The step cannot read the upstream status, so the fallback object carries
  one fixed class. A `custom` tool has no network egress unless it opts in with
  `networkAccess` (and `secrets` for credentials); then it can make the call and shape
  the failure class itself.
- **For an MCP server tool, put the class and recovery steps in the content text.**
  Runtype passes the `content` of a `tools/call` result to the model and does not read
  `isError`, so a result with `isError: true` is recorded as a successful call. A
  non-2xx HTTP response or a JSON-RPC error is still reported as a failed call.
- **`external` tool calls time out after 30 seconds**, and the model receives a
  `timeout` error. For slower upstreams, use a detached `subagent` tool (see
  `tool-design-execution`).

### Errors Runtype writes for you

Tell the agent, in its instructions, how to handle the errors that Runtype writes
itself:

- A tool call that the user denied at approval. It cannot be retried.
- A call interrupted mid-run on a resumed turn. Its effects are unknown, so the agent
  must check whether the write happened before it retries. Set `idempotent: true` on
  read-only runtime tools so that Runtype can safely run an interrupted call again.
  MCP tools follow the server's `readOnlyHint` and `idempotentHint` annotations.
- Missing secrets or an MCP server that is not configured (`not_configured`). The
  agent cannot fix these. It should tell the user what to set up.

For MCP servers that use OAuth2, Runtype refreshes an expired token and retries once
after a 401. Use `authRequired` only when the user must act. For an MCP server, have
the recovery step tell the user to reconnect the server from **Tools**.

### Confirmation requests on chat surfaces

Behind a Persona widget, expose the built-in local tools
(`features.askUserQuestion.expose`, `features.suggestReplies.expose`). An ambiguous
match then becomes a rendered choice that the user taps, not a JSON options list that
the model has to narrate. Elsewhere, return the options in the tool result as shown
above.

### Flow step defaults

Some flow steps continue when they fail. This partial list shows the behavior when
`errorHandling` is unset:

- `fetch-url`, `api-call`, `crawl`, `search`, and `transform-data` continue and write
  `defaultValue`.
- `paginate-api` fails the step.
- `upsert-record` reports `success: false` and writes no output when its source
  variable is missing or does not resolve to a JSON object. `update-record` does the
  same when it cannot find the target record. Both continue with `defaultValue` on
  other failures.
- A `tool-call` step ignores `errorHandling`. It uses `config.onError`, which fails the
  step by default. With `onError: "continue"`, it writes `{ error, result: null }`.

Set `errorHandling` to `"fail"` or `"continue"` explicitly on any step where a silent
continue would hide a real failure from the agent.

### Pauses and retries

- The platform's own pauses are not errors. An `await` event means the run is waiting
  on a person or the client: an approval, a client tool, an elicitation, or a detached
  run. Its `awaitReason` separates pauses that resume on their own from pauses that
  the client must resolve. A surface must render them as pauses, not as failures.
- The model retries failed tools, not the platform. `retryAfterSeconds` in the result
  is what stops a tight loop. Also set the agent's **Max turns** and **Cost budget
  (USD)** so that a tool that keeps failing cannot loop without limit.
- Test failure paths with `execute_tool` and deliberately wrong inputs before you
  attach the tool to an agent. Capture real failures as eval cases with
  `add_eval_case_from_execution` so that the fix stays pinned.

See also [Agent tools: Error handling](https://docs.runtype.com/user-guide/agents/agent-tools#error-handling),
[Runtime tools: Tool replay after an interrupted turn](https://docs.runtype.com/developer-guides/guides/runtime-tools#tool-replay-after-an-interrupted-turn),
and [Runtime tools: Pause and resume on an agent dispatch](https://docs.runtype.com/developer-guides/guides/runtime-tools#pause-and-resume-on-an-agent-dispatch).
