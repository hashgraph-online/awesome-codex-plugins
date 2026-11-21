# Refunds and reversals

**Class id:** `refunds-and-reversals`

Money that came in can go back: a refund, a chargeback, a dispute, a cancelled subscription, an advertiser taking a conversion back. If the app does not follow the money, the user keeps what it bought. Buy, spend or withdraw, refund, repeat.

## Where to look

The event types each "in" handler accepts, and the ones it silently ignores. Subscription lifecycle code. Any code the app uses to issue refunds itself. What happens to referral bonuses and commissions when the underlying payment is reversed.

## Shapes that are bugs

**The reversing event is acknowledged and ignored.**

```js
if (event.type === 'payment.succeeded') { await credit(order); }
res.json({ received: true });           // payment.refunded, dispute.created: 200 and nothing else
```

When the provider's event catalogue is not in the repository, say so in the report's notes and check the events the code does name. The reversing events of seven common providers, and what their handlers get wrong, are in [payment-providers.md](payment-providers.md). List the provider's reversing events (refund, partial refund, dispute opened, dispute lost, subscription cancelled, subscription expired, payment failed on renewal, store refund notification, postback with a reversal status) and find the code for each. Missing code is the finding.

**The reversal is not tied to the original.** The handler subtracts the amount named in the reversal message instead of the amount it credited for that transaction. Then:

- a reversal for a transaction that was never credited still subtracts,
- a reversal delivered twice subtracts twice,
- a reversal with a different amount or user id subtracts the wrong thing from the wrong account.

```php
if ($status == 2) {
    $db->query("UPDATE users SET balance = balance - ? WHERE id = ?", [$reward, $userId]);   // no link to the credit
}
```

**The reversal arrives first.** Providers and networks do not promise an order. A refund or reversal for a payment the app has not processed yet is answered 2xx and forgotten, and the late original then credits in full. Look at what the handler does when it finds no original: it must leave something behind (a closed order, a stored reversal) that the original will meet.

**No rule for a balance that is already spent.** The reversal arrives after the credits were used or withdrawn. Code that clamps at zero forgives the debt silently; code that refuses to go negative fails the event and the provider retries forever. There must be a deliberate rule.

**Entitlements outlive the payment.** A subscription stays active after cancellation, expiry, failed renewal or refund because only the "created" event is handled. A one-time unlock stays after the charge is refunded.

**Partial refunds treated as all or nothing.** A refund of part of the amount removes everything, or removes nothing.

**Refunds the app issues.** An endpoint that refunds an order can be called twice, can refund more than was paid, or refunds without taking back what was granted.

**Second-order rewards stay.** A referral bonus, cashback or affiliate commission paid because of a purchase is kept when the purchase is refunded.

## What correct looks like

- Every credit records where it came from (provider, transaction or order id).
- A reversal looks up that record, reverses exactly what was granted, to the account that received it, and is itself recorded under a unique key so that a second delivery does nothing.
- The rule for spent balances is explicit. A common one: let the balance go negative, block spending and withdrawals while it is below zero, and flag the account.
- Subscription state is driven by the provider's events or by asking the provider, covering cancel, expire, failed renewal and refund.
- A hold period before earned value can be withdrawn makes reversals collectable. See payout controls.

## How to prove it

Complete a purchase with a correctly signed test event, then send the reversing event and observe:

```bash
node scripts/probe.mjs send paid.json --observe me.json
node scripts/probe.mjs send refunded.json --observe me.json       # delta should be minus the credit
node scripts/probe.mjs replay reversal.json --times 2 --observe me.json   # delta should be one reversal, not two
```

For an ignored event the proof is a balance that does not move. For a missing handler in an app that cannot be run, a trace through the event dispatch showing no branch for the type is enough.

## Not a bug

- The provider does not send reversing events for this integration and the business accepts the risk in writing. Record it as clear with that note, and suggest reconciling against the provider's reports.
- Reversals are handled by a scheduled reconciliation job rather than by the webhook. Find the job and check it the same way.
- Clamping at zero as a stated policy for small amounts, with the shortfall recorded.

## Severity

Ignored refunds or chargebacks where the goods can be spent or withdrawn first: critical, because it is a repeatable loop. Double-applied or mis-targeted reversals: high. Missing partial-refund handling: medium.
