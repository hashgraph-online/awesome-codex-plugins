# LLM calls, streams and agent runs

Read this with [reserve-commit-release.md](reserve-commit-release.md) when the metered work is a language model call. It says what to settle in every way a call can end, where each provider reports usage in a stream, how to retry without charging twice, and how to bound a multi-step agent. Prices and the bound are in [ai-pricing.md](ai-pricing.md). Code is in [ai-worked-example.md](ai-worked-example.md).

## One call

```text
count prompt -> price the bound -> reserve -> call with the same limits -> settle in a finally block
```

- The server calls the provider and relays the stream to the browser. The browser never holds a provider key and never reports usage.
- The provider call runs outside any database transaction. Reserve commits first, the settle runs in its own transaction.
- The settle runs on every path out of the call: success, error, timeout, abort. It records the usage on the reservation first, then commits or releases.
- One user action is one reservation, keyed `<account id>:<idempotency key>`. Retries of that action reuse it.

## How a call can end, and what to settle

"Delivered" means any output the app used: text shown to the user, a tool call the app ran, a file it stored.

| Ending | Usage known | Settle |
| --- | --- | --- |
| Finished | Reported by the provider | Commit the reported cost, at most the bound |
| Stopped by the output limit | Reported | Commit it. The user asked for at most that much |
| Provider error before any output | Usually not | Release |
| Timeout before any output | No | Release. Abort the request so the provider stops |
| Provider error or dropped connection after output was delivered | Partly, or not at all | Commit the cost of what is known (below) |
| The user's connection closed during the stream | The server still holds the provider stream | Abort the provider request, then commit what was used |
| The process died | No | The sweeper settles it: commits a recorded cost, otherwise releases |

The release on failure is the default of this skill: nothing delivered, nothing charged. The provider may still bill the app for input or reasoning tokens of a call that produced nothing, for example a response stopped by its output limit while reasoning. That cost stays with the app. Count it per account, so that an account that causes many such calls is visible.

## Where usage arrives in a stream

- **OpenAI, Chat Completions.** Set `stream_options: { include_usage: true }`. An extra chunk before `data: [DONE]` carries `usage` for the whole request, with an empty `choices` array. Every other chunk has `usage: null`. The reference states that an interrupted stream may never deliver the usage chunk.
- **OpenAI, Responses API.** The terminal events `response.completed`, `response.incomplete` and `response.failed` each carry the response object, whose `usage` field holds the totals (it can be null). A synchronous response is cancelled by closing the connection. A response created with `background: true` can be cancelled with `POST /v1/responses/{id}/cancel`, read again with `GET /v1/responses/{id}`, and a dropped stream of it resumed from the last sequence number.
- **Anthropic, Messages API.** `message_start` carries the message with its `usage` (input tokens and cache fields). Each `message_delta` carries `usage` whose counts are cumulative. `output_tokens_details.thinking_tokens` appears only on the final `message_delta`. The stream ends with `message_stop`. An `error` event (such as `overloaded_error`) can arrive in the middle of a stream.
- **Google Gemini, Interactions API.** `interaction.completed` carries the final `usage`. A `step.stop` event may carry `usage`, the running total since the start of the interaction, and `step_usage` for that step. An `error` event can end the stream.
- **Google Gemini, `streamGenerateContent`.** The stream is a sequence of `GenerateContentResponse` objects, and the type has a `usageMetadata` field. The reference does not say which chunk carries the final counts: log a few real streams before relying on one.

Let the adapter for each provider emit the same three things: output deltas, a usage report marked as final or running, and the end of the stream. The settle code then has one shape for every provider.

## A stream that was cut

Order of preference for the usage to commit:

1. **The final report,** if it arrived before the cut.
2. **The provider's record of the call,** where the API keeps one that can be read afterwards (OpenAI background responses). A job reads it and settles, before the reservation expires, instead of the request.
3. **The last running report** (Anthropic's cumulative `message_delta`, Gemini's `step.stop` usage), with the output count raised to your own count of what was delivered if that is higher.
4. **Your own count:** the counted prompt at the `input` price, and the delivered output counted with the provider's count endpoint or a local tokenizer.

Always at most the bound. Mark the call as estimated, and keep the estimate when the real figure arrives later: a corrected charge after the fact confuses users more than a small difference. Reasoning tokens that were never shown cannot be counted by the app. With the default above they are not charged on a cut stream; if the owner prefers to charge the full bound for a cut stream of a reasoning model, write that rule down and show it to users.

## Retries without charging twice

- **The client retries** (a double click, a reconnect, a mobile app resending after a timeout). Same idempotency key, same reservation id: `reserve` returns "seen before", and the handler answers with the stored state of the first attempt (running, finished with its result, or failed). It never calls the model again.
- **The server retries the provider** after an error with nothing delivered (a rate limit, an overload, a 5xx). Retry inside the same reservation, after the same bound check, with a small number of attempts and backoff. Add up the reported usage of every attempt and commit the sum, capped at the bound. The cap means a long series of failed attempts costs the app, not the user.
- **Output was already delivered when the provider failed.** Do not retry silently: the user would see the answer twice. Either commit what was used and let the user continue as a new action with a new key, or send a continuation request inside the same reservation and commit both calls' usage, capped at the bound. Anthropic documents the continuation request for interrupted streams. Tool use and thinking blocks cannot be partly resumed.
- **A retry is never a new reservation for the same action.** A new key belongs to a new action the user chose to start.

