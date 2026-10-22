# Framework Adapters: Fastify


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
