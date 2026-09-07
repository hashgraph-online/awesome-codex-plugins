---
name: refunds-and-disputes
description: Guide for issuing refunds, handling disputes and chargebacks, and reconciling customer access with Dodo Payments
---

# Refunds and Disputes

This skill covers issuing refunds (full and partial), handling the dispute lifecycle, and managing customer access during payment reversals. Disputes are inbound-only; Dodo handles the card-network process as Merchant of Record while you control application access and evidence gathering.

## When to use this skill

- You need to issue a refund (full or partial) for a payment
- A customer disputes a charge and you need to respond with evidence
- You're building access-revocation logic tied to refund or dispute status
- You need to reconcile customer entitlements after a payment reversal
- You're handling refund or dispute webhooks in production

## Core concepts

**Refunds** are initiated by you via the API. Each refund has a status that tells you whether the money has actually left your account. Partial refunds target specific line items in the original payment.

**Disputes** are initiated by the customer's card network. You cannot create them; you only list and retrieve them. The dispute lifecycle spans seven events, each requiring different application actions.

**Amounts** are always in the smallest currency unit (cents for USD, paise for INR, etc.).

**Access revocation** means removing the customer's ability to use the product or service. On a dispute, you typically revoke access while it's open. Restore it only on `dispute.won`; all other outcomes keep access revoked until you reconcile them separately.

## Refunds

### Create a refund

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode',
});

// Full refund
const refund = await client.refunds.create({
  payment_id: 'pay_abc123',
});

console.log(refund.refund_id);
console.log(refund.status); // 'pending', 'succeeded', 'review', or 'failed'
```

### Partial refund by item

To refund only specific items from a payment, pass the `items` array with each item ID and the amount to refund in the smallest currency unit. Omit `amount` to refund the whole item:

```typescript
const partialRefund = await client.refunds.create({
  payment_id: 'pay_abc123',
  items: [
    { item_id: 'item_1', amount: 1000 },
    { item_id: 'item_2', amount: 2500 },
  ],
});
```

### Refund statuses

Each refund has one of four statuses:

| Status | Meaning | Your action |
|---|---|---|
| `pending` | Refund is processing; money hasn't left your account yet | Wait for a webhook or poll the refund status |
| `succeeded` | Money has been returned to the customer | Revoke access if the product is non-refundable; update your records |
| `review` | Refund is under review (rare) | Contact support; do not assume it will succeed |
| `failed` | Refund failed; money remains in your account | Investigate the failure; consider retrying or contacting the customer |

### List and retrieve refunds

```typescript
// List all refunds
const refunds = await client.refunds.list();

// Retrieve a specific refund
const refund = await client.refunds.retrieve('ref_xyz789');
console.log(refund.status);
```

### Handle refund webhooks

Webhook signature verification is covered in the `webhook-integration` skill. Always verify the signature before processing.

```typescript
import DodoPayments from 'dodopayments';
import express from 'express';

const app = express();
app.use(express.raw({ type: 'application/json' }));

// `environment` is a narrow union, but env vars are `string | undefined`.
// Narrow explicitly rather than casting, and default to test mode so a missing
// variable can never accidentally hit live.
const environment = process.env.DODO_PAYMENTS_ENVIRONMENT === 'live_mode' ? 'live_mode' : 'test_mode';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment,
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
});

app.post('/webhook', async (req, res) => {
  try {
    const event = client.webhooks.unwrap(req.body.toString(), {
      headers: {
        'webhook-id': req.headers['webhook-id'] as string,
        'webhook-signature': req.headers['webhook-signature'] as string,
        'webhook-timestamp': req.headers['webhook-timestamp'] as string,
      },
    });

    if (event.type === 'refund.succeeded') {
      const refund = event.data;
      // Refund succeeded; revoke access if needed
      await revokeCustomerAccess(refund.customer.customer_id);
      await updateRefundRecord(refund.refund_id, 'succeeded');
    }

    if (event.type === 'refund.failed') {
      const refund = event.data;
      // Refund failed; keep access active, alert support
      await logRefundFailure(refund.refund_id, refund.reason);
    }

    res.json({ received: true });
  } catch (error) {
    res.status(401).json({ error: 'Invalid signature' });
  }
});
```

## Disputes

### Retrieve disputes

Disputes are inbound-only. You cannot create them; you can only list and retrieve them.

```typescript
// List all disputes
const disputes = await client.disputes.list();

