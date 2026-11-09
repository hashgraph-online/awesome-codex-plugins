# Subscriptions

## Contents

- [Start a subscription](#start-a-subscription)
- [Statuses](#statuses)
- [Subscription webhooks](#subscription-webhooks)
- [Plan changes](#plan-changes)
- [Pause, resume and cancel](#pause-resume-and-cancel)
- [Failed payments and recovery](#failed-payments-and-recovery)
- [On-demand charges](#on-demand-charges)
- [Read a subscription](#read-a-subscription)
- [Common mistakes](#common-mistakes)

## Start a subscription

Create a checkout session for a subscription product ([checkout.md](checkout.md)). Dodo creates the subscription when the customer pays and sends `subscription.active`. Grant access on that webhook.

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [{ product_id: 'pdt_pro_monthly', quantity: 1 }],
  subscription_data: { trial_period_days: 14 }, // optional
  customer: { email: 'subscriber@example.com' },
  return_url: 'https://example.com/billing/success',
});
```

A trialing subscription is `active` from the start; the first charge happens when the trial ends. Credits attached to the product are issued every cycle ([credits.md](credits.md)).

## Statuses

| Status | Meaning | Access |
|---|---|---|
| `pending` | Being created | No |
| `active` | Renewing normally, including during a trial | Yes |
| `past_due` | A renewal failed and your grace period is open (`past_due_ends_at`). Only happens if you enabled a grace period | Yes |
| `on_hold` | A renewal or plan-change charge failed; renewals stopped. Recoverable | No |
| `paused` | Paused on purpose by you or the customer | No |
| `cancelled` | Cancelled; will not renew | No, or until period end (see below) |
| `failed` | The first mandate or payment failed at creation. Terminal | No |
| `expired` | The term ended. Terminal | No |

## Subscription webhooks

| Webhook | Action |
|---|---|
| `subscription.active` | Grant access (new subscription, trial start, or recovery) |
| `subscription.renewed` | Record the renewal and the new `next_billing_date` |
| `subscription.updated` | Sync your stored copy |
| `subscription.plan_changed` | Re-read `product_id` and update the plan. Also fires for add-on changes and for toggling `cancel_at_next_billing_date` |
| `subscription.past_due` | Keep access, ask for payment before `past_due_ends_at` |
| `subscription.on_hold` | Remove access, ask the customer to update the payment method |
| `subscription.paused` / `subscription.unpaused` | Remove / restore access |
| `subscription.update_payment_method` | Sync the payment method |
| `subscription.cancelled` | If `cancel_at_next_billing_date`, revoke at `next_billing_date`; otherwise revoke now |
| `subscription.failed` | Tell the customer the subscription could not start |
| `subscription.expired` | Revoke access |

Verify and deduplicate as in [webhooks.md](webhooks.md). Webhooks can arrive out of order, so for pause and resume re-read the subscription and apply its current status:

```typescript
import DodoPayments from 'dodopayments';

// Called with the verified webhook from your handler.
export async function handleSubscriptionWebhook(event: DodoPayments.UnwrapWebhookEvent) {
  switch (event.type) {
    case 'subscription.active':
      await grantAccess(event.data.customer.customer_id, event.data.product_id);
      break;
    case 'subscription.paused':
    case 'subscription.unpaused': {
      const current = await client.subscriptions.retrieve(event.data.subscription_id);
      if (current.status === 'paused') await revokeAccess(current.subscription_id);
      else if (current.status === 'active' || current.status === 'past_due') {
        await grantAccess(current.customer.customer_id, current.product_id);
      }
      break;
    }
    case 'subscription.cancelled':
      if (event.data.cancel_at_next_billing_date) {
        await scheduleRevocation(event.data.subscription_id, new Date(event.data.next_billing_date));
      } else {
        await revokeAccess(event.data.subscription_id);
      }
      break;
    case 'subscription.on_hold':
    case 'subscription.expired':
      await revokeAccess(event.data.subscription_id);
      break;
  }
}
```

## Plan changes

Preview the charge, show it to the customer, then change the plan. `proration_billing_mode` is required.

```typescript
const preview = await client.subscriptions.previewChangePlan('sub_xxxxx', {
  product_id: 'pdt_business_monthly',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
});
console.log(preview.immediate_charge.summary, preview.new_plan);

await client.subscriptions.changePlan('sub_xxxxx', {
  product_id: 'pdt_business_monthly',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
  on_payment_failure: 'prevent_change', // keep the old plan if the charge fails
});
```

Default: `prorated_immediately` for upgrades. For downgrades, schedule the change for the end of the period with `effective_at: 'next_billing_date'`; nothing is charged now and the pending change appears as `scheduled_change` (undo it with `client.subscriptions.cancelChangePlan('sub_xxxxx')`).

| `proration_billing_mode` | Effect | Billing date |
|---|---|---|
| `prorated_immediately` | Credit for unused time on the old plan, then charge a full new cycle | Resets |
| `difference_immediately` | Charge or credit the price difference | Resets |
| `full_immediately` | Charge the full new price, no credit | Resets |
| `do_not_bill` | No charge, no credit | Kept |

- `on_payment_failure: 'apply_change'` applies the new plan even if the charge fails; the subscription can go `on_hold`.
- Plan changes are rejected while the subscription is `past_due`.
- `discount_codes` on `changePlan` replaces existing discounts; see [discounts.md](discounts.md).
- Changing a product's price does not move existing subscribers. Use `changePlan` for each one.

## Pause, resume and cancel

```typescript
// Pause and resume: send status on its own; combining it with other fields returns 422.
await client.subscriptions.update('sub_xxxxx', { status: 'paused' });
await client.subscriptions.update('sub_xxxxx', { status: 'active' });

// Default cancellation: at the end of the paid period. Stays active, then becomes expired.
await client.subscriptions.update('sub_xxxxx', { cancel_at_next_billing_date: true });

// Immediate cancellation (confirm with the user first in live mode).
await client.subscriptions.update('sub_xxxxx', { status: 'cancelled' });
```

Customers can do all of this themselves in the customer portal ([customers.md](customers.md)); self-service pause must be enabled in the dashboard.

## Failed payments and recovery

- A failed renewal moves the subscription to `past_due` (with a grace period) or `on_hold`.
- **Payment retries** (opt-in, Settings > Recovery) retry soft declines up to 8 times over a configurable window.
- **Dunning** emails the customer for `on_hold` renewals. It never changes the subscription status by itself.
- The customer recovers through the customer portal, or you attach a saved method on the server. Both charge the dues and send `payment.succeeded` then `subscription.active`:

```typescript
await client.subscriptions.updatePaymentMethod('sub_xxxxx', {
  payment_method: { type: 'existing', payment_method_id: 'pm_new_method' },
});
```

## On-demand charges

For billing you trigger yourself, create a mandate-only subscription, then charge it. Dodo does not retry on-demand charges; handle `payment.failed` yourself.

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [{ product_id: 'pdt_on_demand', quantity: 1 }],
  subscription_data: { on_demand: { mandate_only: true } },
  customer: { email: 'customer@example.com' },
  return_url: 'https://example.com/billing/success',
});

const charge = await client.subscriptions.charge('sub_xxxxx', {
  product_price: 2500, // USD 25.00
  product_currency: 'USD',
  product_description: 'Usage for March',
});
console.log(charge.payment_id);
```

For per-unit pricing that Dodo meters and bills each cycle, use [usage-billing.md](usage-billing.md) instead.

## Read a subscription

```typescript
const subscription = await client.subscriptions.retrieve('sub_xxxxx');
console.log(subscription.status, subscription.next_billing_date);

for await (const period of client.subscriptions.retrieveUsageHistory('sub_xxxxx')) {
  console.log(period); // metered usage per billing period
}

const creditUsage = await client.subscriptions.retrieveCreditUsage('sub_xxxxx');
console.log(creditUsage.items);
```

## Common mistakes

- Granting access on `return_url` instead of `subscription.active`.
- Treating every `subscription.plan_changed` as a paid upgrade. Re-read the subscription.
- Revoking access at once on `subscription.cancelled` when `cancel_at_next_billing_date` is true.
- Handling `on_hold` (payment failed) and `paused` (deliberate) the same way.
- Omitting `proration_billing_mode` on `changePlan`.
