---
name: add-subscriptions
description: Build subscription access that follows the provider's state, not the client. Entitlements are derived on the server from the subscription the provider reports, through the whole life cycle (trial, active, past due with retries and grace, cancel at period end or now, pause, resume, upgrade, downgrade, refund, chargeback, revocation), with events handled once and in any order, one entitlement per subscription, credits per paid period granted once, one trial per person, and a reconciliation job against the provider. Covers Stripe Billing, the App Store Server Notifications V2 and Server API, Google Play RTDN and subscriptionsv2, Paddle Billing and RevenueCat, with patterns for Next.js, Express, Django, Laravel and Rails. Use when the user asks to add a subscription, a paid plan, a premium tier or a membership, gate features behind a plan, handle renewals, failed payments, grace periods or cancellations, or fix users who keep access after canceling, lose it after paying, or get monthly credits twice.
license: MIT
compatibility: The verification step needs Node 20 or newer to run the bundled probe and test event scripts.
metadata:
  author: moonetix
  version: "1.3.6"
---

# Add subscriptions

This skill produces subscription access that holds under real provider traffic: a row per subscription that mirrors what the provider says, an access check that reads it on the server at the moment of use, and handlers that end in the right state whatever order the events arrive in. It prevents five failures. A user keeps access after canceling, after a refund or after the card stopped working. A user who paid loses access because an old event arrived last. One payment grants two months of credits. A client or a return page grants a plan. A lost webhook leaves the app wrong for good.

**Which skill.** Use this one for recurring plans and the access and credits they give. The signature check on the provider's events is the `build-webhook-endpoint` skill. Taking back credits or other rewards that a refunded or charged-back payment granted is `handle-refunds-and-reversals`. Spending the credits a plan includes is `add-usage-credits`. Keeping trials and sign-up bonuses from being farmed with new accounts is `guard-signups`.

## Before writing code

Read the project first, and ask the user only what the code cannot tell you.

- **Stack.** Language, framework, database, migration tool, test framework, job scheduler, how a transaction is opened.
- **The provider.** Stripe Billing, the App Store, Google Play, Paddle, RevenueCat, or several. Read the provider's current documentation for its statuses, events and the API call that returns the current state. For the five below, start from the reference, then confirm against the pages it lists.
- **The events today.** The webhook route, what it verifies, which subscription events it handles, and which it acknowledges and drops.
- **How a subscription finds its user.** The record the app writes before sending the user to the provider (a checkout row, an `appAccountToken`, an obfuscated account id, custom data), and whether events are matched by it or by an email.
- **Every access check.** Each route, job and screen that asks "is this user on the plan": a column, a session value, a token claim, a client flag. List them all; step 5 replaces them with one function.
- **What the plan gives.** Features, seats, credits per period. Whether there is a ledger with a unique (kind, ref) key, as the `build-ledger` and `add-usage-credits` skills build it.
- **Trials and offers.** Who decides eligibility (the store or the app) and what a trial gives.

| Provider | Current state from | Order of events | Reference |
| --- | --- | --- | --- |
| Stripe Billing | Retrieve the subscription; periods are on its items | Not guaranteed; do not order by `created` | [references/provider-stripe-billing.md](references/provider-stripe-billing.md) |
| App Store | Get All Subscription Statuses | Most recent `signedDate` wins | [references/provider-app-store.md](references/provider-app-store.md) |
| Google Play | `purchases.subscriptionsv2.get`, called for every notification | Not documented | [references/provider-google-play.md](references/provider-google-play.md) |
| Paddle Billing | Get the subscription, or compare `occurred_at` | Not guaranteed; store and compare `occurred_at` | [references/provider-paddle-billing.md](references/provider-paddle-billing.md) |
| RevenueCat | Its customer endpoint, after every webhook | Not documented | [references/provider-revenuecat.md](references/provider-revenuecat.md) |

Then settle the decisions that belong to the user. Ask once, in one message, and offer the default.

