---
name: better-auth-integration
description: Guide only for applications using @dodopayments/better-auth, covering authenticated customer sync, checkout, portal access, usage ingestion, and verified webhook callbacks.
---

# Better Auth Integration

Use `@dodopayments/better-auth` to synchronize Better Auth users with Dodo Payments and expose authenticated checkout, customer portal, subscription, payment, usage, and webhook endpoints.

## When to use this skill

- Create a Dodo customer automatically when a Better Auth user signs up.
- Start checkout for a signed-in user without exposing a Dodo API key.
- Let users open their customer portal or list their subscriptions and payments.
- Submit metered usage for the signed-in customer.
- Receive signature-verified Dodo webhooks through Better Auth.

## Install

```bash
npm install @dodopayments/better-auth dodopayments better-auth
```

The package exports the lowercase server functions `dodopayments`, `checkout`, `portal`, `usage`, and `webhooks`. Its client entry point exports `dodopaymentsClient`.

## Server setup

Every endpoint is registered by a feature in `use`. Include every feature that the application calls; omitting one makes its route return 404.

```typescript
import { betterAuth } from "better-auth";
import DodoPayments from "dodopayments";
import { checkout, dodopayments, portal, usage, webhooks } from "@dodopayments/better-auth";

const dodoPayments = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: "test_mode",
});

export const auth = betterAuth({
  database: {
    // your database config
  },
  plugins: [
    dodopayments({
      client: dodoPayments,
      createCustomerOnSignUp: true,
      // `user` here is Better Auth's base user: id, name, email, emailVerified,
      // image, createdAt, updatedAt. Anything else (phone number, company, plan)
      // must first be declared via `user.additionalFields` in your Better Auth
      // config, otherwise it does not exist on the type and will be undefined.
      getCustomerParams: (user) => ({
        metadata: { better_auth_user_id: user.id },
      }),
      use: [
        checkout({
          products: [
            { productId: "pdt_premium", slug: "premium-plan" },
          ],
          successUrl: "https://app.example.com/billing/success",
          authenticatedUsersOnly: true,
        }),
        portal(),
        usage(),
        webhooks({
          webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
          onPayload: async (payload) => {
            console.log("Verified Dodo webhook:", payload.type);
          },
        }),
      ],
    }),
  ],
});
```

`products` maps an application slug to a Dodo product ID. `authenticatedUsersOnly: true` requires a Better Auth session for checkout. `getCustomerParams` adds application metadata when customer synchronization runs.

## Browser client setup

```typescript
import { createAuthClient } from "better-auth/react";
import { dodopaymentsClient } from "@dodopayments/better-auth/client";

export const authClient = createAuthClient({
  plugins: [dodopaymentsClient()],
});
```

These are browser methods. They send the Better Auth session cookie automatically; do not pass `request.headers` to them.

## Create a checkout session

```typescript
import { authClient } from "@/lib/auth-client";

async function startCheckout() {
  const { data: session, error } = await authClient.dodopayments.checkoutSession({
    slug: "premium-plan",
    referenceId: "order_123",
  });

  if (error) {
    console.error("Checkout error:", error);
    return;
  }

  if (session) {
    window.location.href = session.url;
  }
}
```

`slug` must match a product configured in `checkout({ products: [...] })`. `referenceId` is optional reconciliation metadata.

## Open the customer portal

```typescript
const { data: portalSession, error } =
  await authClient.dodopayments.customer.portal();

if (error) {
  console.error("Portal error:", error);
} else if (portalSession?.redirect) {
  window.location.href = portalSession.url;
}
```

The portal endpoint requires a signed-in, verified user and resolves that user's synchronized Dodo customer.

## List subscriptions and payments

```typescript
const { data: subscriptions, error: subscriptionsError } =
  await authClient.dodopayments.customer.subscriptions.list({
    query: { page: 1, limit: 10, status: "active" },
  });

const { data: payments, error: paymentsError } =
  await authClient.dodopayments.customer.payments.list({
    query: { page: 1, limit: 10, status: "succeeded" },
  });

if (subscriptionsError || paymentsError) {
  console.error("Could not load billing history");
} else {
  console.log("Subscriptions:", subscriptions?.items);
  console.log("Payments:", payments?.items);
}
```

Both list responses use an `items` envelope. Subscription filters accept `page`, `limit`, and `status`; payment filters use the same pagination fields and payment statuses.

## Ingest metered usage

Enable `usage()` on the server, then submit an event for the signed-in customer:

```typescript
const { data, error } = await authClient.dodopayments.usage.ingest({
  event_id: "evt_usage_123",
  event_name: "api_calls",
  metadata: { requests: 100 },
  timestamp: new Date(),
});

if (error) {
  console.error("Usage ingestion failed:", error);
} else {
  console.log("Ingested events:", data?.ingested_count);
}
```

The plugin derives `customer_id` from the authenticated session. `event_id` is the event's idempotency key; reuse it when retrying the same event.

## Webhook endpoint

`webhooks({ webhookKey, onPayload })` verifies and handles the request itself. With Better Auth's default `/api/auth` base path, configure this URL in the Dodo dashboard:

```text
https://app.example.com/api/auth/dodopayments/webhooks
```

Do not create a second route and do not call `auth.api.dodopayments.verifyWebhook()`; that method does not exist. The plugin reads the raw request, verifies the Standard Webhooks signature with `webhookKey`, and invokes `onPayload` plus any configured event-specific callback.

## Registered endpoints

- `POST /dodopayments/checkout`
- `POST /dodopayments/checkout-session`
- `GET /dodopayments/customer/portal`
- `GET /dodopayments/customer/subscriptions/list`
- `GET /dodopayments/customer/payments/list`
- `POST /dodopayments/usage/ingest`
- `GET /dodopayments/usage/meters/list`
- `POST /dodopayments/webhooks`

Better Auth prefixes these plugin paths with its configured API base path.

## Common mistakes

**Enabling only `portal()`.** Checkout, usage, and webhook routes do not exist unless `checkout()`, `usage()`, and `webhooks()` are also present in `use`.

**Mixing browser and server APIs.** Call `authClient.dodopayments...` in browser code without a `headers` option. Use Better Auth's server API separately when handling server requests.

**Creating duplicate customers.** When `createCustomerOnSignUp` is enabled, do not also call `client.customers.create()` for the same user.

**Granting access from browser state.** Treat verified webhook events or a server-side Dodo lookup as the source of truth for entitlements.

**Adding a custom webhook verifier.** The plugin owns `/dodopayments/webhooks`, signature verification, and callback dispatch.

## Resources

- [Better Auth Adapter](https://docs.dodopayments.com/developer-resources/better-auth-adaptor)
- [Dodo Payments Better Auth package](https://www.npmjs.com/package/@dodopayments/better-auth)
- [Dodo Payments SDK](https://github.com/dodopayments/dodopayments-typescript)
