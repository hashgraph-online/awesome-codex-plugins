---
name: dodo-best-practices
description: Guide for initial Dodo Payments setup, including SDK installation, test and live environments, API keys, and the canonical checkout-to-webhook architecture.
---

# Dodo Payments Integration Guide

This skill covers the foundational concepts and setup for Dodo Payments. Use it when starting a new integration, setting up the SDK, or understanding the core payment flow.

## When to use this skill

- You're building a new payment integration and need to understand Dodo's architecture
- You need to install and initialize the SDK in your language
- You want to understand the canonical payment flow and webhook verification
- You're choosing between framework adapters or payment methods
- You need to know what Dodo handles versus what you must build

---

## What is Dodo Payments

Dodo Payments is a Merchant of Record (MoR). That means Dodo is the legal seller on every transaction, handles sales tax registration and calculation across all jurisdictions, remits taxes to authorities, and manages card-network disputes and chargebacks. As a developer, you don't build a sales-tax engine or dispute-handling system. You create checkout sessions, listen to webhooks, and grant access when payment succeeds.

---

## Environment Setup

### Base URLs

Only two real base URLs exist:

- **Live**: `https://live.dodopayments.com`
- **Test**: `https://test.dodopayments.com`

Never use `api.dodopayments.com` — it has no DNS record and cannot be reached.

### API Keys

Keys have two formats:

- **Test**: `dodo_test_...`
- **Live**: `dodo_live_...`

### Environment Variables

```bash
DODO_PAYMENTS_API_KEY       # Bearer token for API requests
DODO_PAYMENTS_WEBHOOK_KEY   # Secret for webhook signature verification
```

### Default Environment

The `environment` parameter defaults to `live_mode` if omitted. Always pass `test_mode` explicitly during development.

---

## SDK Installation & Initialization

### TypeScript/Node.js

```bash
npm install dodopayments
```

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode', // defaults to 'live_mode'
});
```

Constructor options:

| Option | Type | Default | Notes |
|---|---|---|---|
| `bearerToken` | string | env `DODO_PAYMENTS_API_KEY` | Required for API calls |
| `environment` | `'test_mode' \| 'live_mode'` | `'live_mode'` | Explicit in dev |
| `webhookKey` | string | env `DODO_PAYMENTS_WEBHOOK_KEY` | For `webhooks.unwrap()` |
| `baseURL` | string | — | Override; mutually exclusive with `environment` |

### Python

```bash
pip install dodopayments
```

```python
import os
from dodopayments import DodoPayments

client = DodoPayments(
    bearer_token=os.environ.get("DODO_PAYMENTS_API_KEY"),
    environment="test_mode",  # defaults to "live_mode"
)
```

### Go

```bash
go get -u github.com/dodopayments/dodopayments-go@v1.110.0
```

```go
import (
    "os"

    "github.com/dodopayments/dodopayments-go"
    "github.com/dodopayments/dodopayments-go/option"
)

client := dodopayments.NewClient(
    option.WithBearerToken(os.Getenv("DODO_PAYMENTS_API_KEY")),
    option.WithEnvironmentTestMode(), // defaults to live
)
```

### PHP

```bash
composer require "dodopayments/client:6.19.0"
```

```php
use Dodopayments\Client;

$client = new Client(
    bearerToken: getenv('DODO_PAYMENTS_API_KEY') ?: 'My Bearer Token',
    environment: 'test_mode',
);
```

### Ruby

```bash
gem "dodopayments", "~> 2.22.0"
```

```ruby
dodo_payments = Dodopayments::Client.new(
    bearer_token: ENV["DODO_PAYMENTS_API_KEY"],
    environment: "test_mode"
)
```

### Java

```xml
<dependency>
    <groupId>com.dodopayments.api</groupId>
    <artifactId>dodo-payments-java</artifactId>
    <version>1.110.0</version>
</dependency>
```

```java
DodoPaymentsClient client = DodoPaymentsOkHttpClient.fromEnv();
// Reads DODO_PAYMENTS_API_KEY, DODO_PAYMENTS_WEBHOOK_KEY, DODO_PAYMENTS_BASE_URL
```

### Kotlin

```xml
<dependency>
    <groupId>com.dodopayments.api</groupId>
    <artifactId>dodo-payments-kotlin</artifactId>
    <version>1.110.0</version>