| Decision | Default |
| --- | --- |
| Which statuses give access | Active and trialing until the paid period ends; past due until the grace end; nothing else, including unknown statuses. |
| Grace after a failed renewal | The store's own grace period where there is one (App Store, Google Play). Otherwise 3 days after the end of the last paid period. |
| Cancel | Access until the end of the paid period. Cancel now ends it at once, with no automatic refund. |
| Refund of a subscription payment | Access ends at once. The credits of that period go back through the reversal code. |
| Chargeback | Access ends at once, and the account is marked for review. |
| Pause | No access while paused. |
| Upgrade | The new plan at once. Credits are topped up to the new allowance once for the current period. |
| Downgrade | The current plan until the period ends. Nothing is taken back. |
| Credits per period | Granted by the paid invoice or transaction of each period, expiring at the period end, no rollover. |
| Trial | One per person, with a payment method required. No credits during the trial, or a small trial allowance. |
| Several subscriptions for one user | Access while any of them gives it. |
| Restores and transfers between accounts | Moved only by the store's record, logged, and never shared by two accounts at once. |
| Reconciliation | Hourly against the provider's list, and on demand from an admin action. Every repair alerts a person. |

## Build

Use the project's router, database layer, migration tool and conventions. Do not add a framework to make the patterns fit. The webhook and the access check in Next.js, Express, Django, Laravel and Rails are in [references/stacks.md](references/stacks.md).

1. **Create the tables.** Copy `assets/subscriptions.postgres.sql` into a migration and adapt it: one row per subscription keyed by (provider, provider id), the checkout table that links a subscription to its user, the trial claims, and the event store. Its header lists the changes for MySQL and SQLite.

2. **Link each subscription to its user before checkout.** Write the app's checkout row, then pass its id to the provider: Stripe metadata and `client_reference_id`, Apple `appAccountToken`, Google Play obfuscated account id, Paddle `custom_data`, RevenueCat app user id. Events are matched to users only through it. See "Linking events to the user" in [references/events-in-any-order.md](references/events-in-any-order.md).

3. **Verify every event.** Subscription events go through the same verification as payment events: the raw body, the signature or token, the timestamp, the stored event id. If the project has no verified endpoint, build it with the `build-webhook-endpoint` skill first; the provider references here give the short version.

4. **Store the provider's latest state.** For each event, find the subscription it names, fetch the subscription from the provider outside any transaction, then in one transaction store the event id and write the subscription only when the fetch is newer than what is stored. Where the provider documents an ordering value, newer-wins on that value works too. Never apply an event's state because it arrived last. Pattern and the cases it covers: [references/events-in-any-order.md](references/events-in-any-order.md).

5. **Compute access in one function, at the time of use.** It reads the user's subscription rows and the current time: a status that keeps access, not revoked, and `grace_until` or `paid_through` still ahead. Every gated route, job and screen calls it. Remove the old flags, session values and token claims that decided access. See [references/entitlements-and-lifecycle.md](references/entitlements-and-lifecycle.md).

6. **Map the lifecycle.** For the provider, map each status and event onto the lifecycle table in the same reference: trial, active, renewal, failed payment and grace, recovery, cancel at period end, cancel now, pause, resume, upgrade, downgrade. Past due keeps access from the end of the last paid period, not from the provider's current period end.

7. **End access on refunds, chargebacks and revocations.** Find the subscription through the provider's records (Stripe: the charge's PaymentIntent, its invoice payment and the invoice's parent; Apple and Google Play: the transaction or the purchase token; Paddle: the adjustment's `subscription_id`) and record the revocation on the row, where no later state write can clear it. A refund does not cancel the subscription at Stripe or Paddle. The credits go back through the `handle-refunds-and-reversals` skill.

8. **Grant credits per paid period, once.** The paid invoice or transaction of a new period posts a ledger entry under `<provider>:<subscription>:<period start>`. A plan change in the same period tops up under its own key and never grants a second full allowance. See [references/period-credits-and-trials.md](references/period-credits-and-trials.md).

