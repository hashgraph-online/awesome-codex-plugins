---
name: build-webhook-endpoint
description: Build an endpoint that receives signed server-to-server events, such as payment webhooks, app store server notifications and affiliate or offerwall postbacks. It verifies the signature over the raw body, or the hash over named query parameters, refuses replays, compares amount and currency with the app's own order, and applies each event exactly once before it answers 2xx. Includes checked notes for Stripe, Paddle, Lemon Squeezy, PayPal, RevenueCat, App Store Server Notifications V2 and Google Play real-time developer notifications, and route patterns for Next.js, Express, Django, Laravel and Rails. Use when the user asks to add or fix a webhook handler or a postback URL, verify a webhook signature (Stripe-Signature, Paddle-Signature, X-Signature, PayPal transmission headers, a signed JWS or a Pub/Sub token), stop forged or duplicate credits, handle provider retries and out-of-order events, or rotate a webhook secret.
license: MIT
compatibility: The verification step needs Node 20 or newer to run the bundled probe script.
metadata:
  author: moonetix
  version: "1.3.6"
---

# Build a webhook endpoint

This skill produces the endpoint through which another company's server tells the app that money moved: a payment succeeded, a subscription renewed, a user completed an offer. It prevents three failures. A message nobody verified credits an account because it said so. A genuine message credits twice because it was delivered twice. A genuine message credits the wrong thing because the handler believed its content instead of the app's own records.

**Which of the three skills.** Use this one for payment webhooks and app store notifications, and for any other signed event that grants something. For a whole offerwall (the wall link, the postback, its reversals and the hold), use `add-offerwall`, which builds its postback by the same rules. To take credits back on refunds, chargebacks and reversed conversions, use `handle-refunds-and-reversals` after this one. For the access a subscription gives through renewals, failed payments and cancellations, use `add-subscriptions` on top of this endpoint.

## Before writing code

Read the project first, and ask the user only what the code cannot tell you.

- **Stack.** Language, framework, database, migration tool, test framework. How a route gets the request body, and whether a global body parser runs before every route.
- **Existing handlers.** Every route another company's server calls, and every page a provider redirects the user back to. For each: what it verifies, what it stores, what it credits.
- **The provider's scheme.** Read the provider's current documentation for the signature scheme, the event types, the retry schedule and the time it waits for an answer. Do not write a scheme from memory. If the project already uses the provider's official library, find its verification helper. For the providers in the table below, start from the reference, then confirm against the pages it lists.
- **What the event refers to.** The app's order, purchase or user record that an event names, where it is created, and whether it is committed before the user is sent to the provider.
- **The balance.** Whether the project has a ledger posting function, as the `build-ledger` skill builds it, or changes a balance column directly.
- **Proxies.** What sits in front of the app and whether it rewrites bodies or headers.

Provider references, checked against the providers' documentation on 2026-11-15:

| Provider | Authentication | Deduplicate on | Reference |
| --- | --- | --- | --- |
| Stripe | `Stripe-Signature`: HMAC-SHA256 of `t.body`, 5 minute library tolerance | `event.id` | [references/provider-stripe.md](references/provider-stripe.md) |
| Paddle Billing | `Paddle-Signature`: HMAC-SHA256 of `ts:body`, 5 second SDK tolerance | `event_id` | [references/provider-paddle.md](references/provider-paddle.md) |
| Lemon Squeezy | `X-Signature`: HMAC-SHA256 of the body, no timestamp | No event id: a business key | [references/provider-lemonsqueezy.md](references/provider-lemonsqueezy.md) |
| PayPal | Certificate signature over id, time, webhook id and CRC32, or the verify API | Event `id` | [references/provider-paypal.md](references/provider-paypal.md) |
| RevenueCat | `Authorization` value, optional HMAC header | `event.id` | [references/provider-revenuecat.md](references/provider-revenuecat.md) |
| App Store Server Notifications V2 | Signed JWS with an Apple certificate chain | `notificationUUID` | [references/provider-apple-app-store.md](references/provider-apple-app-store.md) |
| Google Play RTDN | Pub/Sub push OIDC token; purchase read from the Play API | `messageId` and the purchase token | [references/provider-google-play.md](references/provider-google-play.md) |

Then settle the decisions that belong to the user. Ask once, in one message, and offer the default.

| Decision | Default |
| --- | --- |
| Which event grants value | Only the type the provider documents as settled money. Every other type is acknowledged and ignored. |
| Timestamp tolerance | 300 seconds, for schemes that sign a timestamp. |
| A genuine event whose content does not match (wrong amount, unknown order) | Stored as rejected, a person is alerted, the provider gets 2xx. The alternative is a 4xx that shows as failed at the provider. |
| Payment for an order that expired | Honored: the money arrived. Refund instead when the goods are gone. |
| Inline or queued | Inline, in one transaction. Queued only when the work cannot finish within the provider's timeout. |
| Payload retention | The verified raw body is kept for 30 days. Event ids are kept as long as the secret is valid. |
| Cap per postback | A largest plausible reward per event. Anything above is held for a person. |
| Rotation overlap | Old and new secret both accepted for 24 hours. |
| Where alerts go | The channel the team already watches for production errors. |

