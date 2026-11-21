---
name: add-payouts
description: Build withdrawals as a state machine. The funds are taken from the balance before the provider is called, the call carries an idempotency key, a timeout is resolved by asking the provider and never by sending again, and a failure returns the funds once. Adds a minimum, daily limits, a hold on fresh earnings, an earned-only withdrawable balance, a cool-down after a destination change, a review queue and reconciliation with the provider. Covers Next.js with Prisma, Express, Django, Laravel and Rails. Use when the user asks to add payouts, withdrawals, cash-out, redemptions or gift card rewards, or to fix double payouts, lost refunds or missing payout limits.
license: MIT
compatibility: The verification step needs Node 20 or newer to run the bundled probe script.
metadata:
  author: moonetix
  version: "1.3.6"
---

# Add payouts

This skill produces the path on which value leaves the app as money: a payout row that moves through fixed states, funds that are taken before anything is sent, and the limits, holds and checks around it. A payout is the point where a mistake stops being a number in a database. The failures it prevents: parallel requests that are all paid from one balance, a retry that sends a second transfer, a timeout that is treated as a failure so the user gets the refund and the money, a failure that never returns the funds, and an account that is emptied minutes after someone else got into it.

## Before writing code

Read the project first, and ask the user only what the code cannot tell you.

- **Stack and database.** Language, framework, database engine, migration tool, test framework, job scheduler or queue, and how the project opens a transaction.
- **The balance.** A ledger with a posting function, or a bare balance column. Which kinds of entries exist and which of them are earned, bought or given away. This decides what can be withdrawn.
- **Existing payout code.** Any withdrawal endpoint, approval tool or provider call, and the order in which it checks, pays and deducts.
- **The payout provider.** Read its documentation, do not guess: how an idempotency key or your own reference is sent, which answers are final failures, how a payout is looked up afterwards, whether results arrive as events, and which report lists what was sent.
- **Account state.** How the project marks banned, flagged or unverified accounts, and how a user confirms their identity again inside a session.
- **Staff tools.** Where an admin screen and its permissions live, and whether there is an audit log.

Then settle the decisions that belong to the user. Ask once, in one message, and offer the default. The numbers are examples in a ledger of cents. The owner sets them.

| Decision | Default |
| --- | --- |
| What can be withdrawn | Earned value only (offers, sales, commissions). Bought, promotional and bonus value is for spending. |
| Hold on earnings | The longest reversal window of any earning source, and not less than 14 days. |
| Minimum per payout | 5.00, and at least several times the provider's fee. |
| Maximum per request and per 24 hours | 200.00 a day in at most 3 requests. Lower for accounts younger than 30 days. |
| Manual review | The first payout of an account, any payout of 100.00 or more, and a destination that another account uses. |
| Destination change | Password or second factor again, a notice to the old contact address, and a 48 hour cool-down. The same pause after a password or email change. |
| Provider fee | Paid by the app. The user receives the amount shown. |
| When to send | From a queue worker if the project has one. Otherwise right after the request, with a scheduled job that resolves what is open. |
| Unknown result | Asked from the provider every 15 minutes. A person is alerted after 6 hours. |
| Reconciliation | Daily, against the provider's own records. Every difference goes to a person. |

## Build

Use the project's migration tool, database layer and conventions. Do not add a framework to make the patterns fit. The request and the send claim in Next.js with Prisma, Express, Django, Laravel and Rails are in [references/stacks.md](references/stacks.md).

1. **Make sure balance changes go through a posting function.** Payouts post two kinds of entry, `payout` and `payout_refund`, with the payout id as reference, through the function built by the `build-ledger` skill or the project's equivalent. If there is no ledger yet, the minimum is a conditional debit in the same transaction as the payout row and a refund tied to a guarded status change. The hold and the earned-only rule need dated entries, so build the ledger first when they are wanted. See [references/payout-state-machine.md](references/payout-state-machine.md), section "Without a ledger".

