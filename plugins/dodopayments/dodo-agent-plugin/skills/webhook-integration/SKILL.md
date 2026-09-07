---
name: webhook-integration
description: Complete guide for setting up and handling Dodo Payments webhooks for real-time payment event notifications.
---

# Dodo Payments Webhook Integration

Webhooks deliver real-time notifications when payment events occur. Use them to automate workflows, update databases, send confirmations, and keep your systems in sync.

## When to use this skill

- Setting up a webhook endpoint to receive payment, subscription, or refund events
- Implementing signature verification to ensure webhook authenticity
- Handling specific event types (payment succeeded, subscription renewed, etc.)
- Testing webhooks locally during development
- Ensuring idempotent webhook processing to handle retries

---

## Core Concepts

**Webhook**: An HTTP POST request sent by Dodo to your endpoint when an event occurs.

**Signature verification**: Cryptographic proof that a webhook came from Dodo, not an attacker. Required for production.

**Idempotency**: Processing the same webhook multiple times produces the same result. Use the `webhook-id` header to detect and skip duplicates.

**Raw body**: The exact bytes received from Dodo, before parsing. Required for signature verification.

---

## Setup: Creating a Webhook Endpoint

### 1. Create the endpoint in the dashboard

1. Go to **Developer → Webhooks**
2. Click **Create Webhook**
3. Enter your endpoint URL (must be HTTPS in production)
4. Select the events you want to receive
5. Copy the signing secret

### 2. Store the signing secret

```bash
export DODO_PAYMENTS_WEBHOOK_KEY=whsec_...
```

The SDK reads this automatically. You can also pass it explicitly when initializing the client.

---

## Webhook Headers and Payload

Every webhook request includes three required headers (all lowercase, hyphenated):

| Header | Example | Purpose |
|--------|---------|---------|
| `webhook-id` | `evt_abc123` | Unique identifier for this webhook delivery |
| `webhook-signature` | `v1,base64_signature_here` | HMAC-SHA256 signature for verification |
| `webhook-timestamp` | `1704067200` | Unix timestamp (seconds) when the event was sent |

The request body is JSON:

```json
{
  "business_id": "bus_xxxxx",
  "type": "payment.succeeded",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "payload_type": "Payment",
    "payment_id": "pay_xxxxx",
    "status": "succeeded",
    "total_amount": 2999,
    "currency": "USD",
    "customer": {
      "customer_id": "cus_xxxxx",
      "email": "customer@example.com",
      "name": "John Doe"
    }
  }
}
```

---

## Verification: The Centerpiece

**Always verify the signature before processing.** Unverified webhooks can be spoofed.

### Preferred: SDK helper

The simplest and safest approach. The SDK handles all verification details.

**TypeScript/Node:**

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
    const unwrapped = client.webhooks.unwrap(req.body.toString(), {
      headers: {
        'webhook-id': req.headers['webhook-id'] as string,
        'webhook-signature': req.headers['webhook-signature'] as string,
        'webhook-timestamp': req.headers['webhook-timestamp'] as string,
      },
    });
    
    // Signature verified. Process the event.
    console.log(`Received ${unwrapped.type}`);
    res.json({ received: true });
  } catch (error) {
    res.status(401).json({ error: 'Invalid signature' });
  }
});
```

**Python:**

```python
from typing import Literal
from fastapi import FastAPI, Request, HTTPException
from dodopayments import DodoPayments
import os

# `environment` is Literal["live_mode", "test_mode"], not str. Passing the raw
# variable through raises at construction: unset gives
# `ValueError: Unknown environment: None`, and a typo like "test" gives
# `Unknown environment: test`. Narrow it, defaulting to test mode so a
# misconfigured variable can never select live.
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
        unwrapped = client.webhooks.unwrap(
            await request.body(),
            headers={
                "webhook-id": request.headers.get("webhook-id", ""),
                "webhook-signature": request.headers.get("webhook-signature", ""),
                "webhook-timestamp": request.headers.get("webhook-timestamp", ""),
            },
        )
        # Signature verified. Process the event.
        return {"received": True}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid signature")
