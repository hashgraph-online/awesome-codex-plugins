---
name: dodo-payments
description: Integrates Dodo Payments with the dodopayments SDK and the Dodo Payments MCP server. Covers checkout sessions, subscriptions and plan changes, webhook signature verification, usage-based (metered) billing, credits, license keys, products, discounts, localized pricing, customers and the customer portal, refunds and disputes, framework adapters, Better Auth, BillingSDK, mobile checkout, and test mode through go-live. Use whenever a task mentions Dodo Payments, dodopayments, a checkout or pay button, a subscription, a webhook from Dodo, metered or usage billing, credits, license keys, refunds, or a Merchant of Record integration, even if the skill is not named.
---

# Dodo Payments

Dodo Payments is a Merchant of Record: it is the legal seller, collects and remits sales tax, and handles chargebacks. Your code creates checkout sessions, verifies webhooks, and grants access.

## When to use this skill and the standard path

Use it for any Dodo Payments integration or account task. Almost every integration follows the same three steps:

1. **Create a checkout session** on the server with `client.checkoutSessions.create(...)` and redirect the customer to `checkout_url`.
2. **Handle the webhook.** Dodo POSTs a signed webhook to your endpoint. Verify it on the raw body with `client.webhooks.unwrap(...)`.
3. **Grant access** from the verified webhook: `payment.succeeded` for one-time purchases, `subscription.active` for subscriptions. The `return_url` redirect is a UI hint, never proof of payment.

```typescript
import DodoPayments from 'dodopayments';
import express from 'express';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  environment: process.env.DODO_PAYMENTS_ENVIRONMENT === 'live_mode' ? 'live_mode' : 'test_mode',
});
const app = express();

// The webhook route takes the raw bytes, so mount it before express.json().
app.post('/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
  let event: DodoPayments.UnwrapWebhookEvent;
  try {
    event = client.webhooks.unwrap(req.body.toString('utf8'), {
      headers: {
        'webhook-id': req.headers['webhook-id'] as string,
        'webhook-signature': req.headers['webhook-signature'] as string,
        'webhook-timestamp': req.headers['webhook-timestamp'] as string,
      },
    });
  } catch {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  if (event.type === 'payment.succeeded') await grantAccess(event.data.customer.customer_id);
  if (event.type === 'subscription.active') await grantAccess(event.data.customer.customer_id);
  res.json({ received: true });
});

app.use(express.json());
app.post('/api/checkout', async (req, res) => {
  const session = await client.checkoutSessions.create({
    product_cart: [{ product_id: 'pdt_pro_monthly', quantity: 1 }], // map a plan slug server-side
    customer: { email: 'customer@example.com' },
    return_url: 'https://example.com/checkout/success',
  });
  res.json({ checkout_url: session.checkout_url });
});
```

Production handlers also deduplicate on `webhook-id` and process durably: see [references/webhooks.md](references/webhooks.md).

## Client setup, test mode and live mode

| | Test mode | Live mode |
|---|---|---|
| `environment` option | `'test_mode'` | `'live_mode'` (the SDK default) |
| Base URL | `https://test.dodopayments.com` | `https://live.dodopayments.com` |
| API key prefix | `dodo_test_` | `dodo_live_` |

- Install `dodopayments` (npm, pip) or `github.com/dodopayments/dodopayments-go`. PHP, Ruby, Java and Kotlin SDKs exist too; use the MCP `search` tool for their setup.
- Read the key from `DODO_PAYMENTS_API_KEY` and the webhook secret from `DODO_PAYMENTS_WEBHOOK_KEY`.
- Narrow `environment` from an env var and default to `test_mode`, as above, so a missing variable never selects live mode. Keys, products, customers and webhooks never cross between modes.
- Amounts are integers in the smallest currency unit: USD 10.00 is `1000`.
- The SDK retries connection errors, 408, 409, 429 and 5xx twice. `for await` over a list method walks every page.

## Safety rules that must never be broken

