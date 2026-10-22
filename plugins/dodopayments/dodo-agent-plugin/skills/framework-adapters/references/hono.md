# Framework Adapters: Hono


**Package:** `@dodopayments/hono`

### Checkout

```typescript
import { Hono } from "hono";
import { Checkout } from "@dodopayments/hono";
import { dodoEnvironment } from "./lib/dodo-env";

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

The adapter's `CustomerPortal` reads `c.req.query("customer_id")`. Behind your auth middleware, call the SDK directly with the session's customer ID instead:

```typescript
import DodoPayments from "dodopayments";
import { dodoEnvironment } from "./lib/dodo-env";

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: dodoEnvironment,
});

// Assumes your auth middleware ran first and stored the user on the context.
app.get("/api/customer-portal", async (c) => {
  const customerId = c.get("user")?.dodoCustomerId; // from the session, never from the query
  if (!customerId) return c.text("Unauthorized", 401);
  const session = await client.customers.customerPortal.create(customerId);
  return c.redirect(session.link);
});
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