## Multi-step agents and tool calls

An agent run makes several model calls, and the app runs tools between them. Two ways to meter it:

| Model | When | How |
| --- | --- | --- |
| One reservation per step | Short runs, chat with tool calls | Each model call is reserved, called and settled like a single call. The run stops at the first step whose reservation fails, and returns what it has |
| A budget per run | Long or autonomous runs | One reservation for the run's cap. Each step takes its bound from the budget under a condition and returns the unused part. The run commits the total used |

The budget per run is the default for agents: the user agrees to a maximum once ("this task may use up to 400 credits"), and the run cannot spend more than that, whatever the model decides to do.

```sql
-- One row per run, next to its reservation (same id). spent and held are credits.
CREATE TABLE agent_runs (
  id          TEXT PRIMARY KEY REFERENCES credit_reservations (id),
  cap         BIGINT NOT NULL CHECK (cap > 0),
  spent       BIGINT NOT NULL DEFAULT 0 CHECK (spent >= 0),
  held        BIGINT NOT NULL DEFAULT 0 CHECK (held >= 0),
  steps       INTEGER NOT NULL DEFAULT 0,
  max_steps   INTEGER NOT NULL,
  CHECK (spent + held <= cap)
);

-- Before a step: take its bound from the budget. 0 rows: the run is out of budget or steps.
UPDATE agent_runs SET held = held + $2, steps = steps + 1
 WHERE id = $1 AND spent + held + $2 <= cap AND steps < max_steps;

-- After the step, in the step's settle: $2 is the bound, $3 the step's cost, at most the bound.
UPDATE agent_runs SET held = held - $2, spent = spent + $3 WHERE id = $1;
```

- Parallel tool calls or parallel model calls inside one run each take their own bound with the first statement, so they cannot overspend the run together.
- The run's reservation is committed once, at the end, for `spent`. Because `spent` is stored after every step, a run whose process died is committed by the sweeper for `spent` instead of being released.
- Hard limits per run: the credit cap, `max_steps`, and a wall-clock timeout that is shorter than the reservation's lifetime.
- Provider-side tools billed per call count in the step's bound. Tools the app runs itself (a search API, a code sandbox) are metered work of their own: price them in the same step or as their own step.
- A run that stops for budget ends with a clear message and the partial result. It does not fail silently, and it does not reserve more on its own.

## Parallel requests from one user

- Each call and each run reserves before it starts, against `balance - reserved`. Ten tabs that start ten calls at once get as many reservations as the balance covers; the rest get 402.
- A run's cap blocks that many credits while it runs. Cap the number of open reservations and runs per account (count them inside the reserve transaction, after the account row is locked), and keep the default run cap modest.
- Free and trial accounts get a lower cap on parallel calls. Each of their credits is real provider cost to the app.

## Purchases, refunds, expiry and free credits

- **Top-ups** are granted from the payment provider's verified event, as in [credit-ledger.md](credit-ledger.md), section "Granting credits". The verification itself is the `build-webhook-endpoint` skill. An automatic top-up (charge the saved card when the balance runs low) is created by the server under one key per account and threshold crossing, and the credits arrive only with the verified payment event.
- **Refunds and chargebacks** of a pack take back its credits, also when they were spent on model calls: the balance goes below zero and calls are refused until it is topped up. The `handle-refunds-and-reversals` skill covers the payment side.
- **Expiry and the balance screen** follow [expiry-and-display.md](expiry-and-display.md), including the section on AI usage.
- **Free credits at sign-up** cost the app real provider spend per credit, which makes them worth farming with new accounts. Keep the grant small, hold it until the account is verified, and key it once per identity: the `guard-signups` skill builds that.

## Not a bug

- A cut stream is charged less than the same answer finished. The estimate is a floor.
- A failed call is free to the user and costs the app. That is the default rule; the count per account is how abuse shows.
- The balance drops by the bound while a call runs and partly comes back at the end. Show it as "in use", not as spent.
- An agent run stops before the task is done. The cap is the user's own limit.

## Sources

- https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create (`stream_options.include_usage`)
- https://developers.openai.com/api/reference/resources/responses/streaming-events (`response.completed`, `response.incomplete`, `response.failed`)
- https://developers.openai.com/api/docs/guides/background (cancel, poll, resume)
- https://developers.openai.com/api/reference/resources/responses/methods/cancel
- https://developers.openai.com/api/docs/guides/reasoning (incomplete responses)
- https://platform.claude.com/docs/en/build-with-claude/streaming (event flow, cumulative usage, error recovery)
- https://platform.claude.com/docs/en/build-with-claude/extended-thinking (thinking tokens on the final `message_delta`)
- https://ai.google.dev/gemini-api/docs/streaming (Interactions API events)
- https://ai.google.dev/api/generate-content/stream-generate-content
- https://ai.google.dev/gemini-api/docs/thinking (incomplete responses still bill thinking tokens)

Checked 2026-11-15.