```

**Go:**

```go
import (
	"io"
	"net/http"
	"os"

	"github.com/dodopayments/dodopayments-go"
	"github.com/dodopayments/dodopayments-go/option"
)

// The Go SDK has no WithEnvironment(string). It exposes two explicit options,
// so narrow here and default to test mode: an unset or misspelled variable must
// never select live mode.
func dodoEnvironment() option.RequestOption {
	if os.Getenv("DODO_PAYMENTS_ENVIRONMENT") == "live_mode" {
		return option.WithEnvironmentLiveMode()
	}
	return option.WithEnvironmentTestMode()
}

func webhookHandler(w http.ResponseWriter, r *http.Request) {
	client := dodopayments.NewClient(
		option.WithBearerToken(os.Getenv("DODO_PAYMENTS_API_KEY")),
		dodoEnvironment(),
		option.WithWebhookKey(os.Getenv("DODO_PAYMENTS_WEBHOOK_KEY")),
	)

	rawBody, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Cannot read body", http.StatusBadRequest)
		return
	}

	// Unwrap takes the raw body and the request headers directly. It is not
	// context-aware and does not take a map: the signature is
	// Unwrap(payload []byte, headers http.Header, opts ...option.RequestOption).
	if _, err := client.Webhooks.Unwrap(rawBody, r.Header); err != nil {
		http.Error(w, "Invalid signature", http.StatusUnauthorized)
		return
	}

	// Signature verified. Process the event.
	w.WriteHeader(http.StatusOK)
}
```

### Alternative: `standardwebhooks` package

If you prefer manual verification or don't use the Dodo SDK:

```typescript
import { Webhook } from "standardwebhooks";
import express from "express";

const app = express();
app.use(express.raw({ type: "application/json" }));

const webhook = new Webhook(process.env.DODO_PAYMENTS_WEBHOOK_KEY);

