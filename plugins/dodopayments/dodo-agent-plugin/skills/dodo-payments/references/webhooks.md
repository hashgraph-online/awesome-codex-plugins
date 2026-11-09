# Webhooks

## Contents

- [Set up the endpoint](#set-up-the-endpoint)
- [Headers and payload](#headers-and-payload)
- [Verify the signature](#verify-the-signature)
- [Raw body by framework](#raw-body-by-framework)
- [Production handler: durable and idempotent](#production-handler-durable-and-idempotent)
- [Delivery behaviour](#delivery-behaviour)
- [Webhook types](#webhook-types)
- [Common mistakes](#common-mistakes)

Local testing with the Dodo CLI is in [testing-go-live.md](testing-go-live.md). Framework adapters that verify for you are in [framework-adapters.md](framework-adapters.md).

## Set up the endpoint

1. In the dashboard, open **Developer > Webhooks > Create Webhook**, enter the HTTPS URL, and pick the webhook types you handle.
2. Copy the signing secret into `DODO_PAYMENTS_WEBHOOK_KEY`. The SDK reads it for `webhookKey`.
3. Test mode and live mode have separate endpoints and secrets.

## Headers and payload

Every delivery carries `webhook-id` (unique per webhook, use it for deduplication), `webhook-signature` (`v1,<base64>`), and `webhook-timestamp` (Unix seconds). The body:

```json
{
  "business_id": "bus_xxxxx",
  "type": "payment.succeeded",
  "timestamp": "2025-01-01T12:00:00Z",
  "data": { "payload_type": "Payment", "payment_id": "pay_xxxxx", "total_amount": 2999, "currency": "USD", "customer": { "customer_id": "cus_xxxxx", "email": "customer@example.com" } }
}
```

`data` holds the latest state of the resource when the webhook was sent.

## Verify the signature

Dodo follows the Standard Webhooks spec: HMAC-SHA256 over `webhook-id.webhook-timestamp.raw_body`. Let the SDK do it. `unwrap()` checks the signature and the timestamp and returns a typed webhook; it throws on failure.

Express (mount before `express.json()`):

```typescript
import DodoPayments from 'dodopayments';
import express from 'express';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  environment: process.env.DODO_PAYMENTS_ENVIRONMENT === 'live_mode' ? 'live_mode' : 'test_mode',
});
const app = express();

app.post('/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
  try {
    const event = client.webhooks.unwrap(req.body.toString('utf8'), {
      headers: {
        'webhook-id': req.headers['webhook-id'] as string,
        'webhook-signature': req.headers['webhook-signature'] as string,
        'webhook-timestamp': req.headers['webhook-timestamp'] as string,
      },
    });
    console.log(`Verified ${event.type}`);
    res.json({ received: true });
  } catch {
    res.status(401).json({ error: 'Invalid signature' });
  }
});
```

Next.js route handler:

```typescript
// app/api/webhook/route.ts
export async function POST(req: Request) {
  const raw = await req.text();
  try {
    const event = client.webhooks.unwrap(raw, {
      headers: {
        'webhook-id': req.headers.get('webhook-id') ?? '',
        'webhook-signature': req.headers.get('webhook-signature') ?? '',
        'webhook-timestamp': req.headers.get('webhook-timestamp') ?? '',
      },
    });
    console.log(`Verified ${event.type}`);
    return Response.json({ received: true });
  } catch {
    return Response.json({ error: 'Invalid signature' }, { status: 401 });
  }
}
```

Python (FastAPI):

```python
import os
from typing import Literal

from dodopayments import DodoPayments
from fastapi import FastAPI, HTTPException, Request

# Narrow the variable: environment is Literal["live_mode", "test_mode"].
ENVIRONMENT: Literal["live_mode", "test_mode"] = (
    "live_mode" if os.getenv("DODO_PAYMENTS_ENVIRONMENT") == "live_mode" else "test_mode"
)
app = FastAPI()
client = DodoPayments(
    bearer_token=os.getenv("DODO_PAYMENTS_API_KEY"),
    environment=ENVIRONMENT,
    webhook_key=os.getenv("DODO_PAYMENTS_WEBHOOK_KEY"),
)


@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        event = client.webhooks.unwrap(
            await request.body(),
            headers={
                "webhook-id": request.headers.get("webhook-id", ""),
                "webhook-signature": request.headers.get("webhook-signature", ""),
                "webhook-timestamp": request.headers.get("webhook-timestamp", ""),
            },
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid signature")
    print(event.type)
    return {"received": True}
```

Go (`Unwrap` takes the raw body and the request headers):

```go
import (
	"io"
	"net/http"
	"os"

	"github.com/dodopayments/dodopayments-go"
	"github.com/dodopayments/dodopayments-go/option"
)

func webhookHandler(w http.ResponseWriter, r *http.Request) {
	env := option.WithEnvironmentTestMode()
	if os.Getenv("DODO_PAYMENTS_ENVIRONMENT") == "live_mode" {
		env = option.WithEnvironmentLiveMode()
	}
	client := dodopayments.NewClient(
		option.WithBearerToken(os.Getenv("DODO_PAYMENTS_API_KEY")),
		env,
		option.WithWebhookKey(os.Getenv("DODO_PAYMENTS_WEBHOOK_KEY")),
	)
	rawBody, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Cannot read body", http.StatusBadRequest)
		return
	}
	if _, err := client.Webhooks.Unwrap(rawBody, r.Header); err != nil {
		http.Error(w, "Invalid signature", http.StatusUnauthorized)
		return
	}
	w.WriteHeader(http.StatusOK)
}
```

Without the Dodo SDK, use the `standardwebhooks` package: `await new Webhook(process.env.DODO_PAYMENTS_WEBHOOK_KEY).verify(rawBody, headers)`, then `JSON.parse(rawBody)`.

## Raw body by framework

| Framework | Raw body |
|---|---|
| Express | `express.raw({ type: 'application/json' })` on the webhook route, registered before `express.json()` |
| Next.js, Remix, Hono, Bun (`Request`) | `await req.text()` |
| Fastify | a string content-type parser, see [framework-adapters.md](framework-adapters.md) |
| FastAPI | `await request.body()` |
| Go | `io.ReadAll(r.Body)` |

## Production handler: durable and idempotent

Dodo retries, so the same webhook can arrive more than once and out of order. Use this pattern:

1. Verify the signature.
2. Claim `webhook-id` with a unique insert and apply every database change for the webhook in the **same transaction**. If the work throws, the claim rolls back and the retry can run again.
3. Return 2xx only after the transaction (or a durable enqueue) commits. Return non-2xx on failure so Dodo retries.
4. Send emails and other external calls through an outbox after the commit.

```typescript
app.post('/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
  const webhookId = req.headers['webhook-id'] as string;
  let event: DodoPayments.UnwrapWebhookEvent;
  try {
    event = client.webhooks.unwrap(req.body.toString('utf8'), {
      headers: {
        'webhook-id': webhookId,
        'webhook-signature': req.headers['webhook-signature'] as string,
        'webhook-timestamp': req.headers['webhook-timestamp'] as string,
      },
    });
  } catch {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  try {
    // webhookLog.webhookId has a UNIQUE constraint.
    await db.$transaction(async (tx) => {
      const claim = await tx.webhookLog.createMany({
        data: [{ webhookId, eventType: event.type }],
        skipDuplicates: true,
      });
      if (claim.count === 0) return; // already processed

      switch (event.type) {
        case 'payment.succeeded': // one-time purchases
          await handlePaymentSucceeded(event.data, tx);
          break;
        case 'subscription.active':
          await handleSubscriptionActive(event.data, tx);
          break;
      }
    });
    return res.json({ received: true });
  } catch (error) {
    console.error('Webhook processing failed', error);
    return res.status(500).json({ error: 'Processing failed' });
  }
});
```

For slow work, verify, durably enqueue with the queue job ID set to `webhook-id`, return 2xx, and run the transaction above in the worker.

Because order is not guaranteed, re-read the resource (for example `client.subscriptions.retrieve(id)`) when two webhooks for one resource can race, and apply its current status.

## Delivery behaviour

| | |
|---|---|
| Timeout | 30 seconds |
| Success | any 2xx |
| Retries | on any non-2xx: immediately, 5 s, 5 min, 30 min, 2 h, 5 h, 10 h, 10 h |
| Ordering | not guaranteed |
| Transport | HTTPS in production |

## Webhook types

These are the 48 values of `type`. Subscribe only to the ones you handle.

| Family | Types | Typical action |
|---|---|---|
| Payment | `payment.succeeded`, `payment.failed`, `payment.processing`, `payment.cancelled` | Grant one-time access on `succeeded`; wait on `processing` |
| Subscription | `subscription.active`, `subscription.updated`, `subscription.renewed`, `subscription.plan_changed`, `subscription.past_due`, `subscription.on_hold`, `subscription.paused`, `subscription.unpaused`, `subscription.update_payment_method`, `subscription.cancelled`, `subscription.failed`, `subscription.expired` | See [subscriptions.md](subscriptions.md) |
| Refund | `refund.succeeded`, `refund.failed` | See [refunds-disputes.md](refunds-disputes.md) |
| Dispute | `dispute.opened`, `dispute.challenged`, `dispute.accepted`, `dispute.cancelled`, `dispute.expired`, `dispute.won`, `dispute.lost` | See [refunds-disputes.md](refunds-disputes.md) |
| Entitlement grant | `entitlement_grant.created`, `entitlement_grant.delivered`, `entitlement_grant.failed`, `entitlement_grant.revoked` | License keys, files, feature access; see [license-keys.md](license-keys.md) |
| License key | `license_key.created` | Legacy; use `entitlement_grant.created` |
| Credit | `credit.added`, `credit.deducted`, `credit.expired`, `credit.rolled_over`, `credit.rollover_forfeited`, `credit.overage_charged`, `credit.overage_reset`, `credit.manual_adjustment`, `credit.balance_low` | See [credits.md](credits.md) |
| Recovery | `abandoned_checkout.detected`, `abandoned_checkout.recovered`, `dunning.started`, `dunning.recovered` | Monitor recovery; reactivate on `dunning.recovered` |
| Payout | `payout.created`, `payout.in_progress`, `payout.on_hold`, `payout.success`, `payout.failed` | Bookkeeping only, never customer access |

## Common mistakes

- Verifying re-serialized JSON (`JSON.stringify(req.body)`). Verify the exact raw bytes.
- Hand-rolling HMAC. The signed string is `webhook-id.webhook-timestamp.raw_body`, the header can hold several versioned signatures, and length mismatches make `timingSafeEqual` throw. Use `unwrap()`.
- Granting access from `return_url` instead of a verified webhook.
- Returning 2xx before the work is durable, or claiming `webhook-id` in one transaction and fulfilling in another. Either loses webhooks on a crash.
- Doing slow work before responding. Dodo times out after 30 seconds and retries.
- Using `unsafeUnwrap()` outside local tests of `dodo wh trigger` payloads.