## Build

Use the project's router, database layer, migration tool and conventions. Do not add a framework to make the patterns fit.

1. **Give the route the raw body.** Register the route so that it receives the bytes as they arrived, with a size limit, before any body parser, and exempt this route alone from CSRF protection. The table of frameworks is in [references/verify-signatures.md](references/verify-signatures.md). The whole route in Next.js, Express, Django, Laravel and Rails is in [references/webhook-stacks.md](references/webhook-stacks.md).

2. **Load the secret at start-up.** Required, with a minimum length, no default, read as a list so that two can be valid during a rotation. The app does not start without it. Same reference, sections "Secrets" and "Rotation".

3. **Verify before anything else.** The provider's own helper when the project has its library, otherwise the documented scheme: an HMAC over the raw body, a timestamp inside the signed text checked against the tolerance, a constant-time comparison. No branch skips it. Patterns for a timestamped header and for a plain body HMAC are in [references/verify-signatures.md](references/verify-signatures.md). For a postback signed by a hash over query parameters, follow [references/signed-postbacks.md](references/signed-postbacks.md): verify over the strings as received, and act only on values the hash covers.

4. **Create the event store.** Copy `assets/webhook-events.postgres.sql` into a migration and adapt it to the project's database; the header of the file lists the differences. The unique key is (provider, event id).

5. **Process inside one transaction.** Insert the event id, stop when it was there, run the content checks, change state with a conditional update, post the ledger entry, commit. The pattern and the reason for each line are in [references/process-events-once.md](references/process-events-once.md). Grant what the app's own order says, never what the event says.

6. **Check the content.** The event type means settled money. The order exists and is the app's own. Amount and currency equal the order's. Test events are refused in production. Checks run before the first write. Same reference, section "Content checks".

7. **Make state changes conditional and order-proof.** Every move names the states it may start from. Objects with only a current state keep the provider's event time and apply newer events only, or are fetched from the provider's API. Same reference, section "Out of order".

8. **Route reversing events.** Refunds, disputes and reversal statuses go to the project's reversal code. If there is none, store them unapplied and tell the user that the `handle-refunds-and-reversals` skill covers them. Never answer 2xx and drop them.

9. **Answer after the commit.** 2xx for applied, duplicate, ignored and rejected-and-stored. 400 for a failed signature. 5xx when the transaction failed, so the provider retries. The table is in [references/process-events-once.md](references/process-events-once.md).

10. **If there is no ledger,** use the minimum from the same reference: the conditional status change or a unique key on the transaction id, in the same transaction as the balance update. Tell the user what a ledger would add.

11. **Remove what the endpoint replaces.** A return page that marks an order paid because the browser arrived there, a debug parameter, an old unsigned route. The return page may show "processing" and read the order's status.

12. **Write down the rotation steps** where the project keeps its runbooks, with the name of the environment variable and the order of the steps from [references/verify-signatures.md](references/verify-signatures.md).

## Rules that must hold

A reviewer should be able to check each of these against the diff.

- Verification runs on every request to the route, before parsing and before any database work. No header, parameter or environment value that a caller can influence skips it.
- The signature is computed over the raw bytes of the body, not over a parsed and re-serialized object.
- The secret has no default and no fallback. The process fails at start-up without it. It appears in no log line, error message or client bundle.
- Signatures are compared with a constant-time function.
- A timestamped signature outside the tolerance is refused, in the past and in the future.
- The event id is stored under a unique constraint in the schema, in the same transaction as the effect. No `SELECT` decides whether an event is new.
- Every value the handler acts on is covered by the signature or the hash, or comes from the app's own records.
- The amount and currency of the event are compared with the app's order before anything is granted. The grant is read from the order.
- Every state change is a conditional update, and the code checks how many rows changed.
- The response is sent after the commit. A failure before the commit leaves no event row and answers 5xx.
- A duplicate is answered with 2xx.
- No external call, mail or slow job runs inside the transaction.
- Reversing events are applied or stored, never acknowledged and dropped.

## Verify

Write these tests in the project's own test framework, against a real database of the kind the project uses:

- A correctly signed event is accepted. A missing header, a wrong secret, a body changed by one byte, and a timestamp older or newer than the tolerance are each refused, and none of them writes a row.
- The app refuses to start without the secret.
- With two secrets configured, an event signed by either is accepted. With the old one removed, its events are refused.
- The same event twice in sequence, and ten times at once: one effect, every answer 2xx.
- Two events with different ids for the same order: one effect.
- A correctly signed event whose amount or currency differs from the order grants nothing and leaves the order pending.
- An event type the app does not handle is answered 2xx and changes nothing.
- A failure in the middle of the handler leaves no event row and no state change, and the same event sent again is applied.
- Events delivered in the wrong order end in the same state as in the right order.
- For a postback: a changed parameter with the old hash, a missing hash, and a parameter sent as an array are refused. The same transaction id credits once.

