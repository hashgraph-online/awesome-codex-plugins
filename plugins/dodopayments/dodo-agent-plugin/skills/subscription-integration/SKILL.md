---
name: subscription-integration
description: Guide for managing recurring subscriptions after checkout, including trials, lifecycle states, plan changes, cancellation, failed-payment recovery, proration, mandates, and on-demand charges.
---

# Dodo Payments Subscription Integration

Implement recurring billing with trials, plan changes, and on-demand charging. Subscriptions are created through Checkout Sessions, managed via the subscriptions API, and monitored through webhooks.

## When to use this skill

- Building a subscription product with recurring billing and trials
- Handling plan upgrades, downgrades, and migrations mid-cycle
- Implementing on-demand/off-session charging with mandates
- Managing failed payments and dunning recovery
- Building a customer self-service portal for subscription management

---

## Core Concepts

**Subscription lifecycle:** The six subscription statuses are `pending`, `active`, `on_hold`, `cancelled`, `failed`, and `expired`. A trialing subscription reports `active`; `subscription.renewed` is an event, not a status. Failed payments can move a subscription to `on_hold` (recoverable) or `failed` (terminal). Cancellation sets it to `cancelled` or schedules it to become `expired` at period end.

**Checkout Sessions:** The recommended path for creating subscriptions. A single-use hosted checkout that collects payment and customer data, then creates the subscription server-side.

**Proration:** When a customer changes plans mid-cycle, Dodo calculates credits or charges based on the time remaining. Proration mode controls whether the customer is billed immediately, credited, or neither.

**Mandates:** Authorization to charge a customer's payment method repeatedly (for subscriptions) or on-demand (for usage-based billing). Created during Checkout, can be updated if payment fails.

---

## Creating a Subscription

### Via Checkout Session (Recommended)

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode',
});

const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_monthly_plan', quantity: 1 }
  ],
  subscription_data: {
    trial_period_days: 14, // Optional
  },
  customer: {
    email: 'subscriber@example.com',
    name: 'Jane Doe',
  },
  return_url: 'https://yoursite.com/success',
});

// Redirect user to session.checkout_url
console.log('Redirect to:', session.checkout_url);
```

The customer completes payment on the hosted checkout. On success, Dodo creates the subscription and fires the `subscription.active` webhook.

### With Add-ons

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [
    {
      product_id: 'pdt_pro_monthly',
      quantity: 1,
      addons: [
        { addon_id: 'adn_extra_seats', quantity: 3 }
      ]
    }
  ],
  subscription_data: {
    trial_period_days: 7,
  },
  customer: { email: 'user@example.com' },
  return_url: 'https://yoursite.com/success',
});
```

---

## Subscription Lifecycle & Status

| Status | Meaning | Transitions |
|--------|---------|-----------|
| `pending` | Creation in progress | → `active`, `failed` |
| `active` | Actively renewing | → `on_hold`, `cancelled`, `expired` |
| `on_hold` | Renewal/plan-change payment failed; recoverable | → `active` (payment method updated), `failed` (retries exhausted), `cancelled` |
| `cancelled` | Will not renew | → `expired` (at period end) |
| `failed` | Initial mandate/payment failed; terminal | (no recovery) |
| `expired` | Subscription term ended | (terminal) |

**Trial period:** If `trial_period_days` is set, the subscription enters `active` immediately but charges nothing until the trial ends. The first charge occurs on the trial end date.

---

## Subscription Methods

### Retrieve

```typescript
const subscription = await client.subscriptions.retrieve('sub_xxxxx');
console.log(subscription.status, subscription.next_billing_date);
```

### Update Payment Method

When a subscription is `on_hold` due to failed payment, the customer can update their payment method. This automatically charges any outstanding dues.

```typescript
await client.subscriptions.updatePaymentMethod('sub_xxxxx', {
  payment_method: {
    type: 'existing',
    payment_method_id: 'pm_new_method',
  },
});
```

Success emits `payment.succeeded` followed by `subscription.active`.

### List Usage History (Metered Subscriptions)

```typescript
const history = await client.subscriptions.retrieveUsageHistory('sub_xxxxx', {
  page_size: 50,
  page_number: 0,
});
```

### Retrieve Credit Usage

```typescript
const creditUsage = await client.subscriptions.retrieveCreditUsage('sub_xxxxx');
console.log('Subscription:', creditUsage.subscription_id);

for (const item of creditUsage.items) {
  console.log(item.credit_entitlement_name, item.balance); // balance is a string
}
```

---

## Plan Changes (Upgrades & Downgrades)

### Change Plan

```typescript
await client.subscriptions.changePlan('sub_xxxxx', {
  product_id: 'pdt_higher_tier',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
  on_payment_failure: 'prevent_change',
});
```

**Proration modes:**