9. **Limit trials to one per person.** Store trials are the store's decision. For web trials, claim the trial under an identity key from the `guard-signups` skill before the checkout is created. Same reference, section "Trials".

10. **Schedule the reconciliation job.** Page through the provider's list (Stripe with `status=all`) and write each subscription through the same function as the webhook; check every row that gives access the other way round. Alert on every repair. See "Reconciliation" in [references/events-in-any-order.md](references/events-in-any-order.md).

11. **Remove what the client decides.** A return page that sets the plan, a client receipt check that grants, a plan or status field accepted from a request body, a premium flag in local storage. The return page may say "processing" and show what the server has stored.

## Rules that must hold

A reviewer should be able to check each of these against the diff.

- Access is decided on the server, at the time of use, by one function that reads the stored subscription rows and the current time. No client field, redirect, receipt sent by the client or token claim grants or extends it.
- Each subscription is one row under a unique (provider, provider id) key. A user's access is the union of their rows, never one flag that each event overwrites.
- The user of a subscription comes from the app's own checkout record, never from an email or user id in the event, and never changes on a later write.
- Every event is verified before anything is read from it, and its id is stored under a unique key in the same transaction as its effect.
- The stored state is the provider's latest object: fetched from its API, or written only when the provider's ordering value is newer. A slower or older write cannot overwrite a newer one.
- No call to the provider runs inside a database transaction. A failed call answers 5xx so the provider delivers the event again.
- Unknown statuses give no access. Past due gives access only until a stored grace end computed from the last paid period.
- Cancel at period end keeps access until the paid period ends. Cancel now, refund, chargeback and revocation end it at once, as decided, and a later state write does not undo a revocation.
- Credits per period are ledger entries keyed by subscription and period start. Repeats, a second event type for the same payment, a plan change in the same period and the reconciliation job grant nothing more.
- A web trial is claimed under a unique identity key before the checkout is created.
- The webhook, the reconciliation job and any admin action write subscriptions through the same function.

## Verify

Write these tests in the project's own test framework, against a real database of the kind the project uses, with the provider's API stubbed to return the objects each test sets:

- A subscription created but not paid gives no access and no credits. The first paid invoice or transaction gives both.
- The same paid event twice, ten times at once, and as a second event id for the same payment: credits once.
- A renewal extends access past the old period end and grants the next period's credits once.
- A failed renewal keeps access until the grace end, with no event at the grace end, and removes it after. A late payment restores it.
- Cancel at period end: access until the period end, none after. Cancel now: none at once.
- A refund and a chargeback of a subscription payment end access while the provider still reports the subscription active.
- An older "updated" state delivered after a cancellation does not restore access. A "paid" event before the "created" event ends with access, and the late "created" snapshot does not remove it.
- A forged, unsigned or stale event changes nothing. An earlier genuine event delivered again after a cancellation changes nothing.
- A plan, status or period sent by the client changes nothing.
- One user with two subscriptions keeps access until both end.
- The reconciliation job repairs a cancellation and an activation whose events were never delivered.
- An upgrade in the middle of a period tops the credits up once; the renewal after it grants the new allowance once.

Then run the app locally against the provider's test mode or a local stand-in of its API, and probe it with `scripts/probe.mjs` (run it without arguments for the request file format). Copy `assets/sign-test-event.mjs` into the project's test tools; its `stripe`, `paddle` and `revenuecat` modes sign events the way those providers do. App Store and Google Play events are signed by the store and cannot be produced locally: test those handlers with the verification stubbed. `me.json` reads the test user's credit balance; `perk.json` is a request to a route that needs the plan, sent with the test user's token.

`scripts/probe.mjs` is the copy in this skill's folder. Run the commands below from the project directory, so that the request files resolve against the project. Their first line sets `PROBE` to that copy: replace `<skill directory>` with the folder this `SKILL.md` was read from, such as `.agents/skills/add-subscriptions`.

