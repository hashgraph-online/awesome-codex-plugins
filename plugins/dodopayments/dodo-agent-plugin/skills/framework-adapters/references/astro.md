# Framework Adapters: Astro


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
