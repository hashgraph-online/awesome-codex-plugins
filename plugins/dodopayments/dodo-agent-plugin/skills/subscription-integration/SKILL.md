---
name: subscription-integration
description: Dodo Payments subscription lifecycle after checkout, covering trials, statuses like active, on_hold, and cancelled, plan upgrades and downgrades, proration, cancellation, failed-payment recovery, mandates, and on-demand charges. Use when managing recurring billing, plan changes, dunning, or off-session charging; use checkout-integration to start the purchase.
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

**Subscription lifecycle:** The eight subscription statuses are `pending`, `active`, `past_due`, `on_hold`, `paused`, `cancelled`, `failed`, and `expired`. A trialing subscription reports `active`; `subscription.renewed` is an event, not a status. A failed renewal moves a subscription to `past_due` (only if you configured a grace period; access is kept) or `on_hold` (access revoked); both are recoverable. `paused` is a deliberate freeze by you or the customer. `failed` is terminal and only happens when **initial creation** fails. Cancellation sets it to `cancelled` or schedules it to become `expired` at period end.

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
| `active` | Actively renewing | → `past_due`, `on_hold`, `paused`, `cancelled`, `expired` |
| `past_due` | Renewal failed and the grace period is open; customer **keeps** access until `past_due_ends_at` | → `active` (debt settled), `on_hold` or `cancelled` (grace period ends, per your setting) |
| `on_hold` | Renewal/plan-change payment failed; renewals stopped, access revoked; recoverable | → `active` (payment method updated / retry succeeds), `cancelled` |
| `paused` | Deliberately paused by you or the customer; billing frozen, access revoked | → `active` (resumed), `cancelled` |
| `cancelled` | Will not renew | → `expired` (at period end) |
| `failed` | Initial mandate/payment failed at creation; terminal. Never reached from `on_hold` or exhausted retries | (no recovery) |
| `expired` | Subscription term ended | (terminal) |

`past_due` only occurs if you enable a grace period; without one, a failed renewal goes straight to `on_hold`.

**Trial period:** If `trial_period_days` is set, the subscription enters `active` immediately but charges nothing until the trial ends. The first charge occurs on the trial end date.

---

## Subscription Methods

### Retrieve

```typescript
const subscription = await client.subscriptions.retrieve('sub_xxxxx');
console.log(subscription.status, subscription.next_billing_date);
```

### Pause and Resume

Pause and resume run through `status` on the update endpoint. Send it on its own: combining `paused`/`active` with any other field is rejected with `422`.

```typescript
// Pause: renewals stop, access is revoked, next_billing_date shifts by the pause length
await client.subscriptions.update('sub_xxxxx', { status: 'paused' });

// Resume
await client.subscriptions.update('sub_xxxxx', { status: 'active' });
```

Pausing emits `subscription.paused`; resuming emits `subscription.unpaused`. Customer self-service pause in the portal is opt-in (**Settings → Subscriptions → Allow Subscription Pause**).

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
| `prorated_immediately` | Credit for unused time on the old plan, then charge a **full** new cycle (net = full new cycle − unused credit) | Same formula; a credit only remains if the unused credit exceeds the new plan price | Resets to change date |
| `difference_immediately` | Full new-plan charge | Difference becomes credit | Resets |
| `full_immediately` | Full new-plan charge | Full new-plan charge, no credit | Resets |
| `do_not_bill` | No charge | No credit | Preserved |

**Payment failure handling:**

- `prevent_change`: Keep the old plan if the charge fails.
- `apply_change`: Apply the new plan even if payment fails (subscription may become `on_hold`).

**Scheduling:** `effective_at` defaults to `'immediately'`. Pass `effective_at: 'next_billing_date'` to schedule the change (typical for downgrades) - nothing is charged now, the customer keeps the current plan until the period ends, and the pending change appears on the subscription as `scheduled_change` (cancel it with `cancelChangePlan`).

```typescript
await client.subscriptions.changePlan('sub_xxxxx', {
  product_id: 'pdt_lower_tier',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
  effective_at: 'next_billing_date',
});
```

**Plan changes are rejected while the subscription is `past_due`.** Settle the renewal debt first.

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

Full guide: [references/webhook-events.md](references/webhook-events.md).

Covers:

- Example Handler

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

### 5. Confusing `on_hold` with `paused`

`on_hold` is involuntary: a payment failed, and it is recovered by updating the payment method or a successful retry. `paused` is deliberate: you or the customer froze the subscription with `subscriptions.update(id, { status: 'paused' })`, and it is resumed with `{ status: 'active' }`. Handle `subscription.paused`/`subscription.unpaused` separately from `subscription.on_hold`.

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

- [Subscriptions (states, pause, grace period)](https://docs.dodopayments.com/features/subscription)
- [Subscription Integration Guide](https://docs.dodopayments.com/developer-resources/subscription-integration-guide)
- [Upgrade & Downgrade Guide](https://docs.dodopayments.com/developer-resources/subscription-upgrade-downgrade)
- [On-Demand Subscriptions](https://docs.dodopayments.com/developer-resources/ondemand-subscriptions)
- [Subscription Webhooks](https://docs.dodopayments.com/developer-resources/webhooks/intents/subscription)
- [Customer Portal](https://docs.dodopayments.com/features/customer-portal)
- [Subscription Payment Retries](https://docs.dodopayments.com/features/recovery/payment-retries)
- [Subscription Dunning](https://docs.dodopayments.com/features/recovery/subscription-dunning)
