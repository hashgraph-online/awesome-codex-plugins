# Framework adapters

## Contents

- [What the adapters do](#what-the-adapters-do)
- [Packages and exports](#packages-and-exports)
- [Environment variables](#environment-variables)
- [Next.js](#nextjs)
- [Express](#express)
- [Hono](#hono)
- [Fastify](#fastify)
- [Astro](#astro)
- [Remix](#remix)
- [SvelteKit](#sveltekit)
- [Nuxt](#nuxt)
- [TanStack Start](#tanstack-start)
- [Bun](#bun)
- [Convex](#convex)
- [Common mistakes](#common-mistakes)

## What the adapters do

`@dodopayments/<framework>` packages give you ready route handlers:

- **Checkout** with `type: "session"` creates a checkout session from the POSTed checkout session payload. `type: "static"` serves GET links for a product ID.
- **CustomerPortal** redirects to a customer portal session. **It does not authenticate**: it opens the portal for whatever `customer_id` the request carries. Always put it behind your auth and set the customer ID from the signed-in session, as below.
- **Webhooks** verifies the signature and calls `onPayload` with the typed webhook. Add your own deduplication inside `onPayload` ([webhooks.md](webhooks.md)); the callback does not expose `webhook-id`, so key on a stable ID such as `payment_id`.

For Better Auth apps use [better-auth.md](better-auth.md) instead.

## Packages and exports

| Framework | Package | Checkout export | Notes |
|---|---|---|---|
| Next.js, Hono, Astro, Remix, TanStack Start, Bun | `@dodopayments/<name>` (`tanstack` for TanStack) | `Checkout` | Returns a request handler |
| Express | `@dodopayments/express` | `checkoutHandler` | Lowercase; returns `(req, res)` |
| Fastify | `@dodopayments/fastify` | `Checkout` | Returns `{ getHandler, postHandler }` |
| SvelteKit | `@dodopayments/sveltekit` | `Checkout` | Returns `{ GET, POST }` |
| Nuxt | `@dodopayments/nuxt` | `checkoutHandler` | Auto-imported in `server/`; no import statement |
| Convex | `@dodopayments/convex` | `checkout` from `dodo.api()` | Session checkout only |

## Environment variables

```env
DODO_PAYMENTS_API_KEY=dodo_test_...
DODO_PAYMENTS_WEBHOOK_KEY=...
DODO_PAYMENTS_ENVIRONMENT=test_mode
DODO_PAYMENTS_RETURN_URL=https://example.com/checkout/success
```

Nuxt uses `NUXT_PRIVATE_BEARER_TOKEN`, `NUXT_PRIVATE_WEBHOOK_KEY`, `NUXT_PRIVATE_ENVIRONMENT` and `NUXT_PRIVATE_RETURN_URL`. Convex reads variables set in the Convex dashboard.

`environment` is typed `"test_mode" | "live_mode"`, so narrow the env var once and default to test mode:

```typescript
// lib/dodo-env.ts
export const dodoEnvironment =
  process.env.DODO_PAYMENTS_ENVIRONMENT === "live_mode" ? "live_mode" : "test_mode";
```

## Next.js

```typescript
// app/api/checkout/route.ts
import { Checkout } from "@dodopayments/nextjs";
import { dodoEnvironment } from "@/lib/dodo-env";

export const POST = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});
```

```typescript
// app/api/customer-portal/route.ts
import { NextRequest } from "next/server";
import { CustomerPortal } from "@dodopayments/nextjs";
import { dodoEnvironment } from "@/lib/dodo-env";
import { getSessionUser } from "@/lib/auth";

const portal = CustomerPortal({ bearerToken: process.env.DODO_PAYMENTS_API_KEY, environment: dodoEnvironment });

export async function GET(req: NextRequest) {
  const user = await getSessionUser(req);
  if (!user?.dodoCustomerId) return new Response("Unauthorized", { status: 401 });
  const url = new URL(req.url);
  url.searchParams.set("customer_id", user.dodoCustomerId); // overwrite anything the client sent
  return portal(new NextRequest(url, req));
}
```

```typescript
// app/api/webhook/route.ts
import { Webhooks } from "@dodopayments/nextjs";

export const POST = Webhooks({
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => {
    if (payload.type === "payment.succeeded") {
      await db.$transaction(async (tx) => {
        const claim = await tx.webhookLog.createMany({
          data: [{ webhookId: payload.data.payment_id, eventType: payload.type }],
          skipDuplicates: true,
        });
        if (claim.count > 0) await handlePaymentSucceeded(payload.data, tx);
      });
    }
  },
});
```

## Express

The Express `Webhooks` handler verifies against the parsed `req.body`, so it needs `express.json()`, not `express.raw()`. The adapter's portal reads `req.query`, so call the SDK directly behind your auth instead.

```typescript
import express from "express";
import DodoPayments from "dodopayments";
import { checkoutHandler, Webhooks } from "@dodopayments/express";
import { dodoEnvironment } from "./lib/dodo-env";

const app = express();
app.use(express.json());

app.post("/api/checkout", checkoutHandler({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
}));

app.post("/api/webhook", Webhooks({
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => console.log(payload.type),
}));

const client = new DodoPayments({ bearerToken: process.env.DODO_PAYMENTS_API_KEY, environment: dodoEnvironment });
app.get("/api/customer-portal", requireAuth, async (req, res) => {
  const customerId = req.user?.dodoCustomerId; // from the session
  if (!customerId) return res.status(401).send("Unauthorized");
  const session = await client.customers.customerPortal.create(customerId);
  res.redirect(session.link);
});
```

## Hono

```typescript
import { Hono } from "hono";
import DodoPayments from "dodopayments";
import { Checkout, Webhooks } from "@dodopayments/hono";
import { dodoEnvironment } from "./lib/dodo-env";

// Your auth middleware sets "user" on the context.
const app = new Hono<{ Variables: { user?: { dodoCustomerId?: string } } }>();

app.post("/api/checkout", Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
}));

app.post("/api/webhook", Webhooks({
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => console.log(payload.type),
}));

// Portal: call the SDK with the signed-in user's customer ID.
const client = new DodoPayments({ bearerToken: process.env.DODO_PAYMENTS_API_KEY, environment: dodoEnvironment });
app.get("/api/customer-portal", async (c) => {
  const customerId = c.get("user")?.dodoCustomerId;
  if (!customerId) return c.text("Unauthorized", 401);
  const session = await client.customers.customerPortal.create(customerId);
  return c.redirect(session.link);
});
```

## Fastify

Fastify needs a string body parser so the webhook can be verified.

```typescript
import Fastify from "fastify";
import { Checkout, Webhooks } from "@dodopayments/fastify";
import { dodoEnvironment } from "./lib/dodo-env";

const fastify = Fastify();
fastify.addContentTypeParser("application/json", { parseAs: "string" }, (req, body, done) => done(null, body));

const checkout = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});
fastify.post("/api/checkout", checkout.postHandler);

fastify.post("/api/webhook", Webhooks({
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => console.log(payload.type),
}));
```

## Astro

Disable prerendering on these routes. Astro env comes from `import.meta.env`.

```typescript
// src/pages/api/checkout.ts
import { Checkout } from "@dodopayments/astro";

export const prerender = false;
const dodoEnvironment = import.meta.env.DODO_PAYMENTS_ENVIRONMENT === "live_mode" ? "live_mode" : "test_mode";

export const POST = Checkout({
  bearerToken: import.meta.env.DODO_PAYMENTS_API_KEY,
  returnUrl: import.meta.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});
```

The webhook route is `export const POST = Webhooks({ webhookKey: import.meta.env.DODO_PAYMENTS_WEBHOOK_KEY, onPayload })` from `@dodopayments/astro`, also with `prerender = false`.

## Remix

```typescript
// app/routes/api.checkout.tsx
import { Checkout } from "@dodopayments/remix";
import type { ActionFunctionArgs } from "@remix-run/node";
import { dodoEnvironment } from "~/lib/dodo-env";

const checkoutHandler = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});
export const action = ({ request }: ActionFunctionArgs) => checkoutHandler(request);
```

`CustomerPortal` and `Webhooks` from `@dodopayments/remix` take a `Request` the same way; wrap the portal like the Next.js example.

## SvelteKit

```typescript
// src/routes/api/checkout/+server.ts
import { Checkout } from "@dodopayments/sveltekit";
import { DODO_PAYMENTS_API_KEY, DODO_PAYMENTS_RETURN_URL, DODO_PAYMENTS_ENVIRONMENT } from "$env/static/private";

const sessionCheckout = Checkout({
  bearerToken: DODO_PAYMENTS_API_KEY,
  returnUrl: DODO_PAYMENTS_RETURN_URL,
  environment: DODO_PAYMENTS_ENVIRONMENT === "live_mode" ? "live_mode" : "test_mode",
  type: "session",
});
export const POST = sessionCheckout.POST;
```

```typescript
// src/routes/api/webhook/+server.ts
import { Webhooks } from "@dodopayments/sveltekit";
import { DODO_PAYMENTS_WEBHOOK_KEY } from "$env/static/private";

export const POST = Webhooks({
  webhookKey: DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => console.log(payload.type),
});
```

## Nuxt

Add `modules: ["@dodopayments/nuxt"]` and a `runtimeConfig.private` block (`bearerToken`, `webhookKey`, `environment`, `returnUrl`) to `nuxt.config.ts`. The handlers are auto-imported inside `server/`; importing them from `@dodopayments/nuxt` does not resolve.

```typescript
// server/routes/api/checkout.ts
const config = useRuntimeConfig();

export default checkoutHandler({
  bearerToken: config.private.bearerToken,
  returnUrl: config.private.returnUrl,
  environment: config.private.environment,
  type: "session",
});
```

The webhook route is `export default Webhooks({ webhookKey: config.private.webhookKey, onPayload })`.

## TanStack Start

`Checkout(config)` from `@dodopayments/tanstack` returns `(request: Request) => Promise<Response>`. Export it as the route's `POST` handler inside whatever server-route helper your TanStack Start version provides.

```typescript
import { Checkout } from "@dodopayments/tanstack";
import { dodoEnvironment } from "../../lib/dodo-env";

export const POST = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});
```

## Bun

```typescript
import { Checkout, CustomerPortal } from "@dodopayments/bun";
import { dodoEnvironment } from "./lib/dodo-env";
import { getSessionUser } from "./lib/auth";

const checkout = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});
const portal = CustomerPortal({ bearerToken: process.env.DODO_PAYMENTS_API_KEY, environment: dodoEnvironment });

Bun.serve({
  port: 3000,
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname === "/api/checkout") return checkout(request);
    if (url.pathname === "/api/customer-portal") {
      const user = await getSessionUser(request);
      if (!user?.dodoCustomerId) return new Response("Unauthorized", { status: 401 });
      url.searchParams.set("customer_id", user.dodoCustomerId);
      return portal(new Request(url, request));
    }
    return new Response("Not Found", { status: 404 });
  },
});
```

## Convex

Register the component in `convex/convex.config.ts` (`app.use(dodopayments)` with `import dodopayments from "@dodopayments/convex/convex.config"`), run `npx convex dev`, then create the client. `identify` maps the signed-in user to their Dodo customer for the portal.

```typescript
// convex/dodo.ts
import { DodoPayments } from "@dodopayments/convex";
import { components, internal } from "./_generated/api";

const apiKey = process.env.DODO_PAYMENTS_API_KEY;
if (!apiKey) throw new Error("DODO_PAYMENTS_API_KEY is not set");

export const dodo = new DodoPayments(components.dodopayments, {
  identify: async (ctx) => {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) return null;
    const customer = await ctx.runQuery(internal.customers.getByAuthId, { authId: identity.subject });
    return customer ? { dodoCustomerId: customer.dodoCustomerId } : null;
  },
  apiKey,
  environment: process.env.DODO_PAYMENTS_ENVIRONMENT === "live_mode" ? "live_mode" : "test_mode",
});

export const { checkout, customerPortal } = dodo.api();
```

Call `checkout(ctx, { payload: { product_cart, return_url } })` from a Convex **action** (mutations cannot make network calls), mapping a plan slug to a product ID on the server.

## Common mistakes

- Mounting `CustomerPortal` without auth, or taking `customer_id` from the client.
- `express.raw()` in front of the Express `Webhooks` handler; every verification fails.
- No string body parser on Fastify; verification fails.
- Passing `process.env.DODO_PAYMENTS_ENVIRONMENT` straight into `environment`; it does not type-check. Narrow it.
- `type: "dynamic"` for new code; it uses deprecated endpoints. Use `type: "session"`.
- Importing `@dodopayments/core` directly. Use the adapter for your framework.
