---
name: tool-design-errors
description: 'Design actionable agent tool errors, ambiguity handling, retry guidance, and fallback behavior.'
user-invocable: true
argument-hint: '[tool whose failure paths to design]'
---

# Tool Error Design

Raw error codes mean nothing to a language model. An agent that receives `429` either
retries in a tight loop or gives up; an agent that receives "Rate limited. Wait 30
seconds, or reduce `batchSize` to 50 and retry" does the right thing. Errors are the
tool's chance to teach. Design them with the same care as the success path.

## Procedure

1. **Enumerate every way the tool can fail**: bad input, missing prerequisite, not
   found, ambiguous match, upstream unavailable, rate limit, timeout, permission
   denied, missing scope, partial completion.
2. **Classify each one** into exactly one class (below). The class tells the agent
   whether to retry, change the call, ask the user, or re-authenticate.
3. **Write the recovery text** for each: what went wrong, why, and the exact next call.
4. **Decide the ambiguity policy** for any natural-identifier input: thresholds for
   auto-accept, confirm, and reject.
5. **Decide the degradation policy** for multi-source or multi-step tools: what is
   returned when part of the work fails.
6. **Test by reading the error cold**: could an agent with only the tool description
   and this error message make a better second call? If not, rewrite.

## Rules with examples

### Every error carries a class (Error Classification)

| Class          | Meaning                                 | Agent should              |
| -------------- | --------------------------------------- | ------------------------- |
| `retryable`    | Transient; likely to succeed later      | Wait `retryAfter`, retry  |
| `permanent`    | Will not succeed without a changed call | Change parameters or tool |
| `userInput`    | Needs a human decision                  | Ask the user              |
| `authRequired` | Credential or scope missing or expired  | Trigger re-auth           |

Use the same class vocabulary in every tool in the set. Map upstream errors onto it
inside the tool; the agent never sees vendor-specific codes. Retryable errors always
carry `retryAfterSeconds`.

### Every error guides recovery (Recovery Guide)

Structure, not prose:

```json
{
  "error": "User not found",
  "class": "permanent",
  "reason": "No user matches \"jon smith\"",
  "recoverySteps": [
    "Call search_users(query=\"jon smith\") to list candidates",
    "Retry with the user's email address instead of a display name"
  ],
  "suggestions": [{ "id": "usr_1", "name": "Jon Smyth", "email": "jon@example.com" }]
}
```

Include concrete tool names and parameter values, not "check your input". Name
alternative tools when one exists. For a rate limit, say the wait and the size to reduce.

### Ambiguity returns options, never a guess (Confirmation Request)

When a natural identifier matches more than one record, do not pick one. Return the
matches with enough detail to distinguish them (name, email, last activity), cap the
list at five to ten, and state the exact call to make for each option:

```json
{
  "class": "userInput",
  "message": "3 contacts match \"Alex\"",
  "options": [
    { "contactId": "c_1", "name": "Alex Kim", "email": "alex.kim@example.com" },
    { "contactId": "c_2", "name": "Alex Reyes", "email": "areyes@example.com" }
  ],
  "instruction": "Call update_contact(contactId=...) with one of the ids above"
}
```

Zero matches is a `permanent` error with suggestions, not an empty list that reads as
success.

### Thresholds decide when to ask (Fuzzy Match Threshold)

Always confirming is slow; never confirming is dangerous. Pick and document thresholds:

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
  "errors": [{ "source": "billing", "class": "retryable", "reason": "upstream 503" }],
  "retryHint": "Call get_unified_profile again in 60 seconds for billing data"
}
```

Total failure that hides a successful partial result wastes the work already done and
the tokens already spent.

### Provide an alternative when the primary is down (Fallback Tool)

For critical capabilities, define a fallback order (`slack` then `email` then `sms`),
either switch transparently and report `channelUsed` and `wasFallback: true`, or return
a `permanent` error that names the fallback tool to call. Never fall back silently on a
command with different side effects than the one requested.

### Timeouts are errors too

A timeout returns a `retryable` error that says what timed out, how long the limit is,
whether partial results are attached, and whether an async variant exists. See
`tool-design-execution` for the boundary itself.

## Anti-patterns

- Passing the upstream exception string or HTTP status through as the error.
- "Invalid input" with no field name and no valid values.
- Picking the first fuzzy match on a command tool.
- Throwing on the first failed item in a batch.
- A retryable error with no `retryAfter`, so the agent retries immediately.
- Success-shaped responses for failures (`{ "items": [] }` when the query was invalid).
- Recovery text written for the developer ("see logs") rather than the agent.

## On Runtype

- An `external` tool's upstream error body is what the model sees unless the tool
  shapes it; map upstream status codes to the four classes in a `custom` tool or in a
  `transform-data` step that follows it.
- **Confirmation requests have a native carrier on chat surfaces.** Behind a Persona
  widget, expose the built-in local tools (`features.askUserQuestion.expose`,
  `features.suggestReplies.expose`) so an ambiguous match becomes a rendered choice
  the user taps, rather than a JSON options blob the model has to narrate. Elsewhere,
  return the options in the tool result as above.
- **Know which steps swallow and which fail** when `errorHandling` is unset:
  `fetch-url`, `api-call`, `crawl`, and `search` continue with `defaultValue`;
  `paginate-api` fails; `upsert-record` and `update-record` report `success: false`
  and write no output when their input contract is not met (missing source, no
  resolvable target), while operation failures still swallow. Set `errorHandling` to
  `"fail"` or `"continue"` explicitly on any step whose swallow would hide a real
  failure from the agent.
- The platform's own pauses are not errors: `await` frames mean "waiting on a human
  or the client" (approval, client tool, elicitation, detached run), and an agent
  surface must render them as such rather than as failures.
- Retryable errors from tools are retried by the model, not the platform, so
  `retryAfterSeconds` in the result is what stops a tight loop.
- Test failure paths with `execute_tool` using deliberately wrong inputs before wiring
  the tool into an agent, and capture real failures as eval cases with
  `add_eval_case_from_execution` so the fix is pinned.