app.post("/webhooks/dodo", async (req, res) => {
  try {
    const payload = req.body.toString();
    await webhook.verify(payload, req.headers);
    
    const event = JSON.parse(payload);
    console.log(`Received ${event.type}`);
    res.json({ received: true });
  } catch (error) {
    res.status(401).json({ error: "Invalid signature" });
  }
});
```

### `unwrap()` vs `unsafeUnwrap()`

- `unwrap()` verifies the signature. Use this for all production webhooks.
- `unsafeUnwrap()` skips verification. Use only for unsigned test payloads from `dodo wh trigger`.

---

## Raw Body Requirement

Signature verification requires the exact bytes Dodo sent. If you parse the JSON first and then re-serialize it, the bytes change and verification fails.

**Framework-specific setup:**

| Framework | Raw body setup |
|-----------|---|
| **Express** | `app.use(express.raw({ type: 'application/json' }))` |
| **Next.js** | `req.text()` in route handlers; no middleware needed |
| **Fastify** | Custom content-type parser (see adaptor docs) |
| **Hono** | Built-in; no special setup |
| **FastAPI** | `await request.body()` returns bytes |
| **Go** | `io.ReadAll(r.Body)` |

---

## Webhook Event Catalog

Dodo sends 40+ event types across nine domains. Subscribe to only the events you need.

### Payment events

| Event | When it fires | What to do |
|-------|---|---|
| `payment.succeeded` | Payment completed successfully | Grant access, send confirmation, update order status |
| `payment.failed` | Payment attempt failed | Notify customer, suggest retry or alternative payment method |
| `payment.processing` | Payment is still being processed | Acknowledge receipt, wait for `payment.succeeded` or `payment.failed` |
| `payment.cancelled` | Payment was cancelled before completion | Update order status, notify customer if applicable |

### Subscription events

| Event | When it fires | What to do |
|-------|---|---|
| `subscription.active` | Subscription becomes active; recurring charges are scheduled | Grant subscription access, send welcome email |
| `subscription.updated` | Any field on the subscription changes | Sync changes to your database |
| `subscription.on_hold` | Failed renewal temporarily pauses the subscription | Notify customer, prompt payment method update |
| `subscription.renewed` | Subscription amount successfully deducted for a billing period | Log renewal, update next billing date |
| `subscription.plan_changed` | Plan upgraded, downgraded, or modified | Update customer's access level or feature set |
| `subscription.update_payment_method` | Payment method is updated | Sync the new payment method to your records |
| `subscription.cancelled` | Merchant or customer cancels the subscription | Revoke access, send cancellation confirmation |
| `subscription.failed` | Subscription creation fails (mandate creation failed) | Notify customer, suggest alternative payment method |
| `subscription.expired` | Subscription reaches the end of its term | Revoke access, offer renewal or upgrade |

### Refund events

| Event | When it fires | What to do |
|-------|---|---|
| `refund.succeeded` | Refund successfully processed | Update order status, revoke access if applicable |
| `refund.failed` | Refund processing fails | Alert team, investigate reason |

### Dispute events

| Event | When it fires | What to do |
|-------|---|---|
| `dispute.opened` | Customer initiates a dispute | Alert team, prepare evidence |
| `dispute.expired` | Dispute expires without resolution | Log outcome |
| `dispute.accepted` | Merchant accepts the dispute | Process refund if not already done |
| `dispute.cancelled` | Customer or system cancels the dispute | Log outcome |
| `dispute.challenged` | Merchant challenges the dispute | Prepare additional evidence |
| `dispute.won` | Merchant wins the dispute | Log outcome, retain funds |
| `dispute.lost` | Merchant loses the dispute | Process refund, log outcome |

### License key events

| Event | When it fires | What to do |
|-------|---|---|
| `license_key.created` | License key is generated | Send key to customer (legacy; prefer `entitlement_grant.delivered`) |

### Entitlement grant events

| Event | When it fires | What to do |
|-------|---|---|
| `entitlement_grant.created` | Grant row is created | Prepare for fulfillment |
| `entitlement_grant.delivered` | Fulfillment completes; customer receives access | Grant platform, file, or license-key access |
| `entitlement_grant.failed` | Delivery fails and is no longer retried | Alert team, inspect `error_code` and `error_message` |
| `entitlement_grant.revoked` | Access is withdrawn | Revoke customer access, inspect `revocation_reason` |

### Credit events

These concern virtual credit entitlements, not monetary wallet balances.

| Event | When it fires | What to do |
|-------|---|---|
| `credit.added` | Credits granted via subscription, purchase, add-on, or API | Update internal credit balance, log grant |
| `credit.deducted` | Usage or manual debit consumes credits | Update internal credit balance |
| `credit.expired` | Unused credits reach expiry | Log expiration, notify customer if applicable |
| `credit.rolled_over` | Unused credits carried into a new grant | Update internal balance |
| `credit.rollover_forfeited` | Credits forfeited at max rollover count | Log forfeiture |
| `credit.overage_charged` | Overage charged after usage exceeds balance | Update internal balance, notify customer |
| `credit.overage_reset` | Accumulated overage reset (e.g., new billing cycle) | Update internal balance |
| `credit.manual_adjustment` | Manual credit or debit adjustment made | Update internal balance, log adjustment |
| `credit.balance_low` | Balance falls below configured threshold | Notify customer, suggest purchase |

### Recovery and dunning events

| Event | When it fires | What to do |
|-------|---|---|
| `abandoned_checkout.detected` | Failed or incomplete checkout classified as abandoned (after 60 min) | Monitor recovery link usage |
| `abandoned_checkout.recovered` | Customer pays through recovery link | Log recovery, update order status |
| `dunning.started` | Dunning attempt begins after subscription enters `on_hold` | Monitor dunning progress |
| `dunning.recovered` | Customer updates payment method and charge succeeds | Reactivate subscription, send confirmation |

---

## Production-Grade Handler Pattern

Respond quickly after durably recording the event, process asynchronously, and use idempotency keys. In the worker, insert the idempotency claim and apply all durable business changes in one database transaction. If processing throws, the transaction rolls back the claim so the job can retry safely:

```typescript
import DodoPayments from 'dodopayments';
import express from 'express';
import { Queue, Worker } from 'bullmq';

