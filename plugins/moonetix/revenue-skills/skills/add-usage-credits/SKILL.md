---
name: add-usage-credits
description: Build prepaid usage credits for metered features such as AI generations, LLM calls, API calls or exports. Credits are granted from verified purchases and plan renewals, spent per unit of work at a server-side price, and reserved, committed and released for work whose cost is known only afterwards, with expiry and a balance the user can read. Covers AI credits priced from LLM token usage (input, cached, output and reasoning tokens) with a versioned price table, streamed responses from OpenAI, Anthropic and Google Gemini, and budgets for multi-step agent runs, with patterns for Next.js with Prisma, Express, Django, Laravel and Rails. Use when the user asks to add credits, tokens or a usage quota, sell AI credits, charge per generation, per LLM token or per API call, meter AI or agent usage, stop users from running work with an empty balance, or fix credits that are charged twice or not returned when a job or stream fails.
license: MIT
compatibility: The verification step needs Node 20 or newer to run the bundled probe script.
metadata:
  author: moonetix
  version: "1.3.5"
---

# Add usage credits

This skill produces a credit system for metered work: grants that arrive once per verified purchase or renewal, a debit per unit of work that parallel requests cannot overdraw, and a reservation for work whose cost is known only when it ends. It prevents four failures. Ten parallel jobs that all start on the last ten credits. A retried request that pays twice. A failed or abandoned job that keeps the credits. A client that names its own price.

## Before writing code

Read the project first, and ask the user only what the code cannot tell you.

- **Stack and database.** Language, framework, database engine, migration tool, test framework, job scheduler, and how the project opens a transaction.
- **Where the metered work runs.** Every handler, queue consumer and job that calls the paid model, API or renderer. Note whether any client calls a paid third-party API directly with a key it holds.
- **How the cost becomes known.** Fixed per call, or measured afterwards (tokens, seconds, rows, pages). For measured work, find the limit that bounds it and where the provider reports real usage. For model calls: which providers, APIs and models, whether responses are streamed, whether prompt caching, reasoning or provider-side tools are used, and whether agents make several calls per task.
- **Existing balance code.** A credits column, a quota counter, a ledger table. List every statement that writes it.
- **How purchases and plans arrive.** The payment provider's event handler, whether it verifies the event, and which event starts a paid period.
- **Idempotency today.** Whether clients send a key per action, and whether jobs have a stable id.

Then settle the decisions that belong to the user. Ask once, in one message, and offer the default.

| Decision | Default |
| --- | --- |
| Unit and price list | Whole credits. One server-side table of cost per feature, or rate per measured unit, rounded up once. |
| Who owns the credits | The user. The team or workspace when the plan is bought per team. |
| Purchased credits | Never expire. Expiry of paid credits is a legal question in some countries, so the owner decides. |
| Plan allowance | Granted by the verified renewal event, expires at the end of the paid period, no rollover. |
| Promotional credits | One grant per account per code, with an end date, spendable but never refundable as money. |
| Bound not affordable | Refuse with 402 and the amount needed. Do not shorten the work silently. |
| Work that fails | Nothing delivered: all credits back. Part delivered: charged for what was delivered. |
| Reservation lifetime | The hard timeout of the work plus 60 seconds. |
| Result that arrives after its reservation expired | Charged once at its real cost, and counted so that the lifetime can be fixed. |
| Refund of a pack that is already spent | The balance goes below zero, and work is refused until it is topped up. |
| Cost above the reserved bound | The user pays the bound. The overage is logged as a defect in the bound. |

## Build

Use the project's migration tool, database layer and conventions. Do not add a framework to make the patterns fit. The reserve and commit in Next.js with Prisma, Express, Django, Laravel and Rails are in [references/stacks.md](references/stacks.md).

1. **Create the schema.** Copy `assets/credits-schema.sql` into a migration and adapt names and key types. If the project already has a ledger in credits, for example one built with the `build-ledger` skill, keep it and add only the `reserved` column, the reservations table and, if credits expire, the grants table. If it has no ledger, the account and ledger tables in the asset are the minimum: a bare counter column cannot make a repeated grant harmless or explain a balance. See [references/credit-ledger.md](references/credit-ledger.md).

