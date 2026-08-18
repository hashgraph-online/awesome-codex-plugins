---
name: framework-adapters
description: Guide for mounting official @dodopayments/* checkout, portal, and verified-webhook route handlers in supported web frameworks; use domain skills for payment and lifecycle logic.
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

- **Checkout:** static (GET only), dynamic (POST with cart), or session (POST with pre-built session).
- **CustomerPortal:** generates a time-bound portal session link.
- **Webhooks:** verifies webhook signatures and dispatches typed events.

**Export names are not uniform across adapters.** Most export `Checkout` / `CustomerPortal` / `Webhooks`, but two differ, and the return shapes differ as well. Check this table before writing imports:

| Adapter | Checkout export | Portal export | Handler shape |
|---|---|---|---|
| `nextjs`, `hono`, `astro`, `bun`, `remix`, `tanstack` | `Checkout` | `CustomerPortal` | returns a request handler |
| `express` | `checkoutHandler` (lowercase) | `CustomerPortal` | returns `(req, res)` |
| `fastify` | `Checkout` | `CustomerPortal` | returns `{ getHandler, postHandler }` |
| `sveltekit` | `Checkout` | `CustomerPortal` | returns `{ GET, POST }` / `{ GET }` |
| `nuxt` | `checkoutHandler` (auto-imported) | `customerPortalHandler` | no import statement |
| `convex` | `DodoPayments` component | — | `createDodoWebhookHandler` |

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
NUXT_PRIVATE_RETURNURL=https://yourdomain.com/checkout/success
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
import { CustomerPortal } from "@dodopayments/nextjs";

export const GET = CustomerPortal({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: dodoEnvironment,
});
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

**Package:** `@dodopayments/express`

### Checkout

The Express adapter names its checkout export `checkoutHandler` in lowercase, unlike every other adapter. `import { Checkout } from "@dodopayments/express"` does not resolve.

```typescript
import express from "express";
import { checkoutHandler } from "@dodopayments/express";
import { dodoEnvironment } from "./lib/dodo-env";

const app = express();

app.get("/api/checkout", checkoutHandler({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "static",
}));

app.post("/api/checkout", checkoutHandler({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
}));
```

### Customer Portal

```typescript
import { CustomerPortal } from "@dodopayments/express";

app.get("/api/customer-portal", CustomerPortal({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: dodoEnvironment,
}));
```

### Webhooks

```typescript
import { Webhooks } from "@dodopayments/express";

app.use(express.raw({ type: "application/json" }));

app.post("/api/webhook", Webhooks({
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => {
    console.log("Webhook:", payload.type);
  },
}));
```

## Fastify

**Package:** `@dodopayments/fastify`

Fastify requires a string body parser to preserve the raw body for webhook verification.

### Checkout

`Checkout(config)` returns an object with `getHandler` and `postHandler`, not a single callable. Build it once and mount each method, rather than calling the result.

```typescript
import Fastify from "fastify";
import { Checkout } from "@dodopayments/fastify";
import { dodoEnvironment } from "./lib/dodo-env";

const fastify = Fastify();

const staticCheckout = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "static",
});

const sessionCheckout = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});

fastify.get("/api/checkout", staticCheckout.getHandler);
fastify.post("/api/checkout", sessionCheckout.postHandler);
```

### Webhooks

```typescript
import { Webhooks } from "@dodopayments/fastify";

fastify.addContentTypeParser(
  "application/json",
  { parseAs: "string" },
  (req, body, done) => done(null, body)
);

fastify.post("/api/webhook", Webhooks({
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => {
    console.log("Webhook:", payload.type);
  },
}));
```

## Hono

**Package:** `@dodopayments/hono`

### Checkout

```typescript
import { Hono } from "hono";
import { Checkout } from "@dodopayments/hono";

const app = new Hono();

app.get("/api/checkout", Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "static",
}));

app.post("/api/checkout", Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
}));
```

### Customer Portal

```typescript
import { CustomerPortal } from "@dodopayments/hono";

app.get("/api/customer-portal", CustomerPortal({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: dodoEnvironment,
}));
```

### Webhooks

```typescript
import { Webhooks } from "@dodopayments/hono";

app.post("/api/webhook", Webhooks({
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => {
    console.log("Webhook:", payload.type);
  },
}));
```

## Astro

**Package:** `@dodopayments/astro`  
**Route placement:** `src/pages/api/checkout.ts`, `src/pages/api/customer-portal.ts`, `src/pages/api/webhook.ts`

Disable prerendering for checkout routes.

### Checkout

```typescript
// src/pages/api/checkout.ts
import { Checkout } from "@dodopayments/astro";

export const prerender = false;

// Astro reads env from import.meta.env, which is typed as string - so it needs
// the same narrowing as process.env. Define this alongside the other helper in
// lib/dodo-env.ts if you use both.
const dodoEnvironment =
  import.meta.env.DODO_PAYMENTS_ENVIRONMENT === "live_mode" ? "live_mode" : "test_mode";

export const GET = Checkout({
  bearerToken: import.meta.env.DODO_PAYMENTS_API_KEY,
  returnUrl: import.meta.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "static",
});

export const POST = Checkout({
  bearerToken: import.meta.env.DODO_PAYMENTS_API_KEY,
  returnUrl: import.meta.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});
```

### Webhooks

```typescript
// src/pages/api/webhook.ts
import { Webhooks } from "@dodopayments/astro";

export const prerender = false;

export const POST = Webhooks({
  webhookKey: import.meta.env.DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => {
    console.log("Webhook:", payload.type);
  },
});
```

## Remix

**Package:** `@dodopayments/remix`

### Checkout

```typescript
// app/routes/api.checkout.tsx
import { Checkout } from "@dodopayments/remix";
import type { LoaderFunctionArgs, ActionFunctionArgs } from "@remix-run/node";

const checkoutHandler = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});

export const loader = ({ request }: LoaderFunctionArgs) => checkoutHandler(request);
export const action = ({ request }: ActionFunctionArgs) => checkoutHandler(request);
```

### Customer Portal

```typescript
// app/routes/api.customer-portal.tsx
import { CustomerPortal } from "@dodopayments/remix";
import type { LoaderFunctionArgs } from "@remix-run/node";

const portalHandler = CustomerPortal({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: dodoEnvironment,
});

export const loader = ({ request }: LoaderFunctionArgs) => portalHandler(request);
```

### Webhooks

```typescript
// app/routes/api.webhook.tsx
import { Webhooks } from "@dodopayments/remix";
import type { ActionFunctionArgs } from "@remix-run/node";

export const action = ({ request }: ActionFunctionArgs) =>
  Webhooks({
    webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
    onPayload: async (payload) => {
      console.log("Webhook:", payload.type);
    },
  })(request);
```

## SvelteKit

**Package:** `@dodopayments/sveltekit`  
**Route placement:** `src/routes/api/checkout/+server.ts`, `src/routes/api/customer-portal/+server.ts`, `src/routes/api/webhook/+server.ts`

### Checkout

```typescript
// src/routes/api/checkout/+server.ts
import { Checkout } from "@dodopayments/sveltekit";
import { DODO_PAYMENTS_API_KEY, DODO_PAYMENTS_RETURN_URL, DODO_PAYMENTS_ENVIRONMENT } from "$env/static/private";

const checkoutHandler = Checkout({
  bearerToken: DODO_PAYMENTS_API_KEY,
  returnUrl: DODO_PAYMENTS_RETURN_URL,
  environment: DODO_PAYMENTS_ENVIRONMENT,
  type: "session",
});

export const GET = checkoutHandler;
export const POST = checkoutHandler;
```

### Webhooks

```typescript
// src/routes/api/webhook/+server.ts
import { Webhooks } from "@dodopayments/sveltekit";
import { DODO_PAYMENTS_WEBHOOK_KEY } from "$env/static/private";

export const POST = Webhooks({
  webhookKey: DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => {
    console.log("Webhook:", payload.type);
  },
});
```

## Nuxt

**Package:** `@dodopayments/nuxt`

Add the module to `nuxt.config.ts` and configure runtime variables:

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ["@dodopayments/nuxt"],
  runtimeConfig: {
    private: {
      bearerToken: process.env.NUXT_PRIVATE_BEARER_TOKEN,
      webhookKey: process.env.NUXT_PRIVATE_WEBHOOK_KEY,
      environment: process.env.NUXT_PRIVATE_ENVIRONMENT,
      returnUrl: process.env.NUXT_PRIVATE_RETURNURL,
    },
  },
});
```

### Checkout

The Nuxt module registers its handlers with `addServerImportsDir`, so `checkoutHandler`, `customerPortalHandler`, and `Webhooks` are **auto-imported** inside `server/`. Do not import them from `@dodopayments/nuxt` — that entry point exports only the Nuxt module itself, and a named import from it will not resolve.

```typescript
// server/routes/api/checkout.ts
// checkoutHandler and useRuntimeConfig are auto-imported by the module.
const config = useRuntimeConfig();

export default checkoutHandler({
  bearerToken: config.private.bearerToken,
  returnUrl: config.private.returnUrl,
  environment: config.private.environment,
  type: "session",
});
```

### Webhooks

```typescript
// server/routes/api/webhook.ts
// Webhooks and useRuntimeConfig are auto-imported by the module.
const config = useRuntimeConfig();

export default Webhooks({
  webhookKey: config.private.webhookKey,
  onPayload: async (payload) => {
    console.log("Webhook:", payload.type);
  },
});
```

## TanStack Start

**Package:** `@dodopayments/tanstack`

### Checkout

`Checkout(config)` returns a plain `(request: Request) => Promise<Response>`, so export it directly as the route's method handler. The adapter's own documented usage is `export const GET = Checkout(config)`.

```typescript
// src/routes/api/checkout.ts
import { Checkout } from "@dodopayments/tanstack";
import { dodoEnvironment } from "./lib/dodo-env";

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

TanStack Start's server-route definition API has changed across releases (`createServerFileRoute` was removed). Wrap these exports in whatever route helper your installed version provides; the adapter handlers themselves are unaffected.

## Bun

**Package:** `@dodopayments/bun`

### Checkout and Portal

```typescript
import { Checkout, CustomerPortal } from "@dodopayments/bun";

const checkoutHandler = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});

const portalHandler = CustomerPortal({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: dodoEnvironment,
});

Bun.serve({
  port: 3000,
  fetch(request) {
    const url = new URL(request.url);

    if (url.pathname === "/api/checkout") {
      return checkoutHandler(request);
    }
    if (url.pathname === "/api/customer-portal" && request.method === "GET") {
      return portalHandler(request);
    }

    return new Response("Not Found", { status: 404 });
  },
});
```

## Convex

**Package:** `@dodopayments/convex`

Convex uses a component-based architecture. Register the component in `convex.config.ts`:

```typescript
// convex/convex.config.ts
import { defineApp } from "convex/server";
import dodopayments from "@dodopayments/convex/convex.config";

const app = defineApp();
app.use(dodopayments);
export default app;
```

Then use the component in your actions and HTTP routes:

```typescript
// convex/checkout.ts
import { mutation } from "./_generated/server";
import { components } from "./_generated/server";

export const createCheckoutSession = mutation({
  args: { customerId: v.string() },
  handler: async (ctx, args) => {
    const dodo = components.dodopayments;
    return dodo.checkout.createSession(ctx, {
      customerId: args.customerId,
      // ... checkout params
    });
  },
});
```

Convex only supports session checkout, not static or dynamic modes.

## Common mistakes

1. **Duplicate POST handlers:** Next.js and Astro docs show two `export const POST` declarations. Choose one checkout mode per route or add routing logic to dispatch between them.

2. **Wrong webhook variable name:** Check whether your adapter uses `DODO_PAYMENTS_WEBHOOK_KEY` or `DODO_PAYMENTS_WEBHOOK_SECRET`. The docs are inconsistent; use the name your adapter actually references.

3. **Forgetting raw body preservation:** Webhook handlers must receive the raw request body, not a re-parsed JSON object. Fastify requires an explicit string body parser; Express needs `express.raw()`; other frameworks handle this automatically. Webhook signature verification is covered in the `webhook-integration` skill.

4. **Mixing framework conventions:** Each framework has its own request/response shape. Don't try to use a Next.js handler in Express or vice versa. Use the adapter for your framework.

5. **Hardcoding secrets:** Always read API keys and webhook secrets from environment variables, never from code or config files.

6. **Skipping environment setup:** The adapters won't work without `DODO_PAYMENTS_API_KEY` and `DODO_PAYMENTS_ENVIRONMENT`. Set these before testing.

7. **Using `@dodopayments/core` directly:** The core package is an internal dependency, not a documented public entry point. Use the framework adapter for your stack.

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