// BullMQ is illustrative; use your preferred durable async queue.

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

type WebhookEvent = ReturnType<typeof client.webhooks.unwrap>;
type WebhookJob = { event: WebhookEvent; webhookId: string };

const connection = {
  host: process.env.REDIS_HOST ?? '127.0.0.1',
  port: Number(process.env.REDIS_PORT ?? '6379'),
};
const eventQueue = new Queue<WebhookJob>('webhook-events', { connection });

app.post('/webhook', async (req, res) => {
  let unwrapped: WebhookEvent;
  
  try {
    unwrapped = client.webhooks.unwrap(req.body.toString(), {
      headers: {
        'webhook-id': req.headers['webhook-id'] as string,
        'webhook-signature': req.headers['webhook-signature'] as string,
        'webhook-timestamp': req.headers['webhook-timestamp'] as string,
      },
    });
  } catch (error) {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  
  // Durably enqueue before acknowledging, keyed by webhook-id for idempotency
  const webhookId = req.headers['webhook-id'] as string;
  try {
    await eventQueue.add(
      `process-${unwrapped.type}`,
      { event: unwrapped, webhookId },
      {
        jobId: webhookId, // Prevents duplicate queue entries
        attempts: 8,
        backoff: { type: 'exponential', delay: 1000 },
      }
    );
    return res.json({ received: true });
  } catch (error) {
    console.error('Failed to persist webhook', error);
    return res.status(503).json({ error: 'Webhook persistence failed' });
  }
});

// Async worker. webhookLog.webhookId must have a unique constraint.
const worker = new Worker<WebhookJob>(
  'webhook-events',
  async (job) => {
    const { event, webhookId } = job.data;

    await db.$transaction(async (tx) => {
      const claim = await tx.webhookLog.createMany({
        data: [{ webhookId, eventType: event.type }],
        skipDuplicates: true,
      });
      if (claim.count === 0) return;

      switch (event.type) {
        case 'payment.succeeded':
          await handlePaymentSucceeded(event.data, tx);
          break;
        case 'subscription.active':
          await handleSubscriptionActive(event.data, tx);
          break;
        // ... handle other events
      }
    });
  },
  { connection }
);
```

The handlers above must perform entitlement writes through `tx`. Queue emails or other external work through a transactional outbox; a database transaction cannot roll back an already-sent external request.

---

## Delivery Semantics

Understand how Dodo delivers webhooks:

| Property | Behavior |
|----------|----------|
| **Timeout** | 15 seconds for connection and read |
| **Success** | Any `2xx` response acknowledges delivery. Return `200` immediately after durably recording the event. |
| **Failure** | Any non-`2xx` response triggers a retry. |
| **Retries** | Eight attempts: immediately, 5s, 5m, 30m, 2h, 5h, 10h, 10h |
| **Idempotency** | Use `webhook-id` to detect and skip duplicates |
| **Ordering** | No guarantee. Events can arrive out of order. |
| **Payload freshness** | Delivery contains the latest resource state at delivery time |
| **Transport** | Use HTTPS in production |

---

## Framework Adaptor Shortcuts

If you use a supported framework, use the official adaptor package for built-in webhook handling:

| Framework | Package | Webhook handler |
|-----------|---------|---|
| Next.js | `@dodopayments/nextjs` | `Webhooks({ webhookKey, onPayload })` |
| Nuxt | `@dodopayments/nuxt` | `Webhooks({ webhookKey, onPayload })` |
| Express | `@dodopayments/express` | Middleware with raw-body parser |
| Fastify | `@dodopayments/fastify` | `Webhooks({ webhookKey, onPayload })` |
| Hono | `@dodopayments/hono` | `Webhooks({ webhookKey, onPayload })` |
| Astro | `@dodopayments/astro` | `Webhooks({ webhookKey, onPayload })` |
| SvelteKit | `@dodopayments/sveltekit` | `Webhooks({ webhookKey, onPayload })` |
| Remix | `@dodopayments/remix` | `Webhooks({ webhookKey, onPayload })` |
| TanStack Start | `@dodopayments/tanstack` | `Webhooks({ webhookKey, onPayload })` |
| Bun | `@dodopayments/bun` | `Webhooks({ webhookKey, onPayload })` |
| Better Auth | `@dodopayments/better-auth` | Plugin with `webhooks({ webhookKey, onPayload })` |
| Convex | `@dodopayments/convex` | Component with verified HTTP handler |

**Next.js example:**

The adapter callback does not expose `webhook-id`, so this payment example uses `payment_id` as its stable key and commits the claim and durable fulfillment together. Use a handler that exposes `webhook-id` for event types without a verified stable identifier.

```typescript
// app/api/webhook/dodo-payments/route.ts
import { Webhooks } from "@dodopayments/nextjs";

export const POST = Webhooks({
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => {
    // payload is already verified
    console.log(`Received ${payload.type}`);

    if (payload.type !== 'payment.succeeded') return;

    // webhookLog.webhookId must have a unique constraint. If fulfillment
    // throws, the claim rolls back and Dodo's redelivery can retry it.
    await db.$transaction(async (tx) => {
      const claim = await tx.webhookLog.createMany({
        data: [{
          webhookId: payload.data.payment_id,
          eventType: payload.type,
        }],
        skipDuplicates: true,
      });
      if (claim.count === 0) return;

      await handlePaymentSucceeded(payload.data, tx);
    });
  },
});
```

Handle `subscription.active` only in a handler that exposes `webhook-id`, then commit that claim and the entitlement changes in the same transaction.

---

## Local Testing

### Dashboard test tool

1. Go to **Developer → Webhooks → [your endpoint] → Testing**
2. Select an event type
3. Click **Send Example**
4. Verify your endpoint returns `200` and the signature verifies

### CLI: Live forwarding

Forward real test-mode events to localhost:

```bash
dodo wh listen http://localhost:3000/webhook
```

This creates a test webhook, opens a WebSocket relay, and forwards events with valid signatures to your local URL. Requires a test-mode API key. The URL argument is required in direct mode — bare `dodo wh listen` only works as `/wh listen` inside the TUI.

### CLI: Unsigned mock events

Generate realistic unsigned payloads for testing without signature verification:

```bash
dodo wh trigger payment.success http://localhost:3000/webhook
```

Use `unsafeUnwrap()` only for these unsigned payloads. Both arguments are required in direct mode.

### Tunnel

Expose localhost with ngrok and register the HTTPS URL in the dashboard:

```bash
ngrok http 3000
# Register https://xxxx.ngrok.io/webhook in the dashboard
```

---

## Common Mistakes

### 1. Signing only the payload or `timestamp.payload`

**Wrong:**
```typescript
const signed = crypto.createHmac('sha256', secret)
  .update(payload)
  .digest('base64');

// or
const signed = crypto.createHmac('sha256', secret)
  .update(`${timestamp}.${payload}`)
  .digest('base64');
```

**Correct:** The signed message is `webhook-id.webhook-timestamp.raw_body`, all three parts joined by periods. Use the SDK helper to avoid this entirely.

### 2. Re-serializing the parsed body

**Wrong:**
```typescript
const body = await req.json();
const signed = JSON.stringify(body); // Reordered, reformatted, breaks signature
```

**Correct:** Always use the raw bytes:
```typescript
const body = await req.text(); // or req.body.toString() in Express
// Pass body directly to unwrap() or webhook.verify()
```

### 3. Naive comma-splitting of the signature header

**Wrong:**
```typescript
const sig = signature.split(',')[1]; // Assumes exactly one comma
```

The header is versioned and can contain multiple values. Use the SDK helper.

### 4. `timingSafeEqual` throwing on length mismatch

**Wrong:**
```typescript
crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(provided));
// Throws if lengths differ; doesn't return false
```

**Correct:** Use the SDK helper, which handles this safely.

### 5. Granting access from `return_url` instead of verified webhooks

**Wrong:**
```typescript
// User visits return_url after checkout; you grant access
app.get('/checkout/return', (req, res) => {
  grantAccess(req.query.customer_id); // Unverified!
});
```

**Correct:** Grant access only after receiving and verifying a webhook:
```typescript
const event = client.webhooks.unwrap(rawBody, { headers });