| Mode | Upgrade | Downgrade | Billing date |
|------|---------|-----------|--------------|
| `prorated_immediately` | Time-prorated charge | Time-prorated credit | Resets to change date |
| `difference_immediately` | Full new-plan charge | Difference becomes credit | Resets |
| `full_immediately` | Full new-plan charge | Full new-plan charge, no credit | Resets |
| `do_not_bill` | No charge | No credit | Preserved |

**Payment failure handling:**

- `prevent_change`: Keep the old plan if the charge fails.
- `apply_change`: Apply the new plan even if payment fails (subscription may become `on_hold`).

### Preview Plan Change

Show the customer a quote before committing:

```typescript
const preview = await client.subscriptions.previewChangePlan('sub_xxxxx', {
  product_id: 'pdt_new_plan',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
});

console.log('Effective at:', preview.immediate_charge.effective_at);
console.log('Line items:', preview.immediate_charge.line_items);
console.log('Summary:', preview.immediate_charge.summary);
console.log('New plan:', preview.new_plan);
```

### Cancel a Scheduled Plan Change

```typescript
await client.subscriptions.cancelChangePlan('sub_xxxxx');
```

---

## Cancellation

### Immediate Cancellation

```typescript
await client.subscriptions.update('sub_xxxxx', {
  status: 'cancelled',
});
```

Access is revoked immediately.

### Cancel at Period End

```typescript
await client.subscriptions.update('sub_xxxxx', {
  cancel_at_next_billing_date: true,
});
```

The subscription remains `active` until the next billing date, then transitions to `expired`. The `subscription.cancelled` webhook includes `cancel_at_next_billing_date: true` and `next_billing_date` so you know when to revoke access.

---

## On-Demand (Off-Session) Charging

For usage-based or metered subscriptions, charge the customer on-demand without a scheduled renewal.

### Create Subscription with Mandate

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_usage_based', quantity: 1 }
  ],
  subscription_data: {
    on_demand: {
      mandate_only: true,
    }
  },
  customer: { email: 'user@example.com' },
  return_url: 'https://yoursite.com/success',
});
```

This creates a subscription with a mandate but no automatic renewal. You control when to charge.

### Charge On-Demand

```typescript
const charge = await client.subscriptions.charge('sub_xxxxx', {
  product_price: 2500, // $25.00 in cents
  product_currency: 'USD',
  product_description: 'API calls for January 2025',
});

console.log('Payment ID:', charge.payment_id);
```

Amounts are in the smallest currency unit (cents for USD, paise for INR, etc.).

**Dodo does not automatically retry on-demand charges.** You own retry logic and decline filtering. Monitor `payment.failed` webhooks and implement your own retry strategy.

---

## Failed Payments & Recovery

### On-Hold Subscriptions

When a renewal or plan-change charge fails, the subscription moves to `on_hold`. This is recoverable.

```typescript
// Listen for subscription.on_hold webhook
case 'subscription.on_hold':
  // Notify customer, offer payment method update
  await sendPaymentFailedEmail(data.customer.customer_id);
  break;
```

### Recovery Options

1. **Payment Retries:** Opt-in under Settings → Recovery. Dodo retries failed renewals up to 8 times over a configurable 1–30 day window (default 13 days). Only for soft declines.

2. **Customer Portal:** Customer updates payment method → automatic charge for outstanding dues → `subscription.active`.

3. **Manual Charge:** You update the payment method server-side, then call `updatePaymentMethod()`.

### Dunning

Dunning sends up to four configurable emails for `on_hold` renewals and customer-portal cancellations. Exhausted dunning does not change the subscription state; you must handle the final outcome.

---

## Customer Portal

Allow customers to self-serve: view subscriptions, update payment methods, cancel, and upgrade/downgrade.

```typescript
const portalSession = await client.customers.customerPortal.create(
  'cus_xxxxx',
  { return_url: 'https://yoursite.com/account' }
);