// Retrieve a specific dispute
const dispute = await client.disputes.retrieve('dis_abc123');
console.log(dispute.dispute_status);
console.log(dispute.amount); // in smallest currency unit
```

### Dispute lifecycle

A dispute moves through seven events. Each event requires a different action from your application:

| Event | Meaning | Your action |
|---|---|---|
| `dispute.opened` | Customer initiated a chargeback | Record the dispute; consider revoking access immediately; gather evidence from your logs |
| `dispute.challenged` | You submitted evidence | Wait for the card network to review |
| `dispute.accepted` | You accepted (conceded) the dispute; funds go to the cardholder | Keep access revoked; mark the dispute as accepted in your records |
| `dispute.cancelled` | Customer or system cancelled the dispute | Keep access revoked; reconcile the payment separately |
| `dispute.expired` | Dispute window closed without resolution | Treat as lost; keep access revoked |
| `dispute.won` | You won the dispute | Funds are retained; restore access; update customer records |
| `dispute.lost` | You lost the dispute | Funds returned to cardholder; keep access revoked; reconcile your records |

### Handle dispute webhooks

Webhook dispute payloads intentionally contain no customer field. Resolve the customer with an extra `disputes.retrieve()` call: the webhook's `dispute_id` identifies the dispute, and the returned `GetDispute` includes `customer`. Without this lookup, access-control handlers would receive `undefined`.

```typescript
async function resolveDisputeCustomerId(disputeId: string) {
  const dispute = await client.disputes.retrieve(disputeId);
  return dispute.customer.customer_id;
}

