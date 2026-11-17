# Payout controls

**Class id:** `payout-controls`

A payout is the point where a mistake stops being a number in a database and becomes money that is gone. Every other flaw in this audit is cheaper when withdrawals are limited, delayed and paid exactly once.

## Where to look

Withdrawal, cash-out, redemption and gift card endpoints. The code that calls the payout provider. Approval tools. Endpoints that change where a user is paid (email, bank details, wallet address).

## Shapes that are bugs

**No limits at all.**

```js
const coins = Number(req.body.amount);
if (!(coins > 0) || user.balance < coins) return res.status(400).end();
await provider.send(user, coins / RATE);       // any amount, any time, any number of times a day
```

Look for a minimum, a maximum per request, a cap per day, and a cap for new accounts.

**No hold.** Value credited a second ago can be withdrawn now. Then a reversal, a fraud review or a discovered bug always comes too late. Earned value that can be reversed (offers, referrals, sales) needs a maturity period at least as long as the reversal window.

**Everything is withdrawable.** Promo, sign-up and referral bonuses, and purchased credits, flow out through the same door as earned value.

**Paid before recorded, or recorded before paid, with no way back.** The provider is called first and the balance is reduced afterwards (see balance races). Or the balance is reduced, the provider call fails, and nothing returns the funds. Or a timeout is treated as failure, the funds are returned, and the provider pays anyway.

**A balance check on a view that misses later debits.** The check reads the balance as of a time, or through a filter (entries dated up to the request, one status, one currency), while the debits it must account for can sit outside that view. A payout stamped earlier than a payout or clawback already recorded then passes, because the later-dated debit is not part of the as-of balance, and the account goes negative. The amount a payout is compared with must count every debit already recorded, whatever its date or status. A reporting function such as `balance(at)` is not a spending check. When the dates come from the caller, rate it by how easily the caller produces them out of order: clocks that differ between servers, retries, requests processed later than they were made.

**No idempotency key to the provider.** A retried request, a double click or a worker restart creates a second transfer for the same payout.

**A status with no rules.** The payout row has a status column that any code path can set to anything. Look for transitions that should be impossible: paid to pending, failed to paid without a new provider call, a refund of a payout that was already refunded.

**The destination changes without friction.** An attacker who gets into an account changes the payout address and withdraws in the same session. Look for re-authentication, a notification and a cool-off after a destination change.

**Flags are not checked.** Accounts that are banned, under review or in debt can still request payouts. Requests are checked when created but not when executed hours later by a worker.

**No reconciliation.** Nothing compares what the app believes it paid with what the provider reports.

## What correct looks like

A payout is a small state machine with funds reserved up front:

1. In one transaction: check limits, hold and account state; take the funds from the balance; create the payout as `pending`.
2. Call the provider with the payout id as the idempotency key.
3. On success mark it `paid`. On a definite failure return the funds once and mark it `failed`. On a timeout leave it `pending` and ask the provider later; do not guess.

Around it: a minimum and a daily cap, a hold on reversible earnings, only earned value withdrawable, manual approval above a threshold, a cool-off after destination changes, and a daily comparison with the provider's records.

## How to prove it

```bash
node scripts/probe.mjs send payout.json --set-body amount=1                   # below any sensible minimum
node scripts/probe.mjs replay payout.json --times 5 --observe me.json         # no daily cap
node scripts/probe.mjs race payout.json --parallel 5 --observe me.json        # paid more than the balance
```

For the hold: credit a fresh account through a verified test event, request a payout at once, and show that it is paid. For provider idempotency and failure handling, a trace through the payout code is usually the only safe proof. Never call a real payout API to test.

## Not a bug

- Payouts are approved by a person and the tool shows them the account's history. Limits can then be looser; say so in the note.
- The provider enforces its own limits. That is a second line, not a replacement: report missing app-side limits as medium.
- The app has no cash-out. Record the class as not applicable.

## Severity

More paid out than the balance, or a payout that can be triggered twice: critical. No hold on reversible earnings, or bonus value withdrawable: high. Missing minimum, cap or destination cool-off: medium. No reconciliation: low.
