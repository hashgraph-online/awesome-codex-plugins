# Better Auth

## Contents

- [Install](#install)
- [Server setup](#server-setup)
- [Browser client](#browser-client)
- [Checkout, portal and billing history](#checkout-portal-and-billing-history)
- [Usage events](#usage-events)
- [Webhooks and routes](#webhooks-and-routes)
- [Common mistakes](#common-mistakes)

`@dodopayments/better-auth` creates a Dodo customer for each Better Auth user and adds authenticated checkout, customer portal, billing history, usage and webhook endpoints. Use it instead of a framework adapter when the app uses Better Auth.

## Install

```bash
npm install @dodopayments/better-auth dodopayments better-auth zod
```

Needs Better Auth 1.4 or a later 1.x.

## Server setup

Each endpoint exists only if its feature is in `use`.

```typescript
import { betterAuth } from "better-auth";
import DodoPayments from "dodopayments";
import { checkout, dodopayments, portal, usage, webhooks } from "@dodopayments/better-auth";

const dodoPayments = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: process.env.DODO_PAYMENTS_ENVIRONMENT === "live_mode" ? "live_mode" : "test_mode",
});

export const auth = betterAuth({
  database: {
    // your database config
  },
  plugins: [
    dodopayments({
      client: dodoPayments,
      createCustomerOnSignUp: true,
      getCustomerParams: (user) => ({ metadata: { better_auth_user_id: user.id } }),
      use: [
        checkout({
          products: [{ productId: "pdt_pro_monthly", slug: "pro" }],
          successUrl: "https://example.com/billing/success",
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

- `products` maps your slug to a Dodo product ID, so the browser never picks a product ID.
- The plugin adds `dodoCustomerId` to the `user` table. Update the schema with `npx auth generate` (then apply it) or `npx auth migrate`.
- `getCustomerParams` sees only Better Auth's base user fields unless you declare `user.additionalFields`.

## Browser client

```typescript
import { createAuthClient } from "better-auth/react";
import { dodopaymentsClient } from "@dodopayments/better-auth/client";

export const authClient = createAuthClient({ plugins: [dodopaymentsClient()] });
```

The client sends the session cookie itself; do not pass `headers`.

## Checkout, portal and billing history

```typescript
const { data: session, error } = await authClient.dodopayments.checkoutSession({
  slug: "pro",
  referenceId: "order_123", // optional
});
if (!error && session) window.location.href = session.url;

const { data: portalSession } = await authClient.dodopayments.customer.portal();
if (portalSession?.redirect) window.location.href = portalSession.url;

const { data: subscriptions } = await authClient.dodopayments.customer.subscriptions.list({
  query: { page: 1, limit: 10, status: "active" },
});
const { data: payments } = await authClient.dodopayments.customer.payments.list({
  query: { page: 1, limit: 10, status: "succeeded" },
});
console.log(subscriptions?.items, payments?.items);
```

The portal needs a signed-in user with a verified email.

## Usage events

```typescript
const { data, error } = await authClient.dodopayments.usage.ingest({
  event_id: "api-call:req_123", // reuse on retry
  event_name: "api.call",
  metadata: { endpoint: "/v1/users" },
  timestamp: new Date(),
});
if (error) console.error(error);
else console.log(data?.ingested_count);
```

The plugin sets `customer_id` from the session. `usage.ingest` and `usage.meters.list` need a verified email. For usage that the server records, ingest from the server instead ([usage-billing.md](usage-billing.md)).

## Webhooks and routes

`webhooks({ webhookKey, onPayload })` reads the raw body, verifies the signature and calls `onPayload`. Register this URL in the Dodo dashboard (default base path `/api/auth`):

```text
https://example.com/api/auth/dodopayments/webhooks
```

Routes under the Better Auth base path: `POST /dodopayments/checkout`, `POST /dodopayments/checkout-session`, `GET /dodopayments/customer/portal`, `GET /dodopayments/customer/subscriptions/list`, `GET /dodopayments/customer/payments/list`, `POST /dodopayments/usage/ingest`, `GET /dodopayments/usage/meters/list`, `POST /dodopayments/webhooks`.

## Common mistakes

- Leaving a feature out of `use`; its route returns 404.
- Calling `client.customers.create` as well as `createCustomerOnSignUp`; it duplicates customers.
- Adding a second webhook route or calling `auth.api.dodopayments.verifyWebhook()`, which does not exist.
- Granting access from browser state instead of the verified webhook.
