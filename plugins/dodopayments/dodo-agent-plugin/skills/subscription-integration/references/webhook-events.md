# Dodo Payments Subscription Integration: Webhook Events


| Event | When | Action |
|-------|------|--------|
| `subscription.active` | Subscription becomes active, including a trial start or recovery | Grant access |
| `subscription.updated` | Any subscription field changes | Sync your stored copy (status, dates, metadata) |
| `subscription.renewed` | Successful renewal | Log renewal, send receipt |
| `subscription.past_due` | Renewal failed and the grace period opened (payload has `past_due_ends_at`) | Keep access, prompt for payment before the deadline |
| `subscription.on_hold` | Renewal/plan-change payment failed | Notify customer, offer recovery |
| `subscription.paused` | Subscription paused | Revoke access while paused |
| `subscription.unpaused` | Paused subscription resumed | Restore access |
| `subscription.plan_changed` | Plan upgraded/downgraded or add-ons changed | Update entitlements |
| `subscription.update_payment_method` | Payment method updated | Update stored payment details |
| `subscription.cancelled` | Customer cancels | Schedule access revocation per `cancel_at_next_billing_date` |
| `subscription.failed` | Initial creation failed (mandate creation) | Notify customer, offer a new subscription |
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
    case 'subscription.paused':
    case 'subscription.unpaused': {
      // Pause and resume can happen in quick succession, and handlers for
      // different events can finish in any order. Don't trust the event type:
      // re-read the subscription and apply its CURRENT status, scoped to this
      // subscription (the customer may hold other active ones). Run this under
      // a per-subscription lock if your handlers execute concurrently.
      const current = await client.subscriptions.retrieve(event.data.subscription_id);
      if (current.status === 'paused') {
        await suspendSubscriptionAccess(current.subscription_id);
      } else if (current.status === 'active' || current.status === 'past_due') {
        // past_due keeps access during the payment grace period
        await restoreSubscriptionAccess(current.subscription_id);
      }
      break;
    }
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
