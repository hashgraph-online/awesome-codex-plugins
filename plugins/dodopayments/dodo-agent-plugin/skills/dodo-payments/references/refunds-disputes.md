# Refunds and disputes

## Contents

- [Issue a refund](#issue-a-refund)
- [Refund statuses and webhooks](#refund-statuses-and-webhooks)
- [Disputes](#disputes)
- [Dispute webhooks](#dispute-webhooks)
- [Common mistakes](#common-mistakes)

Dodo, as Merchant of Record, moves the money and runs the card-network dispute process. Your app decides who keeps access. A refund is a live-mode write: confirm the payment ID and amount with the user first.

## Issue a refund

```typescript
// Full refund
const refund = await client.refunds.create({ payment_id: 'pay_abc123' });
console.log(refund.refund_id, refund.status);

// Partial refund by line item. Omit amount to refund the whole item.
const partial = await client.refunds.create({
  payment_id: 'pay_abc123',
  items: [{ item_id: 'item_1' }, { item_id: 'item_2', amount: 2500 }],
});
```

Read the refundable items first with `client.payments.retrieveLineItems('pay_abc123')`. If a refund call errors or times out, list the payment's refunds before retrying, so the customer is not refunded twice.

## Refund statuses and webhooks

| `status` | Meaning |
|---|---|
| `pending` | Processing; the money has not left yet |
| `succeeded` | Returned to the customer |
| `review` | Under review; do not assume success |
| `failed` | Not refunded |

Act on the verified webhook ([webhooks.md](webhooks.md)):

```typescript
import DodoPayments from 'dodopayments';

export async function handleRefundWebhook(event: DodoPayments.UnwrapWebhookEvent) {
  if (event.type === 'refund.succeeded') {
    const refund = event.data;
    if (!refund.is_partial) {
      await revokeCustomerAccess(refund.customer.customer_id);
    } else {
      // Remove access only for items with nothing left to refund.
      const { items } = await client.payments.retrieveLineItems(refund.payment_id);
      const fullyRefunded = items.filter((item) => item.refundable_amount === 0).map((item) => item.items_id);
      await revokeItemAccess(refund.customer.customer_id, fullyRefunded);
    }
  }
  if (event.type === 'refund.failed') {
    await alertSupport(event.data.refund_id, event.data.reason); // keep access
  }
}
```

License keys from a refunded one-time payment are disabled by Dodo; see [license-keys.md](license-keys.md).

## Disputes

Customers open disputes through their card network. You can only read them, and you submit evidence in the dashboard (there is no evidence API) within 10 days of the dispute opening.

```typescript
const dispute = await client.disputes.retrieve('dis_abc123');
console.log(dispute.dispute_status, dispute.amount, dispute.customer.customer_id);

for await (const item of client.disputes.list()) {
  console.log(item.dispute_id, item.dispute_status);
}
```

## Dispute webhooks

| Webhook | Access |
|---|---|
| `dispute.opened` | Revoke while open; gather evidence |
| `dispute.challenged` | Keep revoked; evidence under review |
| `dispute.won` | Restore |
| `dispute.cancelled` | Restore; the customer withdrew it |
| `dispute.accepted`, `dispute.lost`, `dispute.expired` | Keep revoked |

Dispute webhook payloads have no customer field. Read the dispute to find the customer:

```typescript
async function customerForDispute(disputeId: string) {
  const dispute = await client.disputes.retrieve(disputeId);
  return dispute.customer.customer_id;
}

export async function handleDisputeWebhook(event: DodoPayments.UnwrapWebhookEvent) {
  if (event.type === 'dispute.opened') {
    await revokeCustomerAccess(await customerForDispute(event.data.dispute_id));
  }
  if (event.type === 'dispute.won' || event.type === 'dispute.cancelled') {
    await restoreCustomerAccess(await customerForDispute(event.data.dispute_id));
  }
}
```

## Common mistakes

- Refunding without deciding on access. Revoke access for a full refund of a non-refundable product.
- Revoking access to every item on a partial refund.
- Restoring access on `dispute.accepted`, `dispute.lost` or `dispute.expired`.
- Reading `customer` from a dispute webhook payload; it is not there.
- Retrying a failed refund call without checking existing refunds first.
