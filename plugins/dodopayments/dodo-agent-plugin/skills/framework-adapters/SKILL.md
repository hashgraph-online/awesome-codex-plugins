---
name: framework-adapters
description: Official @dodopayments/* framework adapters that mount Checkout, CustomerPortal, and Webhooks route handlers. Use when integrating Dodo Payments into Next.js, Express, Fastify, Hono, Astro, Remix, SvelteKit, Nuxt, TanStack, Bun, or Convex, such as @dodopayments/nextjs; use domain skills for payment and subscription logic.
---

# Framework Adapters

Use this skill when you need to integrate Dodo Payments into a web framework using the official adapter packages. Framework adapters handle route plumbing, environment configuration, and handler setup so you don't build checkout, portal, and webhook routes from scratch.

## When to use this skill

- You're building a checkout flow in Next.js, Express, Fastify, Hono, Astro, Remix, SvelteKit, Nuxt, TanStack, Bun, or Convex.
- You need to set up a customer portal session endpoint.
- You're adding webhook handlers that verify signatures and dispatch events.
- You want framework-idiomatic route placement and environment variable handling.
- You need to choose between static, dynamic, or session checkout modes.

## What framework adapters do

Dodo publishes `@dodopayments/*` packages that wrap the core SDK with framework-specific route handlers. Instead of writing your own HTTP handlers, you import the adapter's handlers and mount them directly in your routes.

Each adapter exposes three handler families:

- **Checkout:** static (GET only), dynamic (POST, creates a payment or subscription via the deprecated `POST /payments` / `POST /subscriptions` endpoints - existing integrations only), or session (POST with a checkout session payload - use this for new integrations).
- **CustomerPortal:** generates a time-bound portal session link.
- **Webhooks:** verifies webhook signatures and dispatches typed events.

> **Security - CustomerPortal does not authenticate.** Every `CustomerPortal` handler opens the portal for whatever `?customer_id=` it receives. Mounted as-is, any visitor can open any customer's portal by guessing or enumerating IDs. Put the route behind your own authentication and resolve the customer ID **server-side from the signed-in session**; never accept it from the client. The portal examples below do this.

**Export names are not uniform across adapters.** Most export `Checkout` / `CustomerPortal` / `Webhooks`, but two differ, and the return shapes differ as well. Check this table before writing imports:

| Adapter | Checkout export | Portal export | Handler shape |
|---|---|---|---|
| `nextjs`, `hono`, `astro`, `bun`, `remix`, `tanstack` | `Checkout` | `CustomerPortal` | returns a request handler |
| `express` | `checkoutHandler` (lowercase) | `CustomerPortal` | returns `(req, res)` |
| `fastify` | `Checkout` | `CustomerPortal` | returns `{ getHandler, postHandler }` |
| `sveltekit` | `Checkout` | `CustomerPortal` | returns `{ GET, POST }` / `{ GET }` |
| `nuxt` | `checkoutHandler` (auto-imported) | `customerPortalHandler` | no import statement |
| `convex` | `checkout` (from `dodo.api()`) | `customerPortal` (from `dodo.api()`, uses `identify`) | `createDodoWebhookHandler` |

The adapters handle raw body preservation for webhook verification, environment variable mapping, and framework-specific request/response shapes. Checkout payload design belongs to the `checkout-integration` skill; webhook business logic belongs to `webhook-integration`; portal behavior belongs to `customer-management`.

## Framework selection and installation

| Framework | Package | Install |
|---|---|---|
| Next.js | `@dodopayments/nextjs` | `npm install @dodopayments/nextjs` |
| Express | `@dodopayments/express` | `npm install @dodopayments/express` |
| Fastify | `@dodopayments/fastify` | `npm install @dodopayments/fastify` |
| Hono | `@dodopayments/hono` | `npm install @dodopayments/hono` |
| Astro | `@dodopayments/astro` | `npm install @dodopayments/astro` |
| Remix | `@dodopayments/remix` | `npm install @dodopayments/remix` |
| SvelteKit | `@dodopayments/sveltekit` | `npm install @dodopayments/sveltekit` |
| Nuxt | `@dodopayments/nuxt` | `npm install @dodopayments/nuxt` |
| TanStack Start | `@dodopayments/tanstack` | `npm install @dodopayments/tanstack` |
| Bun | `@dodopayments/bun` | `bun add @dodopayments/bun` |
| Convex | `@dodopayments/convex` | `npm install @dodopayments/convex` |

## Environment variables

Most adapters use these standard names:

```env
DODO_PAYMENTS_API_KEY=dodo_test_...
DODO_PAYMENTS_WEBHOOK_KEY=your-webhook-secret
DODO_PAYMENTS_ENVIRONMENT=test_mode
DODO_PAYMENTS_RETURN_URL=https://yourdomain.com/checkout/success
```

**Nuxt** uses private runtime config prefixes:

```env
NUXT_PRIVATE_BEARER_TOKEN=dodo_test_...
NUXT_PRIVATE_WEBHOOK_KEY=your-webhook-secret
NUXT_PRIVATE_ENVIRONMENT=test_mode
NUXT_PRIVATE_RETURN_URL=https://yourdomain.com/checkout/success
```

**Convex** uses dashboard environment variables (not local `.env`):

```env
DODO_PAYMENTS_API_KEY=dodo_test_...
DODO_PAYMENTS_ENVIRONMENT=test_mode
DODO_PAYMENTS_WEBHOOK_SECRET=your-webhook-secret
```

**Webhook key naming:** Some adapters reference `DODO_PAYMENTS_WEBHOOK_KEY`, others use `DODO_PAYMENTS_WEBHOOK_SECRET`. Check your framework's adapter docs and dashboard configuration to use the correct variable name.

### Narrowing `environment`

Adapter configs type `environment` as `Pick<ClientOptions, "environment">`, i.e. the literal union `"test_mode" | "live_mode"`. `process.env.X` is `string | undefined`, which does **not** assign to it — passing it directly is a type error in every adapter.

Define this helper once and import it wherever you construct an adapter config:

```typescript
// lib/dodo-env.ts
export const dodoEnvironment =
  process.env.DODO_PAYMENTS_ENVIRONMENT === "live_mode" ? "live_mode" : "test_mode";
```

Defaulting to `test_mode` is deliberate: a missing or misspelled variable must never silently resolve to live mode. Every example below uses `dodoEnvironment`.

## Next.js

**Package:** `@dodopayments/nextjs`  
**Route placement:** `app/api/checkout/route.ts`, `app/api/customer-portal/route.ts`, `app/api/webhook/route.ts`

### Checkout (choose one mode per route)

```typescript
// app/api/checkout/route.ts
import { Checkout } from "@dodopayments/nextjs";
import { dodoEnvironment } from "@/lib/dodo-env";

export const GET = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "static",
});

export const POST = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});
```

### Customer Portal

```typescript
// app/api/customer-portal/route.ts
import { NextRequest } from "next/server";
import { CustomerPortal } from "@dodopayments/nextjs";
import { dodoEnvironment } from "@/lib/dodo-env";
// your auth helper
import { getSessionUser } from "@/lib/auth";

const portal = CustomerPortal({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: dodoEnvironment,
});

export async function GET(req: NextRequest) {
  const user = await getSessionUser(req);
  if (!user?.dodoCustomerId) return new Response("Unauthorized", { status: 401 });

  // Overwrite any client-supplied ?customer_id= with the signed-in user's ID.
  const url = new URL(req.url);
  url.searchParams.set("customer_id", user.dodoCustomerId);
  return portal(new NextRequest(url, req));
}
```

### Webhooks

```typescript
// app/api/webhook/route.ts
import { Webhooks } from "@dodopayments/nextjs";

export const POST = Webhooks({
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => {
    console.log("Webhook received:", payload.type);
  },
});
```

## Express

Full guide: [references/express.md](references/express.md).

Covers:

- Checkout
- Customer Portal
- Webhooks

## Fastify

Full guide: [references/fastify.md](references/fastify.md).

Covers:

- Checkout
- Webhooks

## Hono

Full guide: [references/hono.md](references/hono.md).

Covers:

- Checkout
- Customer Portal
- Webhooks

## Astro

Full guide: [references/astro.md](references/astro.md).

Covers:

- Checkout
- Webhooks

## Remix

Full guide: [references/remix.md](references/remix.md).

Covers:

- Checkout
- Customer Portal
- Webhooks

## SvelteKit

Full guide: [references/sveltekit.md](references/sveltekit.md).

Covers:

- Checkout
- Webhooks

## Nuxt

Full guide: [references/nuxt.md](references/nuxt.md).

Covers:

- Checkout
- Webhooks

## TanStack Start

Full guide: [references/tanstack-start.md](references/tanstack-start.md).

Covers:

- Checkout

## Bun

Full guide: [references/bun.md](references/bun.md).

Covers:

- Checkout and Portal

## Convex

Full guide: [references/convex.md](references/convex.md).

## Common mistakes

1. **Duplicate POST handlers:** Next.js and Astro docs show two `export const POST` declarations. Choose one checkout mode per route or add routing logic to dispatch between them.

2. **Wrong webhook variable name:** Check whether your adapter uses `DODO_PAYMENTS_WEBHOOK_KEY` or `DODO_PAYMENTS_WEBHOOK_SECRET`. The docs are inconsistent; use the name your adapter actually references.

3. **Forgetting raw body preservation:** Webhook handlers must receive the raw request body, not a re-parsed JSON object. Fastify requires an explicit string body parser; other frameworks handle this automatically. **Express is the exception:** its `Webhooks` handler verifies against the parsed `req.body`, so register `express.json()` before the route and do not use `express.raw()`, which makes every verification fail. Webhook signature verification is covered in the `webhook-integration` skill.

4. **Mixing framework conventions:** Each framework has its own request/response shape. Don't try to use a Next.js handler in Express or vice versa. Use the adapter for your framework.

5. **Hardcoding secrets:** Always read API keys and webhook secrets from environment variables, never from code or config files.

6. **Skipping environment setup:** The adapters won't work without `DODO_PAYMENTS_API_KEY` and `DODO_PAYMENTS_ENVIRONMENT`. Set these before testing.

7. **Exposing CustomerPortal unauthenticated:** The portal handlers trust `?customer_id=` from the request. Resolve the ID from the signed-in session on the server, as in the examples above, or anyone can open any customer's portal.

8. **Using `@dodopayments/core` directly:** The core package is an internal dependency, not a documented public entry point. Use the framework adapter for your stack.

## Resources

- [Framework Adapters Overview](https://docs.dodopayments.com/developer-resources/framework-adaptors)
- [Next.js Adapter](https://docs.dodopayments.com/developer-resources/nextjs-adaptor)
- [Express Adapter](https://docs.dodopayments.com/developer-resources/express-adaptor)
- [Fastify Adapter](https://docs.dodopayments.com/developer-resources/fastify-adaptor)
- [Hono Adapter](https://docs.dodopayments.com/developer-resources/hono-adaptor)
- [Astro Adapter](https://docs.dodopayments.com/developer-resources/astro-adaptor)
- [Remix Adapter](https://docs.dodopayments.com/developer-resources/remix-adaptor)
- [SvelteKit Adapter](https://docs.dodopayments.com/developer-resources/sveltekit-adaptor)
- [Nuxt Adapter](https://docs.dodopayments.com/developer-resources/nuxt-adaptor)
- [TanStack Adapter](https://docs.dodopayments.com/developer-resources/tanstack-adaptor)
- [Bun Adapter](https://docs.dodopayments.com/developer-resources/bun-adaptor)
- [Convex Component](https://docs.dodopayments.com/developer-resources/convex-component)
