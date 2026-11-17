---
name: handle-refunds-and-reversals
description: Make refunds, chargebacks, disputes and reversed conversions take back what the original event granted, exactly once. Covers credits, entitlements, items and dependent rewards such as referral commission, partial refunds, balances that are already spent, the dispute life cycle, and a reversal that arrives before its original. Maps the refund, dispute and revocation events of Stripe, Paddle, Lemon Squeezy, PayPal, RevenueCat, the App Store and Google Play. Use when the user says refunded customers keep their credits or access, asks to handle refund or dispute webhooks (such as charge.refunded, charge.dispute.created, adjustment.created, order_refunded, PAYMENT.CAPTURE.REFUNDED, an App Store REFUND or a Google Play voided purchase), chargebacks, clawbacks or reversal postbacks, or wants a rule for negative balances and a report of what was reversed.
license: MIT
compatibility: The verification step needs Node 20 or newer to run the bundled probe script.
metadata:
  author: moonetix
  version: "1.3.5"
---

# Handle refunds and reversals

This skill produces the code that follows money when it goes back: a refund, a chargeback, a conversion a network takes back. Each reversal is computed from the credit it undoes, applied once, and followed through to everything that credit caused. It prevents the loop in which a user buys, spends or withdraws, gets the money back and keeps the goods. It also prevents the opposite failures: a reversal that subtracts twice, or from the wrong account.

**Which of the three skills.** Use this one when something already credited must be taken back: a refund, a chargeback, a revocation or a reversed conversion, with everything the credit caused. To receive and verify the event that grants, use `build-webhook-endpoint`. A new offerwall gets its reversal postbacks from `add-offerwall`; this skill fixes reversals in an existing one. Subscription access, and how a refund or a chargeback of a renewal ends it, is the `add-subscriptions` skill; this one takes back the credits that period granted.

## Before writing code

Read the project first, and ask the user only what the code cannot tell you.

- **Stack.** Language, framework, database, migration tool, test framework, how a transaction is opened.
- **How value gets in.** Every path that credits: purchases, subscriptions, conversions, bonuses. For each, the record it leaves: an order row, a ledger entry with its kind and reference, a transaction id. A credit that leaves no record cannot be reversed, and step 2 has to fix that first.
- **Which reversing events arrive.** For each provider, list from its documentation the events that mean money went back: refund, partial refund, dispute opened, won and lost, subscription cancelled or expired, failed renewal, store refund notification, a reversal status in a postback. Then find the code for each. The ones that are acknowledged and ignored are the scope. For Stripe, Paddle, Lemon Squeezy, PayPal, RevenueCat, the App Store and Google Play the list is in [references/provider-reversal-events.md](references/provider-reversal-events.md); confirm it against the pages it cites.
- **What a purchase grants.** A balance, a plan, items, seats. And what it causes for others: referral commission, cashback, tier progress.
- **How value leaves.** Spending, transfers, payouts. Whether payouts have a hold period.
- **Refunds the app issues.** An admin action, a self-service button, a support script.
- **The ledger.** Whether there is a posting function with a unique (kind, reference) key, a pointer to the reversed entry and a flag that allows debt, as the `build-ledger` skill builds it.

Then settle the decisions that belong to the user. Ask once, in one message, and offer the default.

| Decision | Default |
| --- | --- |
| The balance is already spent | Debt. The reversal applies in full, the balance goes below zero, spending and payouts are refused until it is repaid, and the account is marked for review. |
| Partial refund of a balance grant | A proportional share, rounded down, computed on the running total so that a full refund in parts takes back exactly the grant. |
| Partial refund of a plan or item | The grant stays. A full refund or a dispute revokes it. |
| Dispute opened | Take back what is left now, suspend what the order granted, hold payouts. Give it back if the dispute is won. |
| Dispute lost | The account stays restricted until a person reviews it. |
| Dependent rewards | Taken back in proportion, in the same transaction, also when the referrer has spent them. |
| Forgiving debt | Never automatic. Staff may write a debt off, with a reason, as its own entry. |
| Subscription cancelled | Access until the end of the paid period. A refund or a dispute ends it at once. |
| Consumed or delivered goods | Not charged as debt. The account is marked for review. |
| Dispute fee | Recorded for the report, not charged to the user. |
| Who may refund from the app | Staff with a named permission. No self-service. |

## Build

Use the project's database layer, migration tool and conventions. Reversal handlers sit behind the same verification as the handlers that credit: a refund event is checked like a payment event. The route itself in Next.js, Express, Django, Laravel and Rails, with the raw body, the CSRF exemption and the once-only transaction, is in [references/webhook-stacks.md](references/webhook-stacks.md).