</dependency>
```

```kotlin
val client: DodoPaymentsClient = DodoPaymentsOkHttpClient.fromEnv()
```

---

## Framework Adapters

Dodo publishes framework-specific packages under `@dodopayments/*`. Use the one matching your stack:

| Framework | Package | Use if |
|---|---|---|
| Next.js | `@dodopayments/nextjs` | Building with Next.js App Router |
| Nuxt | `@dodopayments/nuxt` | Building with Nuxt 3+ |
| Express | `@dodopayments/express` | Using Express.js |
| Fastify | `@dodopayments/fastify` | Using Fastify |
| Hono | `@dodopayments/hono` | Using Hono (Edge/Node) |
| Astro | `@dodopayments/astro` | Using Astro endpoints |
| SvelteKit | `@dodopayments/sveltekit` | Using SvelteKit server routes |
| Remix | `@dodopayments/remix` | Using Remix loaders/actions |
| TanStack Start | `@dodopayments/tanstack` | Using TanStack Start |
| Better Auth | `@dodopayments/better-auth` | Integrating with Better Auth |
| Convex | `@dodopayments/convex` | Using Convex backend |
| Bun | `@dodopayments/bun` | Using Bun.serve() |

Each adapter provides checkout, customer portal, and webhook handlers tailored to the framework's conventions.

---

## Core Concepts

### Products

Items you sell. Create in the dashboard or via API. Types:

- **One-time**: Single purchase
- **Subscription**: Recurring billing
- **Usage-based**: Metered consumption

### Customers

Represent buyers. Can have multiple payment methods, subscriptions, and credit balances. Create explicitly or implicitly during checkout.

### Checkout Sessions

The primary payment collection method. Create a session server-side, redirect the customer to the hosted checkout URL, and listen for webhooks to confirm payment.

See the `checkout-integration` skill for detailed checkout configuration and the `subscription-integration` skill for recurring lifecycle management.

### Subscriptions

Recurring charges on a schedule. Managed through checkout sessions or the subscriptions API. See the `subscription-integration` skill for lifecycle, trials, plan changes, and on-demand charging.

### Webhooks

Real-time event notifications. Dodo sends events like `payment.succeeded`, `subscription.active`, `refund.succeeded`, and `credit.deducted`. Webhook signature verification is covered in the `webhook-integration` skill.

### Credit Entitlements

Virtual balances (API calls, tokens, compute hours) attached to products. Configured per product with rollover, overage, and expiration rules. See the `credit-based-billing` skill.

---

## The Canonical Payment Flow

1. **Create checkout session** on your server with product ID and customer email.
2. **Redirect customer** to the `checkout_url` returned.
3. **Customer pays** on the hosted checkout.
4. **Dodo sends webhook** (e.g., `payment.succeeded`) to your endpoint.
5. **Verify the webhook signature** using `client.webhooks.unwrap()`.
6. **Grant access** only after webhook verification succeeds.

Never grant access based on the browser `return_url` redirect alone. The webhook is the authoritative confirmation.

```typescript
import express from 'express';

const app = express();

// 1. Create session
const session = await client.checkoutSessions.create({
  product_cart: [{ product_id: 'pdt_example', quantity: 1 }],
  customer: { email: 'customer@example.com' },
  return_url: 'https://yoursite.com/success',
});

// 2. Redirect to session.checkout_url

// 3. Listen for webhook with the exact raw request bytes
app.post('/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
  try {
    // 4. Verify signature
    const webhookId = req.headers['webhook-id'] as string;
    const event = client.webhooks.unwrap(req.body.toString(), {
      headers: {
        'webhook-id': webhookId,
        'webhook-signature': req.headers['webhook-signature'] as string,
        'webhook-timestamp': req.headers['webhook-timestamp'] as string,
      },
    });

    // 5. Suppress duplicates with an atomic unique insert and run side effects
    // in the same database transaction.
    const handled = await processWebhookOnce(webhookId, async () => {
      if (event.type === 'payment.succeeded') {
        // ONE-TIME purchases only. Subscription access starts on subscription.active.
        const payment = event.data;
        await grantOneTimeAccess(payment.customer.customer_id);
      }

      if (event.type === 'subscription.active') {
        await grantSubscriptionAccess(event.data);
      }
    });

    res.json({ received: true, duplicate: !handled });
  } catch (error) {
    res.status(401).json({ error: 'Invalid signature' });
  }
});
```

---

## API Foundations

### Authentication

All requests use Bearer token authentication:

```http
Authorization: Bearer dodo_live_...
```

### Pagination

List endpoints are page-numbered. They accept `page_size` and `page_number`, and the response
exposes the rows on `items`:

```typescript
const payments = await client.payments.list({
  page_size: 50,
  page_number: 0,
});

for (const payment of payments.items) {
  console.log(payment.payment_id);
}
```

The SDK can also walk every page for you:

```typescript
for await (const payment of client.payments.list()) {
  console.log(payment.payment_id);
}
```

### Rate Limits

Dodo enforces rate limits. The SDK automatically retries `429` responses as described below.

### SDK Error Classes

The SDK throws typed errors. Catch and inspect:

```typescript
try {
  await client.checkoutSessions.create({...});
} catch (error) {
  if (error instanceof DodoPayments.APIError) {
    console.error(error.status, error.message);
  }
}
```

### Retries

The SDK retries twice by default with a short exponential backoff on connection errors and `408`, `409`, `429`, and `5xx` responses. Do not add an unconditional custom retry loop.

Override the default for all requests when constructing the client:

```typescript
const clientWithoutRetries = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode',
  maxRetries: 0,
});
```

Or override it for one request:

```typescript
await client.checkoutSessions.create(
  {
    product_cart: [{ product_id: 'pdt_example', quantity: 1 }],
    customer: { email: 'customer@example.com' },
  },
  { maxRetries: 0 },
);
```

---

## Webhook Verification

Webhook signature verification is mandatory. Never trust the payload without verification.

Dodo implements the Standard Webhooks spec. The signed message is `webhook-id.webhook-timestamp.raw_body` (period-joined), HMAC-SHA256, base64-encoded.

**Use the SDK helper:**

```typescript
const event = client.webhooks.unwrap(req.body.toString(), {
  headers: {
    'webhook-id': req.headers['webhook-id'] as string,
    'webhook-signature': req.headers['webhook-signature'] as string,
    'webhook-timestamp': req.headers['webhook-timestamp'] as string,
  },
});
```

The `unwrap()` method verifies the signature and parses the payload. If verification fails, it throws an error.

For detailed webhook setup, event types, and testing, see the `webhook-integration` skill.

---

## Common Mistakes

### 1. Granting access on `return_url` redirect

The browser redirect is not proof of payment. Always wait for the webhook.

```typescript
// WRONG
app.get('/success', (req, res) => {
  grantAccess(req.query.customer_id); // No verification!
});

// CORRECT
app.post('/webhook', async (req, res) => {
  const event = client.webhooks.unwrap(...);
  if (event.type === 'payment.succeeded') {
    grantAccess(event.data.customer.customer_id);
  }
});
```

### 2. Hand-rolling webhook verification

Don't implement HMAC verification yourself. Use `client.webhooks.unwrap()`.

The old approach of signing just the payload is wrong because Standard Webhooks signs `webhook-id.webhook-timestamp.raw_body`. Hand-rolled HMAC will never match.

### 3. Re-serializing the request body

Webhook verification requires the exact raw body. If you parse JSON and re-stringify it, the signature breaks.

```typescript
// WRONG
const body = JSON.parse(req.body);
const event = client.webhooks.unwrap(JSON.stringify(body), {...});

// CORRECT
const event = client.webhooks.unwrap(req.body.toString(), {...});
```

### 4. Using deprecated APIs

Don't use `client.payments.create()` or `client.subscriptions.create()` for new integrations. Both are deprecated. Use `client.checkoutSessions.create()`.

### 5. Forgetting to set `environment: 'test_mode'`

The default is `live_mode`. Always pass `test_mode` explicitly during development to avoid charging real cards.

### 6. Storing API keys in code

Never hardcode keys. Always use environment variables.

### 7. Ignoring the `webhook-timestamp` header

The timestamp prevents replay attacks. `client.webhooks.unwrap()` validates it automatically, but if you hand-roll verification, check that the timestamp is recent (within a few minutes).

### 8. Using `unsafeUnwrap()` in production

`unsafeUnwrap()` skips signature verification. Use it only for unsigned test payloads from `dodo wh trigger`. Never use it for production webhooks.

---

## Resources

- [Dodo Payments Docs](https://docs.dodopayments.com)
- [API Reference](https://docs.dodopayments.com/api-reference/introduction)
- [SDK Repositories](https://github.com/dodopayments)
- [Checkout Sessions Guide](https://docs.dodopayments.com/developer-resources/checkout-session)
- [Webhook Guide](https://docs.dodopayments.com/developer-resources/webhooks)
- [Customer Portal](https://docs.dodopayments.com/features/customer-portal)
- [Subscription Integration](https://docs.dodopayments.com/developer-resources/subscription-integration-guide)
- [Credit-Based Billing](https://docs.dodopayments.com/features/credit-based-billing)