Then run the app locally with test configuration and probe it. Copy `assets/sign-test-event.mjs` into the project's test tools. Its `stripe`, `paddle`, `lemonsqueezy` and `revenuecat` modes sign events the way those providers do; otherwise replace the `webhook` and `postback` example formulas with the scheme the endpoint verifies. PayPal, App Store and Google Play events are signed with the provider's private key and cannot be produced locally: use the provider's test send from its reference, and test the handler with the verification stubbed. It prints a request file for `scripts/probe.mjs` (run the probe without arguments for the format). `me.json` reads the balance of the test user who owns the order.

`scripts/probe.mjs` is the copy in this skill's folder. Run the commands below from the project directory, so that the request files resolve against the project. Their first line sets `PROBE` to that copy: replace `<skill directory>` with the folder this `SKILL.md` was read from, such as `.agents/skills/build-webhook-endpoint`.

```bash
PROBE=<skill directory>/scripts/probe.mjs
export WEBHOOK_TEST_SECRET=whsec_test_not_secret POSTBACK_TEST_KEY=test_postback_key_not_secret
node sign-test-event.mjs webhook payment.succeeded '{"order_id":"<pending order>","amount_cents":499,"currency":"usd"}' > paid.json
node sign-test-event.mjs webhook payment.succeeded '{"order_id":"<pending order>","amount_cents":499,"currency":"usd"}' 600 > stale.json
node sign-test-event.mjs webhook payment.succeeded '{"order_id":"<second pending order>","amount_cents":1,"currency":"usd"}' > underpaid.json
node sign-test-event.mjs postback user_id=<test user> tx=tx-1001 reward=200 status=1 > postback.json

# Before the order is paid, so that a credit would show.
node "$PROBE" send paid.json --drop-header x-signature --observe me.json
node "$PROBE" send paid.json --set-body data.amount_cents=1 --observe me.json
node "$PROBE" send stale.json --observe me.json
node "$PROBE" send underpaid.json --observe me.json

# The genuine event, ten times at once, then twice more.
node "$PROBE" race paid.json --parallel 10 --observe me.json
node "$PROBE" replay paid.json --times 2 --observe me.json

# The postback.
node "$PROBE" send postback.json --drop-query hash --observe me.json
node "$PROBE" send postback.json --set-query reward=99999 --observe me.json
node "$PROBE" race postback.json --parallel 10 --observe me.json
```

With a provider mode, the same probes apply to the provider's event shape. A Paddle event must be sent within five seconds of signing, because that is the SDK tolerance; `EVENT_ID=<id>` signs the same event again with a fresh timestamp.

```bash
node sign-test-event.mjs stripe checkout.session.completed '{"id":"cs_test_1","client_reference_id":"<pending order>","payment_status":"paid","amount_total":499,"currency":"usd"}' > paid.json
node sign-test-event.mjs paddle transaction.completed '{"id":"txn_test_1","status":"completed","custom_data":{"order_id":"<pending order>"},"currency_code":"USD","details":{"totals":{"grand_total":"499"}}}' > paid.json
```

Expected:

- No signature, a changed body with the old signature, and the stale event: each answers 4xx, and the balance does not move.
- The underpaid event: the balance does not move and the second order is still pending. The answer is 2xx with the default decision, and the event is stored as rejected.
- `race` on the genuine event: all ten answer 2xx, and the balance rises by the credits of one order. The `replay` after it: both answer 2xx, and the balance does not move.
- The postback without a hash and with a changed reward: each answers 4xx, and the balance does not move. `race`: every request gets the success answer, and the balance rises by 200.

Done when:

- the tests pass in the project's test run,
- the probes give the expected results three times in a row,
- a search of the route's code finds no path from the request to a write that does not pass verification,
- the secret is absent from the repository, and the app fails to start without it,
- the rotation steps are written down where the team keeps its runbooks.

## Out of scope / do not

- This skill does not build the ledger, reverse refunds or pay out. Those are the `build-ledger`, `handle-refunds-and-reversals` and `add-payouts` skills.
- The provider references record what the documentation said on the date they carry. The provider's current documentation decides the scheme, the event names and the fields.
- Do not verify `JSON.stringify(req.body)`. It fails on genuine events, and the usual next step is to switch verification off.
- Do not make verification depend on the header being present, on a debug flag or on the environment name sent by the caller.
- Do not mark an order paid on the return URL. The browser controls that request.
- Do not deduplicate on a timestamp, an amount or a user id, and do not keep seen ids in a cache that expires or in process memory.
- Do not check for the event id with a `SELECT` and insert afterwards. Insert, and let the unique key decide.
- Do not answer 2xx first and do the work afterwards in the same process. A restart loses the event.
- Do not answer a duplicate with an error. The provider will retry it for days.
- Do not trust a sender address as the only check, and never read it from a forwarding header unless the peer is a proxy the app trusts.
- Do not send probes or test events to a provider's live API or to an environment shared with others.