app.post('/webhook', async (req, res) => {
  try {
    const event = client.webhooks.unwrap(req.body.toString(), {
      headers: {
        'webhook-id': req.headers['webhook-id'] as string,
        'webhook-signature': req.headers['webhook-signature'] as string,
        'webhook-timestamp': req.headers['webhook-timestamp'] as string,
      },
    });

    if (event.type === 'dispute.opened') {
      const dispute = event.data;
      // Record the dispute and revoke access
      await recordDispute(dispute.dispute_id, dispute.payment_id, dispute.amount);
      const customerId = await resolveDisputeCustomerId(dispute.dispute_id);
      await revokeCustomerAccess(customerId);
      // Gather evidence from your system and submit via dashboard
      // (no evidence-submission API exists; use the Dodo dashboard)
    }

    if (event.type === 'dispute.won') {
      const dispute = event.data;
      // Funds retained; restore normal state
      await markDisputeResolved(dispute.dispute_id, 'won');
      const customerId = await resolveDisputeCustomerId(dispute.dispute_id);
      await restoreCustomerAccess(customerId);
    }

    if (event.type === 'dispute.lost') {
      const dispute = event.data;
      // Funds returned to cardholder; keep access revoked
      await markDisputeResolved(dispute.dispute_id, 'lost');
      // Do NOT restore access
    }

    if (event.type === 'dispute.accepted') {
      const dispute = event.data;
      // Merchant conceded; funds go to the cardholder and access stays revoked
      await markDisputeResolved(dispute.dispute_id, 'accepted');
      // Do NOT restore access
    }

    if (event.type === 'dispute.cancelled') {
      const dispute = event.data;
      // Cancellation is not a win; keep access revoked and reconcile separately
      await markDisputeResolved(dispute.dispute_id, 'cancelled');
    }

    res.json({ received: true });
  } catch (error) {
    res.status(401).json({ error: 'Invalid signature' });
  }
});
```

### Evidence submission

Dodo handles the card-network dispute process as Merchant of Record. You submit evidence through the Dodo dashboard, not via API. No evidence-submission API exists.

When a dispute opens, gather your evidence (order confirmation, delivery proof, customer communication, etc.) and upload it to the dashboard within the dispute window (typically 4 days). The card network reviews your evidence and makes a final decision.

## Access revocation pattern

A common pattern for managing access during disputes:

```typescript
async function handleDisputeLifecycle(
  dispute: Awaited<ReturnType<typeof client.disputes.retrieve>>,
) {
  const customerId = dispute.customer.customer_id;

  switch (dispute.dispute_status) {
    case 'dispute_opened':
      // Revoke access immediately
      await revokeCustomerAccess(customerId);
      break;

    case 'dispute_won':
      // You won; restore access
      await restoreCustomerAccess(customerId);
      break;

    case 'dispute_lost':
      // You lost; keep access revoked
      // (do nothing)
      break;

    case 'dispute_accepted':
      // You conceded; funds go to the cardholder and access stays revoked
      break;

    case 'dispute_cancelled':
      // Cancellation is not a win; reconcile separately and keep access revoked
      break;

    case 'dispute_expired':
      // Treat as lost; keep access revoked
      break;

    case 'dispute_challenged':
      // Evidence is under review; keep access revoked
      break;
  }
}
```

## Reconciling entitlements after refund

When a refund succeeds, you must reconcile the customer's access. If the product is non-refundable (e.g., a digital download or subscription already used), revoke access. If it's refundable (e.g., a subscription not yet started), you may restore access or leave it revoked depending on your policy.

```typescript
async function reconcileRefund(refund) {
  if (refund.status !== 'succeeded') {
    return; // Not yet final
  }

  const payment = await client.payments.retrieve(refund.payment_id);
  const customer = payment.customer;

  // Revoke access for non-refundable products
  const includesNonRefundableProduct = payment.product_cart?.some(({ product_id }) =>
    isNonRefundable(product_id),
  );

  if (includesNonRefundableProduct) {
    await revokeCustomerAccess(customer.customer_id);
  }

  // Update your entitlement records
  await updateEntitlementRecord(customer.customer_id, {
    refund_id: refund.refund_id,
    refund_amount: refund.amount,
    refund_date: new Date(),
  });
}
```

## Common mistakes

**Auto-refunding without revoking access.** A refund webhook means money is leaving your account. If the product is non-refundable, revoke access immediately. Don't wait for the customer to ask.

**Treating `dispute.opened` as final.** A dispute is not lost until the card network says so. Keep access revoked while it's open, but don't delete customer data or close their account.

**Ignoring partial refunds when computing entitlements.** If a customer refunds only one item from a multi-item purchase, their entitlement to the other items remains valid. Track refunds by item, not just by payment.

**Restoring access on any outcome except `dispute.won`.** `dispute.accepted` means you conceded and the cardholder receives the funds. A cancelled dispute is also not a win. Keep access revoked and reconcile separately unless you receive `dispute.won`.

**Submitting evidence after the dispute window closes.** The card network typically gives you 4 days to respond. Set a calendar reminder and gather evidence immediately when a dispute opens.

**Assuming Dodo will handle access revocation.** Dodo handles the card-network process; you handle application access. Dodo won't revoke your customer's subscription or file access automatically.

## Resources

- [Refunds API](https://docs.dodopayments.com/api-reference/refunds/post-refunds)
- [Refunds feature guide](https://docs.dodopayments.com/features/transactions/refunds)
- [Dispute webhooks](https://docs.dodopayments.com/developer-resources/webhooks/intents/dispute)
- [Webhook integration skill](../webhook-integration/) for signature verification