1. **Verify webhook signatures on the raw body.** Use `client.webhooks.unwrap()` or the `standardwebhooks` package. Never hand-roll HMAC and never verify re-serialized JSON. `unsafeUnwrap()` is only for the unsigned payloads that `dodo wh trigger` sends.
2. **Use test mode until go-live.** Pass `environment: 'test_mode'` with a `dodo_test_` key. Switch to live only through [references/testing-go-live.md](references/testing-go-live.md).
3. **Never put API keys in client code.** Browser bundles, mobile apps, desktop apps and CLIs never hold a Dodo API key, and Dodo has no publishable key. Call Dodo from your server; the client receives only a URL.
4. **Confirm before any write in live mode.** Before a live refund, cancellation, plan change, charge, delete, or webhook endpoint change, name the resource ID and the effect and wait for the user's yes.
5. **Grant access only from a verified webhook or a server-side API read**, never from `return_url` query parameters, browser state, or a mobile SDK result.

## Routing table

Read only the file the task needs.

| Task | Read |
|---|---|
| Pay button, checkout session options, overlay or inline checkout, static payment links, return URL | [references/checkout.md](references/checkout.md) |
| Checkout inside a React Native, Flutter, iOS or Android app | [references/mobile-checkout.md](references/mobile-checkout.md) |
| Trials, plan upgrades and downgrades, proration, pause, cancel, on-demand charges, dunning | [references/subscriptions.md](references/subscriptions.md) |
| Webhook endpoint, verification, idempotency, retries, the full list of webhook types | [references/webhooks.md](references/webhooks.md) |
| Meters, usage events, per-unit pricing | [references/usage-billing.md](references/usage-billing.md) |
| Prepaid or included credits, balances, ledger, rollover, overage | [references/credits.md](references/credits.md) |
| License key activation and validation in an app, CLI or desktop app | [references/license-keys.md](references/license-keys.md) |
| Products, prices, add-ons, collections, images, digital files | [references/products.md](references/products.md) |
| Discount codes, eligibility, stacking, discounts on plan changes | [references/discounts.md](references/discounts.md) |
| Prices per country or currency, Adaptive Currency, purchasing power parity | [references/localized-pricing.md](references/localized-pricing.md) |
| Customers, customer portal, saved payment methods, wallets | [references/customers.md](references/customers.md) |
| Refunds, disputes, revoking and restoring access | [references/refunds-disputes.md](references/refunds-disputes.md) |
| `@dodopayments/*` adapters for Next.js, Express, Hono, Fastify, Astro, Remix, SvelteKit, Nuxt, TanStack, Bun, Convex | [references/framework-adapters.md](references/framework-adapters.md) |
| Apps that use Better Auth | [references/better-auth.md](references/better-auth.md) |
| Pricing tables and billing UI in React (BillingSDK) | [references/billing-sdk.md](references/billing-sdk.md) |
| Test cards, the Dodo CLI, local webhooks, go-live checklist | [references/testing-go-live.md](references/testing-go-live.md) |
| The `dodopayments` MCP server: tools, sign-in, troubleshooting | [references/mcp.md](references/mcp.md) |

## Using the `dodopayments` MCP server

When the `dodopayments` MCP server is connected (`https://mcp.dodopayments.com/mcp`), it has five tools. The client signs in to Dodo Payments through OAuth when the server is added; no API key is needed.

| Tool | Use it to |
|---|---|
| `search_docs` | Find guides and docs pages |
| `read_docs_page` | Read a full docs page as Markdown |
| `search` | Find SDK and API methods, parameters and response fields |
| `execute` | Run TypeScript against the `dodopayments` SDK on the user's account |
| `feedback` | Report docs that were wrong, missing or confusing |

- Call `search_docs` before writing integration code. The docs win over memory.
- Call `search` before `execute`, so the script uses real method names and fields.
- Use `execute` for account actions (list products, look up a payment, create a test checkout session). Follow safety rule 4 for every live-mode write.

Details: [references/mcp.md](references/mcp.md).

## Old patterns

Recognise these in existing code and replace them in new code:

- `client.payments.create()` and `client.subscriptions.create()` are deprecated. Use `client.checkoutSessions.create()`.
- The `discount_code` string is deprecated. Use the `discount_codes` array.
- The `license_key.created` webhook is legacy. Use `entitlement_grant.created`.
- `client.licenseKeys.list()`, `retrieve()` and `update()` are deprecated. Read keys through entitlement grants.
- `type: "dynamic"` checkout in the framework adapters calls the deprecated endpoints. Use `type: "session"`.