// Redirect to portalSession.link
```

Portal links expire after 24 hours. Customers can:
- View subscription details and renewal dates
- Cancel immediately or at period end
- Upgrade/downgrade within enabled Product Collections
- Update payment methods and reactivate `on_hold` subscriptions
- View billing history and download invoices

For full customer management (creating, updating, listing), see the `customer-management` skill.

---

## Webhook Events

| Event | When | Action |
|-------|------|--------|
| `subscription.active` | Subscription becomes active, including a trial start or recovery | Grant access |
| `subscription.renewed` | Successful renewal | Log renewal, send receipt |
| `subscription.on_hold` | Renewal/plan-change payment failed | Notify customer, offer recovery |
| `subscription.plan_changed` | Plan upgraded/downgraded or add-ons changed | Update entitlements |
| `subscription.cancelled` | Customer cancels | Schedule access revocation per `cancel_at_next_billing_date` |
| `subscription.failed` | Initial mandate/payment failed | Notify customer, offer retry or new subscription |
| `subscription.expired` | Subscription term ended | Revoke access |

Webhook signature verification, raw-body handling, durable processing, and idempotency are covered in the `webhook-integration` skill.

### Example Handler

```typescript
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const raw = await req.text();
  const headers = Object.fromEntries(req.headers.entries());
  const event = await client.webhooks.unwrap(raw, { headers });
  const webhookId = req.headers.get('webhook-id');

  if (!webhookId) {
    return NextResponse.json({ error: 'Missing webhook-id' }, { status: 400 });
  }

  // Implement this as an atomic insert backed by a UNIQUE constraint.
  // Keep the claim and entitlement changes in the same database transaction.
  const claimed = await claimWebhookId(webhookId);
  if (!claimed) {
    return NextResponse.json({ received: true });
  }

  switch (event.type) {
    case 'subscription.active':
      await grantAccess(event.data.customer.customer_id, event.data.product_id);
      break;
    case 'subscription.on_hold':
      await notifyPaymentFailed(event.data.customer.customer_id);
      break;
    case 'subscription.cancelled':
      if (event.data.cancel_at_next_billing_date) {
        await scheduleAccessRevocation(event.data.subscription_id, new Date(event.data.next_billing_date));
      } else {
        await revokeAccessImmediately(event.data.subscription_id);
      }
      break;
    case 'subscription.expired':
      await revokeAccess(event.data.customer.customer_id);
      break;
  }

  return NextResponse.json({ received: true });
}
```

---

## Credit Entitlements

Attach credit entitlements to subscription products to grant credits each billing cycle. For full credit management, see the `credit-based-billing` skill.

Quick example:

```typescript
// Product has credit entitlement attached (e.g., 10,000 tokens/month)
const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_pro_with_credits', quantity: 1 }
  ],
  subscription_data: {
    trial_period_days: 14,
  },
  customer: { email: 'user@example.com' },
  return_url: 'https://yoursite.com/success',
});
```

On each renewal, credits are issued. Monitor `credit.added` and `credit.deducted` webhooks to sync your ledger.

---

## Common Mistakes

### 1. Granting Access on `return_url` Instead of Webhook

**Wrong:**
```typescript
// On return_url redirect
await grantAccess(user.id);
```

The `return_url` is hit before the subscription is fully created. Dodo may still be processing the mandate or payment. Always wait for `subscription.active` webhook.

**Right:**
```typescript
// In webhook handler
case 'subscription.active':
  await grantAccess(data.customer.customer_id);
  break;
```

### 2. Using Deprecated `subscriptions.create`

**Wrong:**
```typescript
const sub = await client.subscriptions.create({
  product_id: 'pdt_monthly',
  customer_id: 'cus_xxxxx',
});
```

This endpoint is deprecated. Use Checkout Sessions.

**Right:**
```typescript
const session = await client.checkoutSessions.create({
  product_cart: [{ product_id: 'pdt_monthly', quantity: 1 }],
  customer: { customer_id: 'cus_xxxxx' },
  return_url: 'https://yoursite.com/success',
});
```

### 3. Misinterpreting `subscription.plan_changed`

`subscription.plan_changed` fires for upgrades, downgrades, add-on changes, AND when `cancel_at_next_billing_date` is toggled. Don't assume every `plan_changed` event means a paid upgrade succeeded. Inspect the payload and check the subscription's current `product_id`.

### 4. Forgetting Proration Mode

**Wrong:**

```typescript
// Missing proration_billing_mode
await client.subscriptions.changePlan('sub_xxxxx', {
  product_id: 'pdt_new',
  quantity: 1,
  // proration_billing_mode: 'prorated_immediately', // REQUIRED
});
```

This will fail. Always specify a proration mode.

### 5. Confusing `on_hold` with Pause

`on_hold` means payment failed, not that the customer paused. There is no general pause/resume operation. `on_hold` is recoverable only by updating the payment method or waiting for retry.

### 6. Not Handling `cancel_at_next_billing_date`

```typescript
// Wrong: revoke immediately
await revokeAccess(data.customer.customer_id);

// Right: check the flag
if (data.cancel_at_next_billing_date) {
  await scheduleAccessRevocation(data.subscription_id, new Date(data.next_billing_date));
} else {
  await revokeAccessImmediately(data.subscription_id);
}
```

---

## Resources

- [Subscription Integration Guide](https://docs.dodopayments.com/developer-resources/subscription-integration-guide)
- [Upgrade & Downgrade Guide](https://docs.dodopayments.com/developer-resources/subscription-upgrade-downgrade)
- [On-Demand Subscriptions](https://docs.dodopayments.com/developer-resources/ondemand-subscriptions)
- [Subscription Webhooks](https://docs.dodopayments.com/developer-resources/webhooks/intents/subscription)
- [Customer Portal](https://docs.dodopayments.com/features/customer-portal)
- [Subscription Payment Retries](https://docs.dodopayments.com/features/recovery/payment-retries)
- [Subscription Dunning](https://docs.dodopayments.com/features/recovery/subscription-dunning)