2. **Create the schema.** Copy `assets/payouts-schema.sql` into a migration and adapt names and key types: a `payouts` table with a status, a server-made id, the client's request key and a copy of the destination, and a `payout_destinations` table with a usable-from time.

3. **Write the policy and the checks.** One server-side object holds the limits. One function computes the withdrawable amount from the ledger. One function returns the reason for a refusal. See [references/limits-holds-and-destinations.md](references/limits-holds-and-destinations.md).

4. **Build the request.** In one transaction, under a lock on the account row: return the earlier payout for a repeated request key, run the checks, post the `payout` entry, insert the row as `pending` or `in_review`. Commit before anything is sent. [references/payout-state-machine.md](references/payout-state-machine.md), section "Request".

5. **Wrap the provider in an adapter** that sends the payout id as the idempotency key, sets a timeout, and maps every answer to `paid`, `accepted`, `failed` or `unknown`. Only answers the provider documents as final failures become `failed`. For tests and local runs, add a stand-in adapter that can be told to pay, fail or time out.

6. **Send through a claim.** One conditional statement moves `pending` to `sending` and checks the account's state again. Only the caller that changed the row calls the provider. Same reference, section "Send".

7. **Resolve what is unknown.** A scheduled job asks the provider about payouts that are still `sending`, applies a definite answer, repeats the call only with the same key when the provider has no record, and reports what needs a person. If the provider sends events, apply them through the same function. Same reference, section "Resolve what is unknown".

8. **Protect the destination.** Changing it needs fresh authentication, closes the old row, opens a new one with a cool-down and notifies the owner. [references/limits-holds-and-destinations.md](references/limits-holds-and-destinations.md), section "Changing where the money goes".

9. **Build the review queue.** Approve and reject as guarded moves, with the staff member's identity from the session, and a screen that shows why the payout is there and what the account did. See [references/review-and-reconciliation.md](references/review-and-reconciliation.md).

10. **Show the user the truth.** The withdrawable amount, what is still in hold and until when, and each payout with its real status: requested, in review, on its way, paid, failed with the funds returned.

11. **Reconcile.** Schedule the queries that compare payouts with the ledger and list stuck payouts, and the daily comparison with the provider's records. Same reference, sections "Reconcile the payouts with the ledger" and "Reconcile with the provider".

## Rules that must hold

- The funds are taken, and the payout row is created, in one transaction that commits before the provider is called. No path calls the provider first.
- The debit is conditional or runs under a row lock, and all checks for one account run one request at a time.
- Every provider call carries the payout id as idempotency key. The key of a payout never changes.
- `sending` is left only on a definite answer from the provider. A timeout, a connection error or an unrecognized answer leaves it `sending`.
- A payout is never sent again with a new key. A repeat uses the same key, inside the time the provider honors it.
- Funds return only on `failed`, `rejected` or `canceled`, in the same transaction as the status change, as one `payout_refund` entry per payout id.
- Every write to the status names the status it expects. No statement sets a status unconditionally.
- A final status never changes. A conflicting answer from the provider is reported, not applied.
- The amount is a whole number, at least the minimum, at most the limits, and converts to whole minor units. The limits are server-side constants.
- Only matured, earned value is withdrawable, computed from the ledger when the request is made.
- Account state is checked when the payout is requested and again when it is claimed for sending.
- A destination is usable only after its cool-down, and a payout keeps the destination it was requested with.
- Staff decisions carry the staff member's identity from the session. Nobody approves a payout of their own account.
- The provider's records and the app's are compared on a schedule, and differences reach a person.

## Verify

Write these tests in the project's own test framework, against a real database of the kind the project uses, with the stand-in provider:

- A request takes the funds and creates one row. The same request key again returns the same payout and takes nothing.
- Five parallel requests with different keys against a balance that covers one: one payout, one debit.
- Requests that together pass the daily amount or count are refused, also when sent in parallel.
- Zero, negative, fractional and string amounts, and amounts below the minimum, are refused and change nothing.
- Fresh earnings, bought value and promotional value cannot be withdrawn. Matured earnings can.
- The provider pays: status `paid`, no refund entry. The provider fails: status `failed`, one refund entry, also when the failure is applied twice.
- The provider times out: status `sending`, no refund, one provider call. The resolver later applies `paid`, or `failed` with one refund.
- The provider has no record: the call is repeated with the same key. Past the key's lifetime it is not, and the payout is reported.
- Two senders at once call the provider once.
- A payout of a flagged account is not sent. A destination inside its cool-down cannot be used.
- Approve and reject each work once, a rejection returns the funds once, and staff cannot approve their own.
- After every test, the payout and ledger reconcile queries return no rows.

Then run the app locally with test configuration and the stand-in provider, and probe it. Never point a test at a real payout API. Describe each request in a JSON file as `scripts/probe.mjs` expects (run it without arguments for the format). `me.json` reads the test user's balance, `payouts.json` reads the payout list with `"path": "payouts.length"`.

`scripts/probe.mjs` is the copy in this skill's folder. Run the commands below from the project directory, so that the request files resolve against the project. Their first line sets `PROBE` to that copy: replace `<skill directory>` with the folder this `SKILL.md` was read from, such as `.agents/skills/add-payouts`.

```bash
PROBE=<skill directory>/scripts/probe.mjs
# Amounts that must be refused.
node "$PROBE" send payout.json --set-body amount=1 --observe me.json
node "$PROBE" send payout.json --set-body amount=-500 --observe me.json

# A double click: the same idempotency key, five times at once.
node "$PROBE" race payout.json --parallel 5 --observe me.json --observe payouts.json

# The daily limit: four requests in a row, each with its own key ({{i}} is 1 to 4).
node "$PROBE" replay payout.json --times 4 --set-header idempotency-key=probe-cap-{{i}} --observe me.json

# A fresh account, credited a moment ago through a verified test event.
node "$PROBE" send payout.json --set-header "authorization=Bearer $FRESH_ACCOUNT_TOKEN" --observe me.json
```

Expected:

- The two bad amounts: a 4xx each, and the balance does not move.
- The race: every request answers with the same payout id, the balance falls by one amount, and the list grows by one.
- The daily limit: with the default of three requests a day, the fourth is refused with a 4xx and the balance falls by three amounts.
- The fresh account: refused because nothing has matured, and the balance does not move.
- With the stand-in provider set to time out, a request leaves the payout `sending` and the balance lowered. Run the resolver command right away, without waiting: the payout becomes `paid` or `failed` according to what the stand-in reports, and a failure raises the balance once.

Done when:

- the tests pass in the project's test run,
- the probes give the expected results three times in a row,
- a search for statements that write the payout status finds only guarded ones,
- the resolver, the reconcile queries and the provider comparison are scheduled, and their failures reach a person,
- the adapter's list of final failure codes was taken from the provider's documentation and says so in a comment.

## Out of scope / do not

- This skill does not build the ledger, verify provider events or reverse earnings. Those are the `build-ledger`, `build-webhook-endpoint` and `handle-refunds-and-reversals` skills. It does not cover identity checks, tax forms or sanctions screening, which may be required by law before paying people: raise that with the owner.
- Do not check the balance, call the provider and deduct afterwards. Parallel requests all pass the check and are all paid.
- Do not treat a timeout as a failure. The refund goes out, and so may the money.
- Do not retry a payout with a fresh key, a fresh payout id or a "retry" button that creates a new transfer for the same row.
- Do not hold a database transaction open while the provider is called.
- Do not set a status with an unconditional update, and do not let an admin tool edit the status column.
- Do not make the whole balance withdrawable, and do not let a transfer between accounts turn bonus value into earned value.
- Do not fix a difference found by reconciliation with a script that edits rows. Post entries, with a name and a reason.
- Do not log full destination details or provider credentials, and do not test against the live provider.
