# Credits per period, and trials

Two things a plan often gives besides access: an allowance of credits for each paid period, and a free trial before the first payment. Both are easy to grant twice.

## Credits per paid period

A plan that includes credits grants them once per paid period. The grant is a ledger entry, as the `add-usage-credits` skill builds it, with a reference built from the subscription and the period it paid for:

```text
kind = 'plan_allowance'
ref  = '<provider>:<subscription id>:<period start, Unix seconds>'
```

The unique (kind, ref) key of the ledger makes every repeat a no-op: the same event delivered again, the same payment reported by two event types, the reconciliation job finding the period again. A key built from the event id does not do that: a second event about the same payment has a new id. A key built from the invoice or transaction id is closer, but a plan change can produce a second paid invoice for the same period.

```js
// Node with the pg driver, inside the transaction that stores the paid period.
// postEntry inserts the ledger row under (kind, ref) and returns false when it was already there.
// periodStart and periodEnd come from the provider's paid invoice or transaction, not from the clock.
export async function grantPeriodAllowance(tx, { provider, subscriptionId, userId, periodStart, periodEnd, allowance, postEntry }) {
  return postEntry(tx, {
    accountId: userId,
    amount: allowance,
    kind: 'plan_allowance',
    ref: `${provider}:${subscriptionId}:${periodStart}`,
    expiresAt: periodEnd, // the default: unused allowance ends with the period
  });
}
```

What counts as a paid period, per provider:

| Provider | A new period was paid when | Period start from |
| --- | --- | --- |
| Stripe Billing | `invoice.paid` with `billing_reason` `subscription_create` or `subscription_cycle` | The subscription line's `period.start` (not the invoice's `period_start`, which Stripe says is not the service period) |
| App Store | `SUBSCRIBED` or `DID_RENEW` with a new `transactionId` | The verified transaction's `purchaseDate`, keyed by its `transactionId` or `webOrderLineItemId` |
| Google Play | `subscriptionsv2.get` shows a new `lineItems[].latestSuccessfulOrderId` | Key on the purchase token and that order id; each renewal gets a new order id |
| Paddle Billing | `transaction.completed` for a subscription renewal, with `billing_period` set | `billing_period.starts_at` |
| RevenueCat | `INITIAL_PURCHASE` or `RENEWAL` | Key on `transaction_id` |

Do not grant from a calendar job alone. A renewal that failed must not refill the allowance.

### A plan change in the middle of a period

The renewal and the upgrade can land in the same period: the period's allowance was granted at renewal, then the user upgrades and the provider charges a prorated amount. The default:

- An upgrade tops the period up to the new plan's allowance, once: the amount is the new allowance minus what this period already received, under the key `<provider>:<subscription>:<period start>:<new plan>`. A second upgrade event, or the renewal event arriving late, grants nothing more, because the period key and the top-up key both exist.
- A downgrade takes nothing back. The lower allowance applies from the next period.
- A Stripe invoice with `billing_reason` `subscription_update` (a proration) is not a new period.

```js
// The top-up after an upgrade. sumForPeriod reads the ledger for refs that start with the period key.
export async function topUpAfterUpgrade(tx, { provider, subscriptionId, userId, periodStart, newPlan, newAllowance, sumForPeriod, postEntry }) {
  const periodKey = `${provider}:${subscriptionId}:${periodStart}`;
  const already = await sumForPeriod(tx, userId, periodKey);
  const missing = newAllowance - already;
  if (missing <= 0) return false;
  return postEntry(tx, { accountId: userId, amount: missing, kind: 'plan_allowance', ref: `${periodKey}:${newPlan}` });
}
```

### Refunds of a period

A refunded or charged-back renewal ends access (see [entitlements-and-lifecycle.md](entitlements-and-lifecycle.md)). The credits of that period are taken back by the reversal code of the `handle-refunds-and-reversals` skill, which reads the grant by its ledger reference and takes back what is left of it. Do not subtract the allowance a second time in the subscription handler.

## Trials

A free trial costs the app money for every account that never pays. The rule: one trial per person, not per account.

**Store trials.** On the App Store and Google Play, the store decides eligibility: Apple allows one introductory offer per subscription group per person, and Google Play shows only the offers the user is eligible for and can limit free trials to one per app. The server still verifies the purchase and reads the trial from it (Apple: `offerType` 1 with `offerDiscountType` `FREE_TRIAL`; Google Play: the line item's `offerPhase`). It does not grant a trial of its own on top.

**Web trials** (Stripe, Paddle) are the app's decision. Claim the trial before the checkout is created, under a unique identity key, in the same transaction as the checkout row:

```sql
-- identity_key comes from the sign-up guard: a normalized email, a verified phone, a card
-- fingerprint from the provider, or a combination the user chose.
INSERT INTO trial_claims (identity_key, user_id, provider, provider_id)
VALUES (:identity_key, :user_id, 'stripe', :checkout_id)
ON CONFLICT (identity_key) DO NOTHING;
-- No row inserted: this person had a trial. Create the checkout without one.
```

- The `guard-signups` skill builds the identity key and the signals behind it. A key on the account id alone is no limit: a second account is free.
- Require a payment method for a trial unless the user decides otherwise. Stripe's `trial_settings.end_behavior.missing_payment_method` decides what happens at the end without one (`create_invoice` is the default, `cancel` and `pause` end access). Paddle's free and paid trials require payment details; its card-less trials are in early access and are canceled when the trial ends without payment details.
- A trial grants the plan's access until the trial end, and the plan's credits only if the user decided so. Free credits in a trial are what farmed accounts come for; the default is a smaller trial allowance or none.
- A trial that ends without payment ends access at the stored trial end, without waiting for an event.
- Stripe now labels `trial_end` and `trial_period_days` as legacy and recommends its trial offers, which need API version `2026-09-30.endive` or later and flexible billing mode. Either way the app's claim comes first.

## Sources

- https://docs.stripe.com/api/invoices/object
- https://docs.stripe.com/api/invoice-line-item/object
- https://docs.stripe.com/billing/subscriptions/webhooks
- https://docs.stripe.com/billing/subscriptions/trials
- https://docs.stripe.com/billing/subscriptions/trials/free-trials
- https://developer.apple.com/documentation/appstoreserverapi/offertype
- https://developer.apple.com/documentation/appstoreserverapi/offerdiscounttype
- https://developer.apple.com/documentation/appstoreserverapi/weborderlineitemid
- https://developer.apple.com/help/app-store-connect/manage-subscriptions/set-up-introductory-offers-for-auto-renewable-subscriptions
- https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2
- https://developer.android.com/google/play/billing/subscriptions
- https://developer.android.com/google/play/billing/integrate
- https://developer.paddle.com/webhooks/transactions/transaction-completed
- https://developer.paddle.com/concepts/subscriptions/trials
- https://developer.paddle.com/build/subscriptions/cardless-trials
- https://www.revenuecat.com/docs/integrations/webhooks/event-types-and-fields

Checked 2026-11-16.