1. **Map the events.** Write down, per provider, which documented event becomes a refund, which stage of a dispute, a conversion reversal, or a change of subscription state, which field gives the amount, and which id links it to the original credit. Unknown events stay acknowledged and ignored. The map for seven providers is in [references/provider-reversal-events.md](references/provider-reversal-events.md).

2. **Make every credit findable.** Each credit has one record that says which account received how much, under a key built from the order id or the provider's transaction id. Dependent rewards are posted with the reference of the entry that caused them. The table of kinds and references is in [references/tie-reversals-to-originals.md](references/tie-reversals-to-originals.md).

3. **Add the tables for the facts.** Copy `assets/reversals.postgres.sql` into a migration and adapt it: `refunds` and `disputes` keyed by the provider's id, `conversions` for credits without an order, `grants` for what an order gave besides a balance.

4. **Write the take-back function.** One function subtracts for a reversal. It reads the account and the upper bound from the original entry and never takes more than is left of the grant. Pattern in [references/tie-reversals-to-originals.md](references/tie-reversals-to-originals.md).

5. **Handle refunds, full and partial.** Store the refund under its id, then settle: each refund's share is computed on the running total. Same reference, section "Refunds, full and partial".

6. **Handle the reversal that arrives first.** The handler that credits a purchase ends with the settle function, so a refund stored earlier is taken back in the same transaction. For credits without an order, the credit and the reversal both write one keyed row first. Same reference, section "A reversal that arrives before its original".

7. **Apply the rule for spent balances.** Reversals pass the debt flag and never fail for lack of funds. Check every way value leaves an account: spending, transfers, payouts, unsent payouts. See [references/debt-entitlements-dependents.md](references/debt-entitlements-dependents.md).

8. **Revoke what was granted besides a balance.** Access is read from the grant row at the time of use. Subscription state follows every event that ends or shortens it. Same reference, section "Entitlements and items".

9. **Take dependent rewards back** in the same transaction, in proportion to what is left of the original. Same reference, section "Dependent rewards".

10. **Handle the dispute life cycle.** Opening takes once, a win gives back exactly what the opening took, the close is a conditional move. Code and the table of event sequences are in [references/disputes-and-reporting.md](references/disputes-and-reporting.md).

11. **Route the app's own refunds through the same functions.** Reserve the amount, call the provider with an idempotency key, and apply the provider's answer under the refund id the webhook will carry. See "Refunds the app issues itself" in [references/tie-reversals-to-originals.md](references/tie-reversals-to-originals.md).

12. **Report and reconcile.** The queries for reversals per day, repeat reversals, debt and unapplied facts, and a scheduled job that feeds the provider's list of refunds and disputes through the same handlers. See [references/disputes-and-reporting.md](references/disputes-and-reporting.md).

13. **If there is no ledger,** build the minimum from [references/tie-reversals-to-originals.md](references/tie-reversals-to-originals.md): a conditional move or unique key that makes the take-back happen once, in the transaction that changes the balance. Tell the user what it cannot do.

## Rules that must hold

A reviewer should be able to check each of these against the diff.

- Every reversal entry points at the entry it reverses and goes to the account that entry credited.
- No amount, user id or account from a reversal message reaches a balance update. The message selects the original and states how much money went back. Everything else is read from stored records.
- Each refund and each dispute is stored under a unique (provider, id) key in the schema. Each reversal entry has a ledger key built from that id.
- Everything taken back for one original never adds up to more than it granted.
- A full refund in parts takes back exactly the grant. Shares are computed on the running total.
- All reversals of one order run under a lock on that order.
- A reversal never fails because the balance is too low. Only reversal paths may push a balance below zero.
- While a balance is below zero, no spend, transfer or payout succeeds.
- Nothing clamps at zero. Forgiven debt is an entry of its own with an actor and a reason.
- A reversal whose original is not there yet is stored, not dropped and not subtracted. The code that credits the original applies it.
- Access checks read the grant at the time of use. A full refund or a dispute revokes it. A won dispute restores only what the dispute revoked.
- Dependent rewards go back in the same transaction as the original.
- A dispute takes once at opening and gives back, when won, the amount it took. Closing is a conditional move from `open`.
- Duplicates are answered with the sender's success response, after the commit.
- The webhook, the admin refund and the reconciliation job call the same functions.

## Verify

Write these tests in the project's own test framework, against a real database of the kind the project uses:

- A full refund takes back the grant. The same refund again, and ten times at once, changes nothing more.
- Three partial refunds that add up to the price take back exactly the grant. Many refunds too small for a share of their own still add up to it.
- A refund after the balance was spent leaves a negative balance. A spend and a payout are then refused. A new credit raises the balance toward zero.
- A refund for an order that was never credited subtracts nothing. When the payment is then processed, the balance ends where it started.
- A conversion reversal before its credit, then the credit: nothing is credited. The credit, then the reversal twice: taken back once.
- A reversal message that names another user or another amount than the original takes the original's amount from the original's account.
- Every row of the sequence table in [references/disputes-and-reporting.md](references/disputes-and-reporting.md).
- A full refund revokes the grant and an access check then fails. A partial refund does not. A dispute revokes, and a win restores.
- Half an order refunded takes half the referral commission. A dispute takes the rest. A win gives it back.
- After every test, the ledger's reconciliation query returns no rows.

Then run the app locally with test configuration and probe it with `scripts/probe.mjs` (run it without arguments for the request file format). Create the signed request files with the helper the project's webhook tests use, signed with the local test secret. Each scenario uses its own test order. `me.json` reads the test user's balance. The order grants 500 credits for 499 cents.

`scripts/probe.mjs` is the copy in this skill's folder. Run the commands below from the project directory, so that the request files resolve against the project. Their first line sets `PROBE` to that copy: replace `<skill directory>` with the folder this `SKILL.md` was read from, such as `.agents/skills/handle-refunds-and-reversals`.

```bash
PROBE=<skill directory>/scripts/probe.mjs
# 1. A full refund, exactly once.
node "$PROBE" send paid-1.json --observe me.json
node "$PROBE" race refund-1.json --parallel 10 --observe me.json
node "$PROBE" replay refund-1.json --times 2 --observe me.json

# 2. Partial refunds of 166, 166 and 167 cents.
node "$PROBE" send paid-2.json --observe me.json
node "$PROBE" send refund-2a.json --observe me.json
node "$PROBE" send refund-2b.json --observe me.json
node "$PROBE" send refund-2c.json --observe me.json

# 3. A dispute that is won.
node "$PROBE" send paid-3.json --observe me.json
node "$PROBE" replay dispute-3-opened.json --times 2 --observe me.json
node "$PROBE" replay dispute-3-won.json --times 2 --observe me.json

# 4. A reversal postback before its credit, for a transaction id never seen.
node "$PROBE" send reversal-4.json --observe me.json
node "$PROBE" send credit-4.json --observe me.json

# 5. A spent balance. Use a fresh test user.
node "$PROBE" send paid-5.json --observe me.json
node "$PROBE" send spend.json --var TOKEN=$TOKEN --observe me.json
node "$PROBE" send refund-5.json --observe me.json
node "$PROBE" send spend.json --var TOKEN=$TOKEN --observe me.json
node "$PROBE" send payout.json --var TOKEN=$TOKEN --observe me.json
```

Expected:

1. The payment raises the balance by 500. In the race all ten answer 2xx and the balance falls by 500. The replay answers 2xx twice and the balance does not move.
2. The three refunds lower the balance by 166, 166 and 168.
3. The opening lowers the balance by 500 once. The win raises it by 500 once.
4. Both answer with the success response, and the balance does not move in either.
5. After the refund the balance is below zero by the price of what was spent. The spend and the payout that follow each answer 4xx, and the balance does not move.

Done when:

- the tests pass in the project's test run,
- the probes give the expected results three times in a row,
- every reversing event the providers document has a handler, or a written note from the user that it is not sent,
- a search for statements that subtract from a balance finds no reversal outside the take-back function,
- the report queries run, and the reconciliation job is scheduled and its failures reach a person.

## Out of scope / do not

- This skill does not verify inbound events, build the ledger or build payouts. Those are the `build-webhook-endpoint`, `build-ledger` and `add-payouts` skills.
- It does not decide refund policy, write dispute evidence, or handle tax and invoices. Credit notes are the accounting system's work.
- Do not subtract the amount named in the reversal message. Look up what was credited.
- Do not clamp at zero. It forgives the debt without a record and makes refunds a way to mint value.
- Do not let a reversal fail on insufficient funds. The provider retries it forever and it never applies.
- Do not update or delete the original entry or mark it "refunded" in place. Post a new entry that points at it.
- Do not answer a reversal with an error because its original is unknown. Store it.
- Do not acknowledge a reversing event that the code does not handle yet without storing it.
- Do not treat a partial refund as all or nothing.
- Do not wait for the dispute decision before taking the value back. The balance will be gone by then.
- Do not build a second take-back in the admin tool. The refund button and the webhook meet on the refund id.
- Do not call a provider's live refund API from a test or a probe.