```bash
PROBE=<skill directory>/scripts/probe.mjs
export WEBHOOK_TEST_SECRET=whsec_test_not_secret
INVOICE='{"id":"in_test_1","object":"invoice","status":"paid","billing_reason":"subscription_create","parent":{"type":"subscription_details","subscription_details":{"subscription":"<test subscription>","metadata":{"checkout_id":"<pending checkout>"}}},"lines":{"data":[{"period":{"start":1763300000,"end":1765892000}}]}}'
EVENT_ID=evt_test_paid_1 node sign-test-event.mjs stripe invoice.paid "$INVOICE" > paid.json
node sign-test-event.mjs stripe invoice.paid "$INVOICE" > paid-again.json
node sign-test-event.mjs stripe invoice.paid "$INVOICE" 600 > stale.json

# Before the first payment, so that a grant would show.
node "$PROBE" send paid.json --drop-header stripe-signature --observe me.json
node "$PROBE" send stale.json --observe me.json
node "$PROBE" send perk.json

# The genuine event ten times at once, again with a fresh signature, and as a second event id.
node "$PROBE" race paid.json --parallel 10 --observe me.json
EVENT_ID=evt_test_paid_1 node sign-test-event.mjs stripe invoice.paid "$INVOICE" > paid.json
node "$PROBE" replay paid.json --times 2 --observe me.json
node "$PROBE" send paid-again.json --observe me.json
node "$PROBE" send perk.json

# The client claims the plan.
node "$PROBE" send checkout.json --set-body plan=premium --set-body status=active --observe me.json
```

Expected:

- Without a signature and with the stale signature: 4xx, the balance does not move, and the perk answers 402 or 403.
- `race`: every answer 2xx, the balance rises by one period's credits. The `replay` and the second event id: 2xx, and the balance does not move. The perk then answers 200.
- The checkout with a plan and a status in the body: no access and no credits for a user who has not paid.

Done when:

- the tests pass in the project's test run,
- the probes give the expected results three times in a row,
- a search for the old access flags, plan columns and token claims finds none that decides access,
- every status and event the provider documents is mapped, or acknowledged on purpose with a note,
- the reconciliation job is scheduled and its repairs reach a person.

## Not a bug

- A user who canceled still has access: correct until the end of the period they paid for.
- Access during a failed payment: correct until the grace end the user chose or the store set.
- The provider says `active` but the app denies access after a refund or a chargeback: the revocation is the app's rule, and the provider does not cancel on refunds.
- A webhook answered 2xx that changed nothing: a duplicate, an older state, or an event for a checkout the app did not create.
- The credits of a period did not grow after an upgrade to a plan with the same allowance.

## Out of scope / do not

- This skill does not build the webhook verification, the ledger, the reversal of credits or the sign-up guard. Those are the `build-webhook-endpoint`, `build-ledger`, `handle-refunds-and-reversals` and `guard-signups` skills. It does not set prices, taxes or invoices: the provider does.
- The provider references record what the documentation said on the date they carry. The provider's current documentation decides statuses, events and fields.
- Do not keep a single `is_premium` or `plan` column that each event overwrites.
- Do not apply events in arrival order, and do not order Stripe events by `created`.
- Do not grant on "subscription created": at Stripe it arrives before payment.
- Do not keep access while past due until the provider's current period end: that period was not paid.
- Do not end access on a cancel at period end, on Apple `AUTO_RENEW_DISABLED`, or on Google Play `SUBSCRIPTION_CANCELED`.
- Do not key period credits on the event id or on the calendar month.
- Do not trust a receipt, a purchase result or a plan name sent by the client. The server asks the provider.
- Do not call the provider inside a database transaction, and do not answer 2xx before the state is stored.
- Do not send probes or test events to a provider's live API or to an environment shared with others.
