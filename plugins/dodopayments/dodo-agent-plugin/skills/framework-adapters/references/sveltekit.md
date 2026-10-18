# Framework Adapters: SvelteKit


**Package:** `@dodopayments/sveltekit`  
**Route placement:** `src/routes/api/checkout/+server.ts`, `src/routes/api/customer-portal/+server.ts`, `src/routes/api/webhook/+server.ts`

### Checkout

```typescript
// src/routes/api/checkout/+server.ts
import { Checkout } from "@dodopayments/sveltekit";
import { DODO_PAYMENTS_API_KEY, DODO_PAYMENTS_RETURN_URL, DODO_PAYMENTS_ENVIRONMENT } from "$env/static/private";

const dodoEnvironment = DODO_PAYMENTS_ENVIRONMENT === "live_mode" ? "live_mode" : "test_mode";

// Checkout() returns { GET, POST }, not a handler. Export GET from a "static"
// handler - the GET of a "session"/"dynamic" handler returns 400.
const staticCheckout = Checkout({
  bearerToken: DODO_PAYMENTS_API_KEY,
  returnUrl: DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "static",
});

const sessionCheckout = Checkout({
  bearerToken: DODO_PAYMENTS_API_KEY,
  returnUrl: DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});

export const GET = staticCheckout.GET;
export const POST = sessionCheckout.POST;
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