2. **Write or adapt the one function that changes a balance.** It inserts the ledger row under the unique (kind, reference) key and updates the cached balance only when a row was inserted. Its debit is one conditional statement on `balance - reserved`. Same reference, section "One function writes the balance".

3. **Put the price list on the server.** The request names a feature. The cost is read from the server's table, and any cost field in the request is ignored.

4. **Grant credits from verified events.** A pack is granted in the handler of the payment provider's verified event, keyed by the order id. A plan allowance is granted by the verified renewal event, keyed by subscription and period. A promotional grant is keyed by code and account. The `build-webhook-endpoint` skill covers the verification itself. Same reference, section "Granting credits".

5. **Charge work with a fixed cost.** Take the credits under `<account>:<idempotency key>`, do the work, and post the give-back entry under the same reference if the work fails. A repeated key returns the first attempt's state. Same reference, section "Spending when the cost is known up front".

6. **Reserve, commit and release work with a measured cost.** Reserve the price of the work's upper bound before it starts, commit the real cost when it ends, release when nothing was delivered. Pass the same limit to the work that was priced into the reservation. See [references/reserve-commit-release.md](references/reserve-commit-release.md).

   **If the work is a language model call,** price it from a versioned price table loaded from the provider's price page, map each provider's usage onto it, and reserve the price of the request's own limits: [references/ai-pricing.md](references/ai-pricing.md). What to settle when a call fails, times out, is cut mid-stream or is retried, where each provider reports usage in a stream, and budgets for agent runs: [references/ai-calls-and-streams.md](references/ai-calls-and-streams.md). Runnable TypeScript and Python: [references/ai-worked-example.md](references/ai-worked-example.md).

7. **Schedule the sweeper** that releases reservations past their lifetime, and enforce the same timeout on the work itself. Same reference, section "Stale reservations".

8. **Add expiry if the decisions call for it.** One grant row per positive entry, consumed soonest expiry first, and a job that posts an `expiry` entry for what is left. See [references/expiry-and-display.md](references/expiry-and-display.md).

9. **Expose the balance and the history.** One endpoint returns available credits, credits in use, upcoming expiry and the allowance. Refusals are HTTP 402 with a machine-readable body. History is read from the ledger. Same reference, sections "What to show the user" and "Entitlement is decided on the server".

10. **Schedule the two reconcile queries** from [references/credit-ledger.md](references/credit-ledger.md) and send a failure to a person.

## Rules that must hold

- Every change to a credit balance is one ledger row and one balance update in the same transaction, written by one function.
- The ledger has a unique constraint on (kind, reference) in the schema. The balance update runs only when the insert reported a new row.
- A grant's reference comes from the event that justifies it: order id, subscription and period, code and account. Never a random value.
- Credits are granted only by server code acting on a verified event. No client request, redirect or "success" page grants.
- The cost of work comes from the server's price list. No cost, credit amount, plan or account id is taken from the request body.
- A debit and a reservation are each one conditional statement on `balance - reserved`, and the code checks the number of rows changed.
- Credits are taken or reserved before the work starts. No path runs metered work first and charges later.
- A request that can be retried carries an idempotency key, scoped to the account, and is charged once.
- A reservation is settled once: committed or released by a guarded status change. A commit never charges more than was reserved.
- Every reservation has an expiry, the work has a timeout below it, and a scheduled job releases what is stale.
- `reserved` equals the sum of open reservations, and `balance` equals the sum of ledger entries. Both checks are scheduled.
- Only reversal paths (a refund, a chargeback, a commit of delivered work) may take a balance below zero.
- A model call is priced from the provider's reported usage with the price version stored on its reservation, reasoning tokens as output, rounded up once. A cut stream is charged for what was delivered, at most the bound.
- The metered work runs on the server. The balance shown in the client is a display, not a control.

## Verify

Write these tests in the project's own test framework, against a real database of the kind the project uses:

- The same purchase event delivered twice grants once. The same renewal event grants once, and the next period grants again.
- Ten parallel spends with different keys against a balance that covers three: three succeed, seven get 402, the balance ends at zero, and three `usage` rows exist.
- The same idempotency key five times in parallel: one charge, the work runs once.
- Work with a fixed cost that throws: the credits are back, once.
- Reserve 50 of 100 and commit 30: balance 70, reserved 0, one `usage` entry of -30.
- Two reservations of 60 against 100, started together: exactly one succeeds.
- Commit twice, release twice, commit after release with cost zero: the second call changes nothing.
- A reservation past its expiry is released by the sweeper. A commit that arrives later charges once.
- A cost field in the request does not change what is charged.
- If credits expire: the soonest expiry is consumed first, the expiry job removes only what is due and only once, and reserved credits are not expired.
- For model calls, the tests listed at the end of [references/ai-worked-example.md](references/ai-worked-example.md): a cut stream, a user who disconnects, a price change during a call, and ten parallel calls against a balance that covers two bounds.
- After every test, both reconcile queries return no rows.

Then run the app locally with test configuration and probe it. Describe each request in a JSON file as `scripts/probe.mjs` expects (run it without arguments for the format). `credits.json` reads the test account's credits endpoint with `"path": "available"`.

`scripts/probe.mjs` is the copy in this skill's folder. Run the commands below from the project directory, so that the request files resolve against the project. Their first line sets `PROBE` to that copy: replace `<skill directory>` with the folder this `SKILL.md` was read from, such as `.agents/skills/add-usage-credits`.

```bash
PROBE=<skill directory>/scripts/probe.mjs
# A retried request: the same idempotency key, in sequence and at the same moment.
node "$PROBE" replay generate.json --times 3 --observe credits.json
node "$PROBE" race generate.json --parallel 10 --observe credits.json

# The client names its own price.
node "$PROBE" send export.json --set-body cost=0 --set-body credits=0 --observe credits.json

# The purchase event, delivered twice.
node "$PROBE" replay purchase-event.json --times 2 --observe credits.json

# An account with fewer credits than the bound.
node "$PROBE" send generate.json --set-header "authorization=Bearer $EMPTY_ACCOUNT_TOKEN" --observe credits.json
```

Expected:

- `replay` and `race` on the generation: every request answers 2xx or "still running", available credits fall by the cost of one generation, and the work ran once.
- The request with its own price: charged the server's price.
- The purchase event: both deliveries answer 2xx, and available credits rise by one pack.
- The empty account: 402 with the amount needed, no work started, no reservation left behind.

The probe repeats one request, so with a key in it the probe proves retry safety. The overdraw race needs different keys and is covered by the tests above. If an endpoint accepts requests without a key, also race it with `--drop-header idempotency-key`: no more requests succeed than the balance covers.

Done when:

- the tests pass in the project's test run,
- the probes give the expected results three times in a row,
- a search for writes to the balance column finds only the posting function, plus the `reserved` updates in reserve, commit and release,
- the sweeper, the expiry job if there is one, and the reconcile queries are scheduled, and their failures reach a person.

## Out of scope / do not

- This skill does not verify payment events, take payments or process refunds as such. Those are the `build-webhook-endpoint` and `handle-refunds-and-reversals` skills. It is not a subscription billing system and not postpaid, invoice-based metering: the plan, its access, its renewals and when its allowance is granted are the `add-subscriptions` skill. Keeping free sign-up credits from being farmed with new accounts is the `guard-signups` skill.
- Do not run the work and charge afterwards without a reservation. Parallel jobs all pass a balance check that none of them has lowered yet.
- Do not charge an estimate up front and call it final, and do not bill more than was reserved.
- Do not hold a database transaction open across the model or API call. Reserve, commit the transaction, work, then settle in a second transaction.
- Do not settle in a path that depends on the client: a commit that runs when the browser reads the last chunk never runs for a closed tab.
- Do not release a reservation when part of the result was already delivered. Commit what was used.
- Do not keep the balance in a cache, a token claim or local storage as a second source of truth.
- Do not grant an allowance from a calendar job alone when the plan is paid. A failed renewal must not refill.
- Do not rate-limit as a replacement for the conditional debit. A rate limit slows abuse down, it does not make the arithmetic right.