if (event.type === 'payment.succeeded') {
  grantAccess(event.data.customer.customer_id);
}
```

### 6. Doing slow work before responding 2xx

**Wrong:**
```typescript
app.post('/webhook', async (req, res) => {
  const unwrapped = client.webhooks.unwrap(...);
  
  // Slow database writes, email sends, etc.
  await db.payment.create(...);
  await sendEmail(...);
  
  res.json({ received: true }); // Dodo times out after 15s
});
```

**Correct:** Durably enqueue first, then respond immediately. Return non-`2xx` if persistence fails so Dodo retries:
```typescript
app.post('/webhook', async (req, res) => {
  const unwrapped = client.webhooks.unwrap(...);

  try {
    await queue.add('process-event', unwrapped); // Durable write
    return res.json({ received: true });
  } catch (error) {
    console.error('Failed to persist webhook', error);
    return res.status(503).json({ error: 'Webhook persistence failed' });
  }
});
```

### 7. Acknowledging before durable persistence

**Wrong:**
```typescript
res.json({ received: true });
await queue.add('process-event', unwrapped); // A crash can lose an acknowledged event
```

**Correct:** Verify the signature, durably insert or enqueue the event, and only then return `2xx`. If persistence fails, return non-`2xx` so Dodo retries.

### 8. Committing an idempotency claim before fulfillment

**Wrong:**
```typescript
const claim = await db.webhookLog.createMany({
  data: [{ webhookId }],
  skipDuplicates: true,
});
if (claim.count === 0) return;

await grantSubscriptionEntitlements(event.data); // A failure leaves the claim behind
```

The retry sees the existing claim and skips fulfillment, permanently dropping the event.

**Correct:** Commit the claim and all durable fulfillment changes in one transaction. A failure rolls both back, so the retry can claim the event again:
```typescript
const event = client.webhooks.unwrap(rawBody, { headers });

await db.$transaction(async (tx) => {
  const claim = await tx.webhookLog.createMany({
    data: [{ webhookId, eventType: event.type }],
    skipDuplicates: true,
  });
  if (claim.count === 0) return;

  if (event.type === 'subscription.active') {
    await grantSubscriptionEntitlements(event.data, tx);
  }
});
```

Use a transactional outbox for email or other external effects that must follow the database commit.

---

## Resources

- [Webhook Documentation](https://docs.dodopayments.com/developer-resources/webhooks)
- [Event Catalog](https://docs.dodopayments.com/developer-resources/webhooks/intents/webhook-events-guide)
- [Standard Webhooks Spec](https://standardwebhooks.com/)
- [Framework Adaptors](https://docs.dodopayments.com/developer-resources/framework-adaptors)
- [CLI Reference](https://docs.dodopayments.com/developer-resources/sdks/cli)
